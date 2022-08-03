# -*- coding: utf-8 -*-

from collections import OrderedDict
from dataclasses import dataclass, field
from typing import List, Dict
import json

from .blocksyntaxparser import BlockSyntaxParser, ParseError


@dataclass
class Block:
    """
    A class for code blocks.

    id: unique identifier. For decision block, id is parameter:option.
    parameter: parameter name, if the block is a decision.
    option: option name, if the block is a decision.
    chunks: code broken up at the boundaries of placeholder variables.
    """

    id: str = ''
    parameter: str = ''
    option: str = ''
    chunks: List = field(default_factory=lambda: [])
    code_str: str = ''
    block_prefix: str = ''

@dataclass
class BlockCode:
    dec_name: str = ''
    opt_name: str = ''
    code_str: str = ''
    extra_line: bool = False
    block_prefix: str = ''

    def __post_init__(self):
        if self.opt_name == '':
            self.opt_name = self.dec_name
            
    @property
    def code_num_lines(self) -> int:
        return len(self.code_str.split('\n')) - (0 if self.extra_line else 1)
    
    def __repr__(self):
        return f'{self.dec_name}:{self.opt_name}' if self.dec_name != self.opt_name else self.dec_name 
    
    @classmethod
    def init_from_template_block(cls, blk: Block, extra_line=True):
        return cls(blk.id, blk.option, blk.code_str, extra_line, blk.block_prefix)
        
@dataclass
class Chunk:
    """A class for code chunks.
    A code chunk contains at most one placeholder variable.

    variable: the corresponding placeholder variable, if any.
    code: the code template proceeding the variable or the block boundary.
    """
    variable: str = ''
    code: str = ''
    start_lineno: int = -1
    end_lineno: int = -1


class CodeParser:
    def __init__(self):
        self.blocks: List[Block] = OrderedDict()
        self.all_blocks: List[BlockCode] = [] # for direct ordered block to line mapping
        self.order = []

        self.raw_spec = ''
        self.spec = {}

        self.inline_constraints = []
        self.inline_vars = []
        self.used_vars = set()
        
        
    @property
    def boba_var_to_decision_ind(self) -> Dict[str, int]:
        if 'decisions' in self.spec:
            return {d_dict['var']: i for i, d_dict in enumerate(self.spec['decisions'])}
    
    @staticmethod
    def _get_block_name(block):
        """Get the ID of the block, ignoring options."""
        return block.id if block.parameter == '' else block.parameter

    def _add_block(self, block: Block):
        """Add a block to our data structure."""
        # handle config block
        if block.id == 'BOBA_CONFIG':
            self.raw_spec += block.chunks[0].code
            self.all_blocks.append(BlockCode.init_from_template_block(block))
            return
        if block.id == 'END':
            block.id = ''
            if len(self.order):
                self.blocks[self.order[-1]].chunks += block.chunks
                self.blocks[self.order[-1]].code_str += block.code_str
                new_block = BlockCode(dec_name=self.blocks[self.order[-1]].id,
                                      opt_name=self.blocks[self.order[-1]].option,
                                      code_str=block.code_str,
                                      extra_line=True,
                                      block_prefix=block.block_prefix
                                      )
                self.all_blocks.append(new_block) 
                return

        # ignore empty block
        if block.id == '' and block.chunks[0].code == '':
            return

        # handle unnamed block
        if block.id == '':
            block.id = '_start' if len(self.blocks) == 0 else '_end'

        # check if id exists
        if block.id in self.blocks:
            err = 'Duplicated code block ID "{}"'.format(block.id)
            raise ParseError(err)

        # add to data structure
        self.blocks[block.id] = block
        self.all_blocks.append(BlockCode.init_from_template_block(block,
                                                                  extra_line=block.id!='_start'))
        bn = CodeParser._get_block_name(block)
        if bn not in self.order:
            self.order.append(bn)

    def get_block_names(self):
        """
        Get the ID of all blocks, ignoring options
        :return: a set of unique names
        """
        blocks = set()
        for b in self.blocks:
            bl = self.blocks[b]
            blocks.add(CodeParser._get_block_name(bl))
        return blocks

    def get_decisions(self):
        """
        Get a dict of all block-level decisions, where the key is the parameter
        and the value is a list of block ids (namely, parameter:option).
        :return:
        """
        decs = {}
        for b in self.blocks:
            bl = self.blocks[b]
            if bl.parameter:
                p = bl.parameter
                if p in decs:
                    decs[p].append(bl.id)
                else:
                    decs[p] = [bl.id]
        return decs

    def parse(self, dec_parser, f):
        """ Make a pass over the template, parsing block declarations and
        placeholder variables inside the code."""
        code = ''
        bl = Block()
        block_code_lines = []
        self.blocks: List[Block] = OrderedDict()
        self.all_blocks: List[BlockCode] = [] # for direct ordered block to line mapping
        self.order = []
        for i, line in enumerate(f):
            if BlockSyntaxParser.can_parse(line):
                # end of the previous block
                bl.chunks.append(Chunk('', code))
                bl.code_str = ''.join(block_code_lines)
                code = ''
                block_code_lines = []
                self._add_block(bl)

                # parse the metadata and create a new block
                bp_id, par, opt, cond = BlockSyntaxParser(line).parse()
                bl = Block(bp_id, par, opt, [], block_prefix=line)

                # store inline constraints, if any
                if cond:
                    self.inline_constraints.append(cond)
            else:
                # match decision variables
                try:
                    vs, codes = dec_parser.parse_code(line)
                    if len(vs):
                        # store inline variables
                        self.used_vars.update(vs)

                        # chop into more chunks
                        # combine first chunk with previous code
                        bl.chunks.append(Chunk(vs[0], code + codes[0]))
                        for i in range(1, len(vs)):
                            bl.chunks.append(Chunk(vs[i], codes[i]))

                        # remaining code after the last matched variable
                        code = codes[-1]
                    else:
                        code += line
                    block_code_lines.append(line)
                except ParseError as e:
                    msg = 'At line "{}"\n\t{}'.format(line, e.args[0])
                    raise ParseError(msg)
                

        # add the last block
        bl.chunks.append(Chunk('', code))
        bl.code_str = ''.join(block_code_lines)
        self._add_block(bl)

        # parse the spec
        try:
            self.spec = json.loads(self.raw_spec) if self.raw_spec else {}
            # ensure all items in decision options are str
            for d_dict in self.spec['decisions']:
                new_opts = []
                for opt in d_dict['options']:
                    if type(opt) is not str:
                        opt = str(opt)
                    new_opts.append(opt)
                d_dict['options'] = new_opts
            
        except ValueError as e:
            msg = self.raw_spec + '\n' + e.args[0]
            msg += '\nBoba config is not valid JSON'
            raise ParseError(msg)
