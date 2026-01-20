"""EPUB I/O utilities for extraction, parsing, and repackaging."""

import tempfile
import zipfile
from pathlib import Path
from typing import Dict, List, Tuple
from xml.etree import ElementTree as ET

from .models import EpubBook, ManifestItem, SpineItem


def extract_epub(epub_path: Path, temp_dir: Path) -> Path:
    """
    Extract EPUB ZIP to temporary directory.
    
    Args:
        epub_path: Path to EPUB file
        temp_dir: Temporary directory for extraction
    
    Returns:
        Path to extracted root directory
    
    Raises:
        zipfile.BadZipFile: If file is not a valid ZIP
        IOError: If extraction fails
    """
    if not epub_path.exists():
        raise FileNotFoundError(f"EPUB file not found: {epub_path}")
    
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(epub_path, "r") as zip_file:
        zip_file.extractall(temp_dir)
    
    return temp_dir


def parse_container(container_path: Path) -> Path:
    """
    Parse META-INF/container.xml to find OPF path.
    
    Args:
        container_path: Path to container.xml
    
    Returns:
        Path to OPF file (relative to EPUB root)
    
    Raises:
        XMLSyntaxError: If container.xml is malformed
        ValueError: If OPF reference not found
    """
    try:
        tree = ET.parse(container_path)
    except ET.ParseError as e:
        raise ValueError(f"Malformed container.xml: {e}") from e
    
    root = tree.getroot()
    
    # EPUB container namespace
    ns = {"ocf": "urn:oasis:names:tc:opendocument:xmlns:container"}
    
    # Find rootfile with media-type="application/oebps-package+xml" or "application/epub+zip"
    rootfiles = root.findall(".//ocf:rootfile", ns)
    for rootfile in rootfiles:
        media_type = rootfile.get("media-type", "")
        if media_type in ("application/oebps-package+xml", "application/epub+zip"):
            opf_path_str = rootfile.get("full-path", "")
            if opf_path_str:
                return Path(opf_path_str)
    
    raise ValueError("OPF file reference not found in container.xml")


def parse_opf(opf_path: Path, root_path: Path) -> Tuple[List[SpineItem], Dict[str, ManifestItem]]:
    """
    Parse OPF file to extract spine and manifest.
    
    Args:
        opf_path: Path to OPF file
        root_path: EPUB root directory for resolving relative paths
    
    Returns:
        Tuple of (spine_items, manifest_items)
    
    Raises:
        XMLSyntaxError: If OPF is malformed
        ValueError: If required elements missing
    """
    try:
        tree = ET.parse(opf_path)
    except ET.ParseError as e:
        raise ValueError(f"Malformed OPF file: {e}") from e
    
    root = tree.getroot()
    
    # EPUB namespaces (handle both EPUB 2 and 3)
    ns = {
        "opf": "http://www.idpf.org/2007/opf",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    
    # Parse manifest
    manifest_items: Dict[str, ManifestItem] = {}
    manifest_elem = root.find(".//opf:manifest", ns)
    if manifest_elem is None:
        raise ValueError("Manifest element not found in OPF")
    
    for item_elem in manifest_elem.findall("opf:item", ns):
        item_id = item_elem.get("id")
        href = item_elem.get("href", "")
        media_type = item_elem.get("media-type", "")
        
        if item_id:
            # Resolve href relative to OPF location
            opf_parent = opf_path.parent
            absolute_href = (opf_parent / href).resolve()
            # Get relative path from root
            try:
                resolved_href = absolute_href.relative_to(root_path.resolve())
            except ValueError:
                # If not relative, use the href as-is
                resolved_href = Path(href)
            
            manifest_items[item_id] = ManifestItem(
                id=item_id,
                href=resolved_href,
                media_type=media_type
            )
    
    # Parse spine
    spine_items: List[SpineItem] = []
    spine_elem = root.find(".//opf:spine", ns)
    if spine_elem is None:
        raise ValueError("Spine element not found in OPF")
    
    for itemref_elem in spine_elem.findall("opf:itemref", ns):
        idref = itemref_elem.get("idref", "")
        if idref and idref in manifest_items:
            manifest_item = manifest_items[idref]
            # Resolve to absolute path
            absolute_href = root_path / manifest_item.href
            
            spine_items.append(SpineItem(
                idref=idref,
                href=absolute_href
            ))
    
    return spine_items, manifest_items


def repackage_epub(temp_dir: Path, output_path: Path) -> None:
    """
    Create EPUB ZIP from temporary directory.
    
    Args:
        temp_dir: Temporary directory with EPUB contents
        output_path: Path to output EPUB file
    
    Raises:
        IOError: If ZIP creation fails
    
    Notes:
        - mimetype must be first entry (uncompressed)
        - Preserve directory structure
        - Use ZIP_DEFLATED compression (except mimetype)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add mimetype first, uncompressed (EPUB spec requirement)
        mimetype_path = temp_dir / "mimetype"
        if mimetype_path.exists():
            zip_file.write(mimetype_path, "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Add all other files
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "mimetype":
                arcname = file_path.relative_to(temp_dir)
                zip_file.write(file_path, arcname, compress_type=zipfile.ZIP_DEFLATED)
