from typing import Dict, List
from src.gumtree.main.client.line_diff import LineDiff, LinePosMark


def test_process_line_marks():
    pos1 = LinePosMark(5, 20, 'x')
    pos2 = LinePosMark(5, 8, 'y')
    pos3 = LinePosMark(5, 6, 'z')
    pos4 = LinePosMark(9, 12, 'z')
    pos5 = LinePosMark(13, 17, 'z')
    pos6 = LinePosMark(14, 17, 'y')
    line_to_line_pos_mark: Dict[int, List[LinePosMark]] = {1: 
        [pos1, pos2, pos4, pos3, pos5, pos6]}
    line_to_mark_list = LineDiff.process_line_marks_to_mark_list(line_to_line_pos_mark)[1]
    assert len(line_to_mark_list) == 22
    assert line_to_mark_list[0] == (5, 'x')
    assert line_to_mark_list[1] == (5, LineDiff.RESET_TAG)
    assert line_to_mark_list[2] == (5, 'y')
    assert line_to_mark_list[3] == (5, LineDiff.RESET_TAG)
    assert line_to_mark_list[4] == (5, 'z')
    assert line_to_mark_list[5] == (6, LineDiff.RESET_TAG)
    assert line_to_mark_list[12] == (12, 'x')
    assert line_to_mark_list[13] == (13, LineDiff.RESET_TAG)
    assert line_to_mark_list[17] == (17, LineDiff.RESET_TAG)
    assert line_to_mark_list[18] == (17, 'z')
    assert line_to_mark_list[19] == (17, LineDiff.RESET_TAG)
    assert line_to_mark_list[20] == (17, 'x')
    print('here')
    
    
if __name__ == "__main__":
    test_process_line_marks()