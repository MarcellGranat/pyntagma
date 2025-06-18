from functools import cache, cached_property
from pathlib import Path

from pydantic import BaseModel

from .pdf_reader import silent_pdfplumber
from .position import HorizontalCoordinate, Position, VerticalCoordinate


@cache
def get_filelength(file: Path) -> int:
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
                pages.append(Page(path=file, file_page_number=i, page_number=index_in_document, document=self))
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


class Page(BaseModel):
    path: Path
    file_page_number: int  # in the file
    page_number: int  # in the document
    document: Document

    @cached_property
    def words(self) -> list["Word"]:
        with silent_pdfplumber(self.path) as pdf:
            return [
                Word(**word, page=self) for word in pdf.pages[self.file_page_number].extract_words()
            ]
        
    @cached_property
    def lines(self) -> list["Line"]:
        with silent_pdfplumber(self.path) as pdf:
            return [
                Line(**line, page=self) for line in pdf.pages[self.file_page_number].extract_text_lines()
            ]
        
    @cached_property
    def height(self) -> float:
        with silent_pdfplumber(self.path) as pdf:
            return pdf.pages[self.file_page_number].height
    
    @cached_property
    def width(self) -> float:   
        with silent_pdfplumber(self.path) as pdf:
            return pdf.pages[self.file_page_number].width
        
    def __hash__(self):
        return hash((self.path.absolute, self.file_page_number, self.page_number))
    
    def __str__(self):
        return f"Page({self.path.name}, page_number={self.page_number})"
    
    def __repr__(self):
        return f"Page({self.path.name}, page_number={self.page_number})"


def words_of_line(line: 'Line') -> list['Word']:
    """
    Extract words from a line.
    """
    if not isinstance(line, Line):
        raise ValueError("line must be an instance of Line.")
    
    words = []
    for word in line.page.words:
        if line.position.contains(word.position):
            words.append(word)
    if not words:
        raise ValueError("No words found in the line.")
    if len(words) > 1:
        words = sorted(words, key=lambda x: x.position.x0.value)
    
    return words
    

def line_of_word(word: 'Word') -> 'Line':
    """
    Find the line that contains the word.
    """
    for line in word.page.lines:
        if line.position.contains(word.position):
            return line
    raise ValueError("No line found for the word.")
    

class Word(BaseModel):
    page: "Page"
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
            bottom=VerticalCoordinate(page=self.page, value=self.bottom)
        )

    @cached_property
    def line(self) -> 'Line':
        """
        Find the line that contains the word.
        """
        return line_of_word(self)
    
    def __hash__(self) -> int:
        return hash((self.page.path, self.page.page_number, self.text, self.x0, self.x1, self.top, self.bottom))


class Line(BaseModel):
    page: "Page"
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
            bottom=VerticalCoordinate(page=self.page, value=self.bottom)
        )
    
    @cached_property
    def words(self) -> list[Word]:
        """
        Extract words from the line.
        """
        return words_of_line(self)
    
    def __hash__(self) -> int:
        return hash((self.page.path, self.page.page_number, self.text, self.x0, self.x1, self.top, self.bottom))
