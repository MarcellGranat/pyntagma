"""Thin wrappers around pdfplumber for quiet PDF IO and cropping.

Includes a `silent` context manager to suppress stdout/stderr and a `Crop`
utility for extracting regions from a page as images/bytes.
"""

import logging
import os
import sys
from contextlib import contextmanager
from io import BytesIO
from pathlib import Path

import pdfplumber
from PIL.Image import Image
from pydantic import BaseModel


@contextmanager
def silent():
    """Temporarily silence stdout/stderr and lower logging during a block."""
    devnull = open(os.devnull, "w")
    old_stdout, old_stderr = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = devnull, devnull
    old_log_level = logging.getLogger().level
    logging.getLogger().setLevel(logging.CRITICAL + 1)
    try:
        yield
    finally:
        sys.stdout, sys.stderr = old_stdout, old_stderr
        logging.getLogger().setLevel(old_log_level)
        devnull.close()


@contextmanager
def silent_pdfplumber(path_or_fp, **kwargs):
    """Open a pdfplumber PDF while suppressing output within the block."""
    with silent():
        with pdfplumber.open(path_or_fp=path_or_fp, **kwargs) as pdf:
            yield pdf


class Crop(BaseModel):
    """Represents a rectangular crop on a PDF page and utilities to render it."""
    path: Path
    page_number: int
    x0: float
    x1: float
    top: float
    bottom: float
    padding: int = 0
    resolution: int = 600

    def __str__(self):
        return f"Crop(x0={self.x0}, x1={self.x1}, top={self.top}, bottom={self.bottom})"

    def __repr__(self):
        return f"Crop(x0={self.x0}, x1={self.x1}, top={self.top}, bottom={self.bottom})"

    def __hash__(self):
        return hash(
            (self.path, self.page_number, self.x0, self.x1, self.top, self.bottom)
        )

    @property
    def im(self) -> Image:
        """Return the PIL image for this crop (respects padding/resolution)."""
        with silent_pdfplumber(self.path) as pdf:
            x0 = max(self.x0 - self.padding, 0)
            x1 = min(self.x1 + self.padding, pdf.pages[self.page_number].width)
            top = max(self.top - self.padding, 0)
            bottom = min(self.bottom + self.padding, pdf.pages[self.page_number].height)

            page = pdf.pages[self.page_number]
            cropped = page.within_bbox((x0, top, x1, bottom))
            return cropped.to_image(resolution=self.resolution).original

    def save(self, path: Path | str = Path("crop.png")):
        """
        Save the cropped image to a file.
        """
        im = self.im
        im.save(path, format="PNG")

    @property
    def buffer(self) -> BytesIO:
        """
        Get the cropped image as a BytesIO object.
        """
        im = self.im
        buffer = BytesIO()
        im.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer

    @property
    def bytes(self) -> bytes:
        """
        Get the cropped image as bytes.
        """
        return self.buffer.getvalue()
