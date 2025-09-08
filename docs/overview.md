# Overview

Pyntagma is a modern, standardized toolkit for working with documents—focused on PDFs today—with a clean, composable API. Its goal is to bring together proven techniques in document analysis into one convenient library so practitioners and researchers can define precise, reusable rules to extract data from large, heterogeneous archives.

## Goals

- Unified primitives for geometry and text structure (Pages, Positions, Lines/Words/Chars).
- Composable “algebra” on positions for robust region selection and matching.
- Bidirectional navigation helpers to move between text units reliably.
- Interop-friendly models using Pydantic for clarity and validation.
- Quiet, predictable PDF I/O on top of pdfplumber.

## Core Building Blocks

- `Document`, `Page`: Open one or more PDF files and iterate pages consistently.
- `Position`, `Vertical/HorizontalCoordinate`: Represent regions with precise arithmetic and comparisons.
- `PdfAnchor` and text anchors (`Line`, `Word`, `Char`): Attach semantics to regions.
- `Crop`: Render any position to an image/bytes for visualization or multimodal AI.

## Quick Start

```python
from pathlib import Path
from pyntagma import Document

doc = Document(files=[Path("tests/test_pdfs/test-1.pdf")])
page = doc.pages[0]

# Navigate text
first_line = page.lines[0]
words = first_line.words

# Work with geometry
bbox = first_line.position.bbox
crop = first_line.position.crop  # PIL image via pdfplumber
crop.save("line.png")
```

Continue with Concepts for how the algebra compares to bidirectional navigation, and see AI Tools for model-assisted workflows.
