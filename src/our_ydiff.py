
import json
from typing import List, Tuple, Set, Dict
from ydiff import Hunk, DiffMarker, COLORS, colorize, strtrim, strsplit, terminal_size
import re
  
class OurHunk(Hunk):
    def __init__(self, 
                 hunk_headers: List[str], 
                 hunk_meta: str, 
                 old_addr: Tuple[int, int], 
                 new_addr: Tuple[int, int], 
                 old_text: str, 
                 new_text: str,):
        super().__init__(hunk_headers, hunk_meta, old_addr, new_addr)
        self.old_text = old_text
        self.new_text = new_text
        
    @classmethod
    def init_from_block_names(cls, 
                              block_decision_names: Set[str],
                              old_addr: Tuple[int, int],
                              new_addr: Tuple[int, int],
                              old_text: str,
                              new_text: str
                              ):
        headers = ['\nRelevant Block(s): ']
        headers.append(', '.join( block_decision_names) + '\n')     
        meta = f'@@ template_spec_lines: {old_addr[0]},{old_addr[1]}\tuniverse_spec_lines: {new_addr[0]},{new_addr[1]}\n'
        return cls(headers, meta, old_addr, new_addr, old_text, new_text)
    
    @classmethod
    def init_from_boba_json(cls,
                            old_json: Dict,
                            new_json: Dict,
                            meta: str = ''
                            ):
        headers = ['Boba Variable Json Difference\n']
        old_text = json.dumps(old_json, indent=2)
        new_text = json.dumps(new_json, indent=2)
        
        old_addr = (1, len(old_text.split('\n')))
        new_addr = (1, len(new_text.split('\n')))
        return cls(headers, meta, old_addr, new_addr, old_text, new_text)
        
    
    def _get_old_text(self):
        return self.old_text.split('\n')
    
    def _get_new_text(self):
        return self.new_text.split('\n')

    def is_completed(self):
        return True  
    
class OurUnifiedDiff: #based on ydiff.UnifiedDiff
    def __init__(self, 
                 headers: List[str], 
                 old_path: str, 
                 new_path: str, 
                 hunks: List[OurHunk]):
        self._headers = headers
        self._old_path = old_path
        self._new_path = new_path
        self._hunks = hunks
        
        
class UnmatchedLineDiffMarker(DiffMarker):
    def _markup_side_by_side(self, diff):
        """Returns a generator"""

        def _normalize(line):
            index = 0
            while True:
                index = line.find('\t', index)
                if (index == -1):
                    break
                # ignore special codes
                offset = (line.count('\x00', 0, index) * 2 +
                          line.count('\x01', 0, index))
                # next stop modulo tab width
                width = self._tab_width - (index - offset) % self._tab_width
                line = line[:index] + ' ' * width + line[(index + 1):]
            return (line
                    .replace('\n', '')
                    .replace('\r', ''))

        def _fit_with_marker_mix(text, base_color):
            """Wrap input text which contains mdiff tags, markup at the
            meantime
            """
            out = [COLORS[base_color]]
            tag_re = re.compile(r'\x00[+^-]|\x01')

            while text:
                if text.startswith('\x00-'):    # del
                    out.append(COLORS['reverse'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x00+'):  # add
                    out.append(COLORS['reverse'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x00^'):  # change
                    out.append(COLORS['underline'] + COLORS[base_color])
                    text = text[2:]
                elif text.startswith('\x01'):   # reset
                    if len(text) > 1:
                        out.append(COLORS['reset'] + COLORS[base_color])
                    text = text[1:]
                else:
                    # FIXME: utf-8 wchar might break the rule here, e.g.
                    # u'\u554a' takes double width of a single letter, also
                    # this depends on your terminal font.  I guess audience of
                    # this tool never put that kind of symbol in their code :-)
                    #
                    out.append(text[0])
                    text = text[1:]

            out.append(COLORS['reset'])

            return ''.join(out)

        # Set up number width, note last hunk might be empty
        try:
            (start, offset) = diff._hunks[-1]._old_addr
            max1 = start + offset - 1
            (start, offset) = diff._hunks[-1]._new_addr
            max2 = start + offset - 1
        except IndexError:
            max1 = max2 = 0
        num_width = max(len(str(max1)), len(str(max2)))

        # Set up line width
        width = self._width
        if width <= 0:
            # Autodetection of text width according to terminal size
            try:
                # Each line is like 'nnn TEXT nnn TEXT\n', so width is half of
                # [terminal size minus the line number columns and 3 separating
                # spaces
                #
                width = (terminal_size()[0] - num_width * 2 - 3) // 2
            except Exception:
                # If terminal detection failed, set back to default
                width = 80

        # Setup lineno and line format
        left_num_fmt = colorize('%%(left_num)%ds' % num_width, 'yellow')
        right_num_fmt = colorize('%%(right_num)%ds' % num_width, 'yellow')
        line_fmt = (left_num_fmt + ' %(left)s ' + COLORS['reset'] +
                    right_num_fmt + ' %(right)s\n')

        # yield header, old path and new path
        for line in diff._headers:
            yield self._markup_header(line)
        yield self._markup_old_path(diff._old_path)
        yield self._markup_new_path(diff._new_path)

        # yield hunks
        for hunk in diff._hunks:
            for hunk_header in hunk._hunk_headers:
                yield self._markup_hunk_header(hunk_header)
            yield self._markup_hunk_meta(hunk._hunk_meta)
            for old, new, changed_left, changed_right in hunk.mdiff():
                if old[0]:
                    left_num = str(hunk._old_addr[0] + int(old[0]) - 1)
                else:
                    left_num = ' '

                if new[0]:
                    right_num = str(hunk._new_addr[0] + int(new[0]) - 1)
                else:
                    right_num = ' '

                left = _normalize(old[1])
                right = _normalize(new[1])

                if changed_left or changed_right:
                    if not old[0]:
                        left = ''
                        # right = right.rstrip('\x01')
                        # if right.startswith('\x00+'):
                        #     right = right[2:]
                        right = _fit_with_marker_mix(right, 'green') #self._markup_new(right)
                    elif not new[0]:
                        right = ''
                        # left = left.rstrip('\x01')
                        # if left.startswith('\x00-'):
                        #     left = left[2:]
                        left = _fit_with_marker_mix(left, 'red') #self._markup_old(left)
                        
                    else:
                        if changed_left:
                            left = _fit_with_marker_mix(left, 'red')
                        if changed_right:
                            right = _fit_with_marker_mix(right, 'green')
                else:
                    left = self._markup_common(left)
                    right = self._markup_common(right)

                if self._wrap:
                    # Need to wrap long lines, so he`re we'll iterate,
                    # shaving off `width` chars from both left and right
                    # strings, until both are empty. Also, line number needs to
                    # be printed only for the first part.
                    lncur = left_num
                    rncur = right_num
                    while left or right:
                        # Split both left and right lines, preserving escaping
                        # sequences correctly.
                        lcur, left, llen = strsplit(left, width)
                        rcur, right, rlen = strsplit(right, width)

                        # Pad left line with spaces if needed
                        if llen < width:
                            lcur = '%s%*s' % (lcur, width - llen, '')

                        yield line_fmt % {
                            'left_num': lncur,
                            'left': lcur,
                            'right_num': rncur,
                            'right': rcur
                        }

                        # Clean line numbers for further iterations
                        lncur = ''
                        rncur = ''
                else:
                    # Don't need to wrap long lines; instead, a trailing '>'
                    # char needs to be appended.
                    wrap_char = colorize('>', 'lightmagenta')
                    left = strtrim(left, width, wrap_char, len(right) > 0)
                    right = strtrim(right, width, wrap_char, False)

                    yield line_fmt % {
                        'left_num': left_num,
                        'left': left,
                        'right_num': right_num,
                        'right': right
                    }