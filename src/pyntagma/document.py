"""High-level document model built on top of pdfplumber.

Provides `Document`, `Page` and text primitives (`Line`, `Word`, `Char`) with
geometric positions, plus helpers to navigate between them.
"""

from functools import cache, cached_property
from pathlib import Path
from typing import Iterable

from pdfplumber.display import PageImage
from pydantic import BaseModel

from src.pyntagma.pdf_reader import silent_pdfplumber
from src.pyntagma.position import (
    HorizontalCoordinate,
    PdfAnchor,
    Position,
    VerticalCoordinate,
)


@cache
def get_filelength(file: Path) -> int:
    """Return the number of pages for a PDF file."""
    with silent_pdfplumber(file) as pdf:
        return len(pdf.pages)


class Document(BaseModel):
    """
    A document consisting of multiple PDF files.
    """

    files: list[Path]

    @property
    def pages(self) -> list["Page"]:
        pages = []
        index_in_document = 0
        files = sorted(self.files)
        for file in files:
            num_pages = get_filelength(file)
            for i in range(num_pages):
                pages.append(
                    Page(
                        path=file,
                        file_page_number=i,
                        page_number=index_in_document,
                        document=self,
                    )
                )
                index_in_document += 1
        return pages

    @cached_property
    def n_pages(self) -> int:
        """
        Get the number of pages in the document.
        """
        return len(self.pages)

    def __len__(self):
        return self.n_pages

    def __str__(self):
        return f"Document(files={len(self.files)}, pages={len(self.pages)})"

    def __repr__(self):
        return f"Document(files={len(self.files)}, pages={len(self.pages)})"


@cache
def _get_words(page: "Page") -> list["Word"]:
    with silent_pdfplumber(page.path) as pdf:
        return [
            Word(**word, page=page)
            for word in pdf.pages[page.file_page_number].extract_words()
        ]


@cache
def _get_lines(page: "Page") -> list["Line"]:
    with silent_pdfplumber(page.path) as pdf:
        return [
            Line(**line, page=page)
            for line in pdf.pages[page.file_page_number].extract_text_lines()
        ]


@cache
def _get_chars(page: "Page") -> list["Char"]:
    with silent_pdfplumber(page.path) as pdf:
        return [
            Char(**char, page=page) for char in pdf.pages[page.file_page_number].chars
        ]


class Page(BaseModel):
    """A single page within a `Document`.

    Indices are available both relative to the file (`file_page_number`) and
    relative to the full document (`page_number`).
    """
    path: Path
    file_page_number: int  # in the file
    page_number: int  # in the document
    document: Document

    @property
    def words(self) -> list["Word"]:
        return _get_words(self)

    @property
    def lines(self) -> list["Line"]:
        return _get_lines(self)

    @property
    def chars(self) -> list["Char"]:
        return _get_chars(self)

    @cached_property
    def height(self) -> float:
        with silent_pdfplumber(self.path) as pdf:
            return pdf.pages[self.file_page_number].height

    @cached_property
    def width(self) -> float:
        with silent_pdfplumber(self.path) as pdf:
            return pdf.pages[self.file_page_number].width

    @property
    def im(self) -> PageImage:
        """
        Get the image of the page.
        """
        with silent_pdfplumber(self.path) as pdf:
            return pdf.pages[self.file_page_number].to_image()

    def plot_on(
        self, items: Iterable, colors: str | list[str] | None, **kwargs
    ) -> PageImage:
        """
        Plot the page on the given items.
        """
        if not colors:
            colors = "red"

        im = self.im

        for item, color in zip(items, colors):
            if isinstance(item, Position):
                position = item
            else:
                position = item.position
            im.draw_rect(position.bbox, stroke=color, **kwargs)

        return im

    def __hash__(self):
        return hash((self.path.absolute, self.file_page_number, self.page_number))

    def __str__(self):
        return f"Page({self.path.name}, page_number={self.page_number})"

    def __repr__(self):
        return f"Page({self.path.name}, page_number={self.page_number})"


def words_of_line(line: "Line") -> list["Word"]:
    """
    Extract words from a line.
    """
    words = []
    for word in line.page.words:
        if line.position.contains(word.position):
            words.append(word)
    if not words:
        raise ValueError("No words found in the line.")
    if len(words) > 1:
        words = sorted(words, key=lambda x: x.position.x0.value)

    return words


def line_of_word(word: "Word") -> "Line":
    """
    Find the line that contains the word.
    """
    for line in word.page.lines:
        if line.position.contains(word.position):
            return line
    raise ValueError("No line found for the word.")


def chars_of_word(word: "Word") -> list["Char"]:
    """Extract chars belonging to a given `Word`."""
    if not isinstance(word, Word):
        raise ValueError("word must be an instance of Word.")

    chars = []
    for char in word.page.chars:
        if word.position.contains(char.position):
            chars.append(char)
    if not chars:
        raise ValueError("No chars found in the word.")
    return chars


def word_of_char(char: "Char") -> "Word":
    """Return the `Word` that contains the given `Char`."""
    for word in char.page.words:
        if word.position.contains(char.position):
            return word
    raise ValueError("No word found for the char.")


class TextAnchor(PdfAnchor):
    """Base class for textual anchors with absolute coordinates on a page."""
    text: str
    x0: float
    x1: float
    top: float
    bottom: float

    @property
    def position(self) -> Position:
        return Position(
            x0=HorizontalCoordinate(page=self.page, value=self.x0),
            x1=HorizontalCoordinate(page=self.page, value=self.x1),
            top=VerticalCoordinate(page=self.page, value=self.top),
            bottom=VerticalCoordinate(page=self.page, value=self.bottom),
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.page.path,
                self.page.page_number,
                self.text,
                self.x0,
                self.x1,
                self.top,
                self.bottom,
            )
        )


class Word(TextAnchor):
    @cached_property
    def line(self) -> "Line":
        """
        Find the line that contains the word.
        """
        return line_of_word(self)

    @property
    def chars(self) -> list["Char"]:
        """
        Extract chars from the word.
        """
        return chars_of_word(self)


class Char(TextAnchor):
    @property
    def word(self) -> "Word":
        """
        Find the word that contains the char.
        """
        return word_of_char(self)

    @property
    def line(self) -> "Line":
        """
        Find the line that contains the char.
        """
        return self.word.line


class Line(TextAnchor):
    @cached_property
    def words(self) -> list[Word]:
        """
        Extract words from the line.
        """
        return words_of_line(self)

    @cached_property
    def chars(self) -> list["Char"]:
        """
        Extract chars from the line.
        """
        _chars = []
        for word in self.words:
            _chars.extend(word.chars)
        return _chars
