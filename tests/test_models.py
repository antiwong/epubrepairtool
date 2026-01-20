"""Tests for data models."""

from pathlib import Path

import pytest

from epub_repair.models import EpubBook, ManifestItem, SpineItem


def test_spine_item_validation():
    """Test SpineItem validation."""
    with pytest.raises(ValueError, match="idref cannot be empty"):
        SpineItem(idref="", href=Path("test.xhtml"))


def test_manifest_item_validation():
    """Test ManifestItem validation."""
    with pytest.raises(ValueError, match="id cannot be empty"):
        ManifestItem(id="", href=Path("test.xhtml"), media_type="application/xhtml+xml")
    
    with pytest.raises(ValueError, match="media_type cannot be empty"):
        ManifestItem(id="test", href=Path("test.xhtml"), media_type="")


def test_epub_book_get_xhtml_files():
    """Test EpubBook.get_xhtml_files()."""
    root = Path("/tmp/test")
    opf = root / "content.opf"
    
    spine_items = [
        SpineItem(idref="ch1", href=root / "ch1.xhtml"),
        SpineItem(idref="ch2", href=root / "ch2.xhtml"),
    ]
    
    manifest_items = {
        "ch1": ManifestItem(
            id="ch1",
            href=Path("ch1.xhtml"),
            media_type="application/xhtml+xml"
        ),
        "ch2": ManifestItem(
            id="ch2",
            href=Path("ch2.xhtml"),
            media_type="application/xhtml+xml"
        ),
        "style": ManifestItem(
            id="style",
            href=Path("style.css"),
            media_type="text/css"
        ),
    }
    
    book = EpubBook(
        root_path=root,
        opf_path=opf,
        spine_items=spine_items,
        manifest_items=manifest_items
    )
    
    xhtml_files = book.get_xhtml_files()
    assert len(xhtml_files) == 2
    assert root / "ch1.xhtml" in xhtml_files
    assert root / "ch2.xhtml" in xhtml_files


def test_epub_book_get_css_files():
    """Test EpubBook.get_css_files()."""
    root = Path("/tmp/test")
    opf = root / "content.opf"
    
    spine_items = []
    manifest_items = {
        "style1": ManifestItem(
            id="style1",
            href=Path("style1.css"),
            media_type="text/css"
        ),
        "style2": ManifestItem(
            id="style2",
            href=Path("style2.css"),
            media_type="text/css"
        ),
    }
    
    book = EpubBook(
        root_path=root,
        opf_path=opf,
        spine_items=spine_items,
        manifest_items=manifest_items
    )
    
    css_files = book.get_css_files()
    assert len(css_files) == 2
