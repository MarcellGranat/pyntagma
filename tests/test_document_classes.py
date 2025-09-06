import re
from pathlib import Path

from src.pyntagma import Document, Word

# Create a document with the actual 2-part PDF files
test_files = [Path("tests/test_pdfs/test-1.pdf"), Path("tests/test_pdfs/test-2.pdf")]

doc = Document(files=test_files)
page = doc.pages[2]


def test_self_return():
    assert doc == doc.pages[2].document
    assert doc.pages[2].document == doc.pages[2].document


def test_class_setting():
    assert isinstance(page.words[0], Word)


def test_words_of_line():
    if page.words and page.lines and page.lines[0].words:
        assert page.words[0] == page.lines[0].words[0]

    for test_word in page.words:
        line = test_word.line
        words = line.words
        if words:
            assert test_word in words
            assert re.sub(r"\s+", " ", line.text) == re.sub(
                r"\s+", " ", " ".join(word.text for word in words)
            )
        else:
            raise ValueError("Line has no words")


def test_page():
    assert page.words[0].page == page
