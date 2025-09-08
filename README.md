# Pyntagma

[![Coverage Status](https://img.shields.io/badge/coverage-80%25-green.svg)](htmlcov/index.html)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Pyntagma is a Python library for creating and managing complex data extraction pipelines with ease. Its name is derived from the Greek word 'Syntagma', meaning 'composition', symbolizing that this package fits for semi-structured documents.

## Features

- **PDF Document Processing**: Extract and analyze text, words, and lines from PDF documents
- **Multi-file Document Support**: Handle documents that span multiple PDF files
- **Precise Positioning**: Track exact coordinates and positions of text elements
- **Type-safe Design**: Built with Pydantic models for robust data validation
- **Silent PDF Processing**: Suppresses verbose logging during PDF operations
- **Flexible Cropping**: Extract specific regions from PDF pages

## Installation

Install Pyntagma using:

```bash
pip install pyntagma
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

