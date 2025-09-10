"""Pyntagma: PDF document processing package."""

from .agent import DocumentAgent, OllamaChatModel
from .document import Char, Chars, Document, Line, Lines, Page, Word, Words
from .pdf_reader import Crop, silent_pdfplumber
from .position import (
    ExplicitAnchor,
    HorizontalCoordinate,
    HorizontalPosition,
    PdfAnchor,
    Position,
    VerticalCoordinate,
    VerticalPosition,
    get_position,
    left_position_join,
    position_union,
)

__all__ = [
    "Document",
    "Page",
    "Word",
    "Line",
    "Position",
    "VerticalCoordinate",
    "HorizontalCoordinate",
    "VerticalPosition",
    "HorizontalPosition",
    "PdfAnchor",
    "ExplicitAnchor",
    "get_position",
    "position_union",
    "left_position_join",
    "Crop",
    "silent_pdfplumber",
]
