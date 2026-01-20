"""EPUB version detection and metadata helpers."""

from pathlib import Path
from typing import Tuple
from xml.etree import ElementTree as ET


def locate_opf_path(container_path: Path) -> Path:
    """
    Locate the OPF path from container.xml.
    
    Args:
        container_path: Path to META-INF/container.xml
    
    Returns:
        Path to OPF file (relative to EPUB root)
    
    Raises:
        ValueError: If container.xml is malformed or OPF not found
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


def detect_epub_version(opf_tree: ET.ElementTree) -> Tuple[str, str]:
    """
    Detect EPUB version from OPF package element.
    
    Args:
        opf_tree: Parsed OPF XML tree
    
    Returns:
        Tuple of (normalized_version, raw_version)
        - normalized_version: "2" or "3"
        - raw_version: Full version string like "2.0", "2.0.1", "3.0", "3.2"
    
    Raises:
        ValueError: If version attribute not found
    """
    root = opf_tree.getroot()
    
    # Check for package element
    if root.tag != "{http://www.idpf.org/2007/opf}package":
        # Try without namespace
        if root.tag == "package":
            pass
        else:
            raise ValueError(f"Expected <package> element, found <{root.tag}>")
    
    version = root.get("version")
    if not version:
        raise ValueError("No version attribute found in <package> element")
    
    # Normalize version
    version_parts = version.split(".")
    major_version = version_parts[0]
    
    if major_version == "2":
        normalized = "2"
    elif major_version == "3":
        normalized = "3"
    else:
        # Unknown version, but return as-is
        normalized = major_version
    
    return normalized, version


def load_opf(opf_path: Path) -> ET.ElementTree:
    """
    Load OPF file into XML tree.
    
    Args:
        opf_path: Path to OPF file
    
    Returns:
        Parsed ElementTree
    
    Raises:
        ValueError: If OPF is malformed
    """
    try:
        return ET.parse(opf_path)
    except ET.ParseError as e:
        raise ValueError(f"Malformed OPF file: {e}") from e
