"""High-level document model built on top of pdfplumber.

Provides `Document`, `Page` and text primitives (`Line`, `Word`, `Char`) with
geometric positions, plus helpers to navigate between them.
"""

from functools import cached_property, lru_cache
from pathlib import Path
from typing import (
    Any,
    Callable,
    Generic,
    Iterable,
    Iterator,
    Self,
    TypeVar,
    Union,
    overload,
)

from pdfplumber.display import PageImage
from pydantic import BaseModel

from .pdf_reader import silent_pdfplumber
from .position import (
    ExplicitAnchor,
    HorizontalCoordinate,
    PdfAnchor,
    Position,
    VerticalCoordinate,
    position_union,
)


@lru_cache(maxsize=128)
def _get_file_length(file: Path) -> int:
    """Return the number of pages for a PDF file."""
    with silent_pdfplumber(file) as pdf:
        return len(pdf.pages)


@lru_cache(maxsize=128)
def _get_page_height(file: Path, page_number: int) -> float:
    """Return the number of pages for a PDF file."""
    with silent_pdfplumber(file) as pdf:
        return pdf.pages[page_number].height


@lru_cache(maxsize=128)
def _get_page_width(file: Path, page_number: int) -> float:
    """Return the number of pages for a PDF file."""
    with silent_pdfplumber(file) as pdf:
        return pdf.pages[page_number].width


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
            num_pages = _get_file_length(file)
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
        return sum(_get_file_length(file) for file in self.files)

    def __len__(self):
        return self.n_pages

    def __str__(self):
        return f"Document(files={len(self.files)}, pages={len(self.pages)})"

    def __repr__(self):
        return f"Document(files={len(self.files)}, pages={len(self.pages)})"


@lru_cache(maxsize=128)
def _get_words(page: "Page") -> list["Word"]:
    with silent_pdfplumber(page.path) as pdf:
        return [
            Word(**word, page=page)
            for word in pdf.pages[page.file_page_number].extract_words()
        ]


@lru_cache(maxsize=128)
def _get_lines(page: "Page") -> list["Line"]:
    with silent_pdfplumber(page.path) as pdf:
        return [
            Line(**line, page=page)
            for line in pdf.pages[page.file_page_number].extract_text_lines()
        ]


@lru_cache(maxsize=128)
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
    def words(self) -> "Words":
        return Words(_get_words(self))

    @property
    def lines(self) -> "Lines":
        return Lines(_get_lines(self))

    @property
    def chars(self) -> "Chars":
        return Chars(_get_chars(self))

    @property
    def height(self) -> float:
        return _get_page_height(self.path, self.file_page_number)

    @property
    def width(self) -> float:
        return _get_page_width(self.path, self.file_page_number)

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


@lru_cache(maxsize=128)
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


@lru_cache(maxsize=128)
def line_of_word(word: "Word") -> "Line":
    """
    Find the line that contains the word.
    """
    for line in word.page.lines:
        if line.position.contains(word.position):
            return line
    raise ValueError("No line found for the word.")


@lru_cache(maxsize=128)
def chars_of_word(word: "Word") -> list["Char"]:
    """Extract chars belonging to a given `Word`."""

    chars = []
    for char in word.page.chars:
        if word.position.contains(char.position):
            chars.append(char)
    if not chars:
        raise ValueError("No chars found in the word.")
    return chars


@lru_cache(maxsize=128)
def word_of_char(char: "Char") -> "Word":
    """Return the `Word` that contains the given `Char`."""
    for word in char.page.words:
        if word.position.contains(char.position):
            return word
    raise ValueError("No word found for the char.")


class TextAnchor(ExplicitAnchor, frozen=True):
    """Base class for textual anchors with absolute coordinates on a page."""

    text: str

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

    def __str__(self) -> str:
        return f"{self.__class__.__name__}(text='{self.text}')"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(text='{self.text}')"


T = TypeVar("T")


class TextAnchorList(Generic[T]):
    def __init__(self, items: Iterable[T] = []):
        self.items: list[T] = list(items)

    def __iter__(self) -> Iterator[T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def __hash__(self) -> int:
        return hash(tuple(self.items))

    @overload
    def __getitem__(self, index: int) -> T: ...
    @overload
    def __getitem__(self, index: slice) -> Self: ...
    @overload
    def __getitem__(self, index: str) -> T: ...
    @overload
    def __getitem__(self, index: Iterable[int]) -> Self: ...
    @overload
    def __getitem__(self, index: Iterable[bool]) -> Self: ...
    @overload
    def __getitem__(self, index: Iterable[str]) -> Self: ...
    @overload
    def __getitem__(self, index: Callable[[T], bool]) -> Self: ...

    def __getitem__(
        self,
        index: Union[
            int,
            slice,
            str,
            Iterable[int],
            Iterable[bool],
            Iterable[str],
            Callable[[T], bool],
        ],
    ):
        # int
        if isinstance(index, int):
            return self.items[index]

        # slice
        if isinstance(index, slice):
            return self.__class__(self.items[index])

        # single string -> match by .text
        if isinstance(index, str):
            for it in self.items:
                if getattr(it, "text", None) == index:
                    return it
            raise KeyError(f"No item found with text '{index}'")

        # callable predicate -> filter
        if callable(index):
            pred: Callable[[T], bool] = index
            return self.__class__([it for it in self.items if pred(it)])

        # iterables
        if isinstance(index, Iterable):
            seq = list(index)

            # list of bools -> mask
            if all(isinstance(x, bool) for x in seq):
                if len(seq) != len(self.items):
                    raise IndexError("Boolean mask length must match list length")
                return self.__class__([it for it, keep in zip(self.items, seq) if keep])

            # list of ints -> positional take
            if all(isinstance(x, int) for x in seq):
                return self.__class__([self.items[i] for i in seq])

            # list of str -> match many by .text (keeps order of strings)
            if all(isinstance(x, str) for x in seq):
                want = set(seq)
                return self.__class__(
                    [it for it in self.items if getattr(it, "text", None) in want]
                )

        raise TypeError(
            "Unsupported index type. Use int, slice, str, iterable of int/bool/str, or a predicate function."
        )

    def sort(self, key: Callable[[T], Any], reverse: bool = False) -> Self:
        return self.__class__(sorted(self.items, key=key, reverse=reverse))

    def filter(self, predicate: Callable[[T], bool]) -> Self:
        return self.__class__(item for item in self.items if predicate(item))

    def extend(self, other: Iterable[T]) -> None:
        self.items.extend(other)

    def append(self, item: T) -> None:
        self.items.append(item)

    def pop(self, index: int = -1) -> T:
        return self.items.pop(index)

    @property
    def position(self) -> Position:
        return position_union(item.position for item in self.items)  # type: ignore "TextAnchor type only fixed in subclasses"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, TextAnchorList):
            raise NotImplementedError(
                f"Cannot compare {self.__class__.__name__} with {other.__class__.__name__}"
            )
        return self.items == other.items

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({len(self.items)} items)"


class Words(TextAnchorList["Word"]):
    def __init__(self, items: Iterable["Word"]):
        self.items = list(items)

    @property
    def lines(self) -> "Lines":
        _lines = set()
        for word in self.items:
            _lines.add(word.line)
        return Lines(_lines)

    @property
    def chars(self) -> "Chars":
        _chars = []
        for word in self.items:
            _chars.extend(word.chars)
        return Chars(_chars)


class Lines(TextAnchorList["Line"]):
    def __init__(self, items: Iterable["Line"]):
        self.items = list(items)

    @property
    def words(self) -> Words:
        _words = []
        for line in self.items:
            _words.extend(line.words)
        return Words(_words)

    @property
    def chars(self) -> "Chars":
        _chars = []
        for line in self.items:
            _chars.extend(line.chars)
        return Chars(_chars)


class Chars(TextAnchorList["Char"]):
    def __init__(self, items: Iterable["Char"]):
        self.items = list(items)

    @property
    def words(self) -> "Words":
        _words = set()
        for char in self.items:
            _words.add(char.word)
        return Words(_words)

    @property
    def lines(self) -> "Lines":
        _lines = set()
        for char in self.items:
            _lines.add(char.line)
        return Lines(_lines)


class Word(TextAnchor, frozen=True):
    @property
    def line(self) -> "Line":
        """
        Find the line that contains the word.
        """
        return line_of_word(self)

    @property
    def chars(self) -> Chars:
        """
        Extract chars from the word.
        """
        return Chars(chars_of_word(self))


class Char(TextAnchor, frozen=True):
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


class Line(TextAnchor, frozen=True):
    @property
    def words(self) -> Words:
        """
        Extract words from the line.
        """
        return Words(words_of_line(self))

    @property
    def chars(self) -> Chars:
        """
        Extract chars from the line.
        """
        _chars = set()
        for word in self.words:
            for char in word.chars:
                _chars.add(char)
        return Chars(_chars)
