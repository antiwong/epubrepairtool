"""EPUB I/O utilities for extraction, inspection, and repackaging."""

import tempfile
import zipfile
from pathlib import Path
from typing import Optional

from .versioning import locate_opf_path, load_opf


def verify_epub_file(epub_path: Path) -> None:
    """
    Verify that the input file is a valid ZIP file (EPUB container).
    
    Args:
        epub_path: Path to EPUB file
    
    Raises:
        FileNotFoundError: If file doesn't exist
        zipfile.BadZipFile: If file is not a valid ZIP
    """
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    try:
        with zipfile.ZipFile(epub_path, "r") as zip_file:
            # Try to read the ZIP file
            zip_file.testzip()
    except zipfile.BadZipFile as e:
        raise zipfile.BadZipFile(f"Not a valid EPUB (ZIP) file: {e}") from e


def extract_epub(epub_path: Path, temp_dir: Path) -> Path:
    """
    Extract EPUB ZIP to temporary directory.
    
    Args:
        epub_path: Path to EPUB file
        temp_dir: Temporary directory for extraction
    
    Returns:
        Path to extracted root directory
    """
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(epub_path, "r") as zip_file:
        zip_file.extractall(temp_dir)
    
    return temp_dir


def get_opf_path(extracted_root: Path) -> Path:
    """
    Get the OPF path from container.xml.
    
    Args:
        extracted_root: Root directory of extracted EPUB
    
    Returns:
        Path to OPF file (relative to extracted_root)
    """
    container_path = extracted_root / "META-INF" / "container.xml"
    if not container_path.exists():
        raise ValueError("META-INF/container.xml not found")
    
    opf_relative = locate_opf_path(container_path)
    return extracted_root / opf_relative


def save_opf(opf_tree, opf_path: Path) -> None:
    """
    Save OPF tree back to file.
    
    Args:
        opf_tree: ElementTree to save
        opf_path: Path to save OPF file
    """
    # Ensure parent directory exists
    opf_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with XML declaration and proper formatting
    opf_tree.write(
        opf_path,
        encoding="utf-8",
        xml_declaration=True,
        method="xml"
    )


def repackage_epub(extracted_root: Path, output_path: Path) -> None:
    """
    Create EPUB ZIP from extracted directory.
    
    Args:
        extracted_root: Root directory with EPUB contents
        output_path: Path to output EPUB file
    
    Notes:
        - mimetype must be first entry (uncompressed)
        - Preserve directory structure
        - Use ZIP_DEFLATED compression (except mimetype)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add mimetype first, uncompressed (EPUB spec requirement)
        mimetype_path = extracted_root / "mimetype"
        if mimetype_path.exists():
            zip_file.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Add all other files
        for file_path in extracted_root.rglob("*"):
            if file_path.is_file() and file_path.name != "mimetype":
                arcname = file_path.relative_to(extracted_root)
                zip_file.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)


def copy_epub(input_path: Path, output_path: Path) -> None:
    """
    Copy EPUB file from input to output.
    
    Args:
        input_path: Source EPUB file
        output_path: Destination EPUB file
    """
    import shutil
    output_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(input_path, output_path)
