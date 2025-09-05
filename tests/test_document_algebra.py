from pathlib import Path

from src.pyntagma import Document
from src.pyntagma.position import Position, position_union

# Create a document with the actual 2-part PDF files
test_files = [
        Path("tests/test_pdfs/test-1.pdf"),
        Path("tests/test_pdfs/test-2.pdf")
    ]
    
doc = Document(files=test_files)
page = doc.pages[3]


def test_page_property():
    assert page.words[0].page == page
    assert page.words[0].page.page_number == page.page_number
    assert page.lines[3].page == page

def test_equality():
    assert page.lines[0].position == page.lines[0].position
    assert page.lines[0].position != page.lines[1].position

def test_before():
    assert page.lines[0].position.vertical < page.lines[1].position.vertical
    assert not (page.lines[0].position.vertical < page.lines[0].position.vertical)
    assert not (page.lines[0].position.vertical > page.lines[1].position.vertical)

    # expect diff_before to be negative, but its only one line
    diff_before = page.lines[0].position.vertical - page.lines[1].position.vertical
    assert diff_before < -1
    assert diff_before > -20

    assert diff_before == page.lines[0].position.vertical.bottom - page.lines[1].position.vertical.top

def test_after():
    assert page.lines[1].position.vertical > page.lines[0].position.vertical
    assert not (page.lines[1].position.vertical < page.lines[0].position.vertical)

    diff_after = page.lines[1].position.vertical - page.lines[0].position.vertical

    assert diff_after > 1
    assert diff_after < 20

def test_next_page():
    #  previous page lines are always before the next page lines
    line1 = doc.pages[0].lines[-1]
    line2 = doc.pages[1].lines[0]
    assert line1.position.vertical.bottom.value > line2.position.vertical.top.value
    assert line1.position.vertical < line2.position.vertical
    assert not (line1.position.vertical > line2.position.vertical)
    assert line2.position.vertical > line1.position.vertical
    assert not (line2.position.vertical < line1.position.vertical)

def test_distance():
    line1 = doc.pages[0].lines[-1]
    line2 = doc.pages[2].lines[0]
    page_height = doc.pages[0].height

    coord_diff = line2.position.vertical.top - line1.position.vertical.bottom
    pos_diff = line2.position.vertical - line1.position.vertical

    assert coord_diff == pos_diff

    assert pos_diff > 0
    assert pos_diff > page_height
    assert pos_diff == line2.position.vertical.top.value + page_height  + (line1.page.height - line1.position.vertical.bottom.value)

    rev_pos_diff = line1.position.vertical - line2.position.vertical
    assert rev_pos_diff < 0

    assert .9 < abs(rev_pos_diff) / pos_diff < 1.1 # should be a close value
    assert rev_pos_diff != pos_diff # but different


def test_position_union():
    union: Position = position_union([page.lines[0], page.lines[1]])

    assert union.vertical.top == page.lines[0].position.vertical.top
    assert union.vertical.bottom == page.lines[1].position.vertical.bottom
    if page.lines[0].position.horizontal.x0 < page.lines[1].position.horizontal.x0:
        assert union.horizontal.x0 == page.lines[0].position.horizontal.x0

    if page.lines[0].position.horizontal.x0 > page.lines[1].position.horizontal.x0:
        assert union.horizontal.x0 == page.lines[1].position.horizontal.x0

def test_coord_shift():
    ver_pos = doc.pages[1].lines[0].position.top
    shifted = ver_pos.shift(10)
    assert shifted.page == ver_pos.page
    assert shifted.value == ver_pos.value + 10
    assert shifted.shift(-10) == ver_pos

    page_shifted = ver_pos.shift(700)
    assert page_shifted.page.page_number == ver_pos.page.page_number + 1
    assert page_shifted - 700 == ver_pos
    assert page_shifted == ver_pos + 700

    hor_pos = doc.pages[1].lines[0].position.horizontal.x0
    shifted_hor = hor_pos.shift(10)
    assert shifted_hor.page == hor_pos.page
    assert shifted_hor.value == hor_pos.value + 10
    assert shifted_hor.shift(-10) == hor_pos

    # large value
    assert shifted_hor.shift(2000).value == hor_pos.page.width
    assert hor_pos.shift(20) - 20 == hor_pos
    assert hor_pos.shift(-2000).value == 0

    # method chaining
    shifted = hor_pos \
        .shift(10) \
        .shift(20)
    
    assert shifted.value == hor_pos.value + 30

def test_chars():
    word = page.words[3]
    chars = word.chars
    assert len(chars) == len(word.text)
    assert "".join(_.text for _ in chars) == word.text
    assert word.chars[0].word == word
    assert word.chars[0].line == word.line
