
import json
from typing import List, Tuple, Set, Dict
from ydiff import Hunk

  
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