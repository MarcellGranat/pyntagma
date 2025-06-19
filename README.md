# Pyntagma

[![Coverage Status](https://img.shields.io/badge/coverage-80%25-green.svg)](htmlcov/index.html)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

<div align="center">
    <img src="docs/banner.png" alt="Pyntagma Banner">
</div>

Pyntagma is a Python library for creating and managing complex data structures with ease. Its name is derived from the Greek word 'Syntagma', meaning 'composition', symbolizing that this package fits for semi-structured documents.

## Features

- **PDF Document Processing**: Extract and analyze text, words, and lines from PDF documents
- **Multi-file Document Support**: Handle documents that span multiple PDF files
- **Precise Positioning**: Track exact coordinates and positions of text elements
- **Type-safe Design**: Built with Pydantic models for robust data validation
- **Silent PDF Processing**: Suppresses verbose logging during PDF operations
- **Flexible Cropping**: Extract specific regions from PDF pages

## Installation

Install Pyntagma using uv (recommended):

```bash
uv add git+https://github.com/MarcellGranat/pyntagma.git
```

## Quick Start

### Basic Document Processing

```python
from pyntagma import Document
from pathlib import Path

# Create a document from one or more PDF files
doc = Document(files=[
    Path("document-part1.pdf"),
    Path("document-part2.pdf")
])

# Access pages
print(f"Total pages: {len(doc.pages)}")

# Get the first page
page = doc.pages[0]
print(f"Page dimensions: {page.width} x {page.height}")

# Extract words and lines
words = page.words
lines = page.lines

print(f"Found {len(words)} words and {len(lines)} lines")
```

### Working with Text Elements

```python
# Access word properties
for word in page.words[:5]:  # First 5 words
    print(f"'{word.text}' at position ({word.x0}, {word.top})")
    print(f"Word dimensions: {word.x1 - word.x0} x {word.bottom - word.top}")

# Access line properties
for line in page.lines[:3]:  # First 3 lines
    print(f"Line: '{line.text}'")
    print(f"Line words: {len(line.words)}")
```

### Position-based Operations

```python
from pyntagma import Position, HorizontalCoordinate, VerticalCoordinate

# Create custom positions
position = Position(
    x0=HorizontalCoordinate(page=page, value=100),
    x1=HorizontalCoordinate(page=page, value=200),
    top=VerticalCoordinate(page=page, value=50),
    bottom=VerticalCoordinate(page=page, value=80)
)

# Check if one position contains another
word_position = page.words[0].position
if position.contains(word_position):
    print("Word is within the specified region")
```

### PDF Cropping

```python
from pyntagma import Crop

# Define a crop region
crop = Crop(
    path=Path("document.pdf"),
    page_number=0,
    x0=100.0,
    x1=400.0,
    top=50.0,
    bottom=200.0,
    padding=10,
    resolution=300
)

# Use the crop for further processing
print(f"Crop region: {crop}")
```

## API Reference

### Core Classes

#### `Document`
Represents a multi-file PDF document.

**Properties:**
- `files: list[Path]` - List of PDF files comprising the document
- `pages: list[Page]` - All pages across all files
- `n_pages: int` - Total number of pages

#### `Page`
Represents a single page within a document.

**Properties:**
- `path: Path` - Path to the PDF file containing this page
- `file_page_number: int` - Page number within the file (0-indexed)
- `page_number: int` - Page number within the document (0-indexed)
- `words: list[Word]` - All words on the page
- `lines: list[Line]` - All lines on the page
- `height: float` - Page height in points
- `width: float` - Page width in points

#### `Word`
Represents a single word with position information.

**Properties:**
- `page: Page` - The page containing this word
- `text: str` - The word text
- `x0, x1: float` - Horizontal boundaries
- `top, bottom: float` - Vertical boundaries
- `position: Position` - Position object for spatial operations
- `line: Line` - The line containing this word

#### `Line`
Represents a line of text with position information.

**Properties:**
- `page: Page` - The page containing this line
- `text: str` - The complete line text
- `x0, x1: float` - Horizontal boundaries
- `top, bottom: float` - Vertical boundaries
- `position: Position` - Position object for spatial operations
- `words: list[Word]` - Words within this line

#### `Position`
Represents a rectangular region on a page.

**Properties:**
- `x0, x1: HorizontalCoordinate` - Horizontal boundaries
- `top, bottom: VerticalCoordinate` - Vertical boundaries

**Methods:**
- `contains(other: Position) -> bool` - Check if this position contains another

#### `Crop`
Defines a rectangular region for extraction from a PDF page.

**Properties:**
- `path: Path` - PDF file path
- `page_number: int` - Target page number
- `x0, x1: float` - Horizontal boundaries
- `top, bottom: float` - Vertical boundaries
- `padding: int = 0` - Padding around the crop region
- `resolution: int = 600` - Output resolution for image extraction

### Coordinate System

Pyntagma uses the standard PDF coordinate system:
- Origin (0,0) is at the bottom-left corner
- X-axis extends horizontally to the right
- Y-axis extends vertically upward
- All measurements are in points (1/72 inch)

### Utility Functions

- `words_of_line(line: Line) -> list[Word]` - Extract words from a line
- `line_of_word(word: Word) -> Line` - Find the line containing a word
- `silent_pdfplumber(path, **kwargs)` - Context manager for silent PDF processing

## Development

### Setting up the Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd pyntagma

# Install dependencies with uv
uv sync --group test

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov=src/pyntagma --cov-report=html
```

### Running Tests

The test suite includes comprehensive tests for all major functionality:

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_document.py

# Run with verbose output
uv run pytest -v
```

### Test Coverage

Current test coverage: **80%**

Coverage breakdown:
- `__init__.py`: 100%
- `document.py`: 90%
- `pdf_reader.py`: 75%
- `position.py`: 77%

To generate coverage reports:

```bash
uv run pytest --cov=src/pyntagma --cov-report=html
# Open htmlcov/index.html in your browser
```

## Requirements

- Python 3.9+
- pydantic >= 2.0.0
- pdfplumber >= 0.9.0

### Development Requirements

- pytest >= 7.0.0
- pytest-cov >= 4.0.0

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass (`uv run pytest`)
6. Commit your changes (`git commit -m 'Add amazing feature'`)
7. Push to the branch (`git push origin feature/amazing-feature`)
8. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Author

**MarcellGranat** - [granatcellmar98@gmail.com](mailto:granatcellmar98@gmail.com)

## Acknowledgments

- Built with [Pydantic](https://pydantic.dev/) for robust data validation
- PDF processing powered by [pdfplumber](https://github.com/jsvine/pdfplumber)
- Uses [uv](https://docs.astral.sh/uv/) for fast Python package management