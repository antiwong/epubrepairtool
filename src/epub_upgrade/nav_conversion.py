"""NCX to nav.xhtml conversion for EPUB 2 → EPUB 3 upgrade."""

from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET


def find_ncx_in_manifest(opf_tree: ET.ElementTree, extracted_root: Path, opf_path: Path) -> Optional[Path]:
    """
    Find NCX file in manifest and return its path.
    
    Args:
        opf_tree: Parsed OPF tree
        extracted_root: Root of extracted EPUB
        opf_path: Path to OPF file
    
    Returns:
        Path to NCX file if found, None otherwise
    """
    root = opf_tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    
    manifest = root.find(".//opf:manifest", ns)
    if manifest is None:
        return None
    
    opf_dir = opf_path.parent
    
    for item in manifest.findall("opf:item", ns):
        media_type = item.get("media-type", "")
        if media_type == "application/x-dtbncx+xml":
            href = item.get("href", "")
            if href:
                # Resolve relative to OPF location
                ncx_path = (opf_dir / href).resolve()
                if ncx_path.exists():
                    return ncx_path
    
    return None


def parse_ncx(ncx_path: Path) -> ET.Element:
    """
    Parse NCX file and extract navigation structure.
    
    Args:
        ncx_path: Path to NCX file
    
    Returns:
        Root element of parsed NCX
    
    Raises:
        ValueError: If NCX is malformed
    """
    try:
        tree = ET.parse(ncx_path)
        return tree.getroot()
    except ET.ParseError as e:
        raise ValueError(f"Malformed NCX file: {e}") from e


def convert_ncx_to_nav_xhtml(ncx_path: Path, extracted_root: Path, opf_dir: Path) -> Path:
    """
    Convert NCX to EPUB 3 nav.xhtml.
    
    Args:
        ncx_path: Path to source NCX file
        extracted_root: Root of extracted EPUB
        opf_dir: Directory containing OPF (for relative path resolution)
    
    Returns:
        Path to created nav.xhtml file (relative to extracted_root)
    """
    ncx_root = parse_ncx(ncx_path)
    
    # NCX namespace
    ncx_ns = {"ncx": "http://www.daisy.org/z3986/2005/ncx/"}
    
    # Find navMap
    nav_map = ncx_root.find(".//ncx:navMap", ncx_ns)
    if nav_map is None:
        raise ValueError("No navMap found in NCX")
    
    # Create nav.xhtml
    html = ET.Element("html", xmlns="http://www.w3.org/1999/xhtml", xmlns_epub="http://www.idpf.org/2007/ops")
    head = ET.SubElement(html, "head")
    title = ET.SubElement(head, "title")
    title.text = "Table of Contents"
    
    body = ET.SubElement(html, "body")
    nav = ET.SubElement(body, "nav", attrib={"epub:type": "toc"})
    h1 = ET.SubElement(nav, "h1")
    h1.text = "Table of Contents"
    
    # Convert navPoints to nested list
    ol = ET.SubElement(nav, "ol")
    _convert_nav_points(nav_map.findall(".//ncx:navPoint", ncx_ns), ol, ncx_ns)
    
    # Save nav.xhtml
    nav_path = opf_dir / "nav.xhtml"
    nav_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with proper XML declaration
    tree = ET.ElementTree(html)
    tree.write(
        nav_path,
        encoding="utf-8",
        xml_declaration=True,
        method="xml"
    )
    
    # Return relative path from extracted_root
    try:
        return nav_path.relative_to(extracted_root)
    except ValueError:
        # If not relative, return absolute path
        return nav_path


def _convert_nav_points(nav_points: list, parent_ol: ET.Element, ncx_ns: dict):
    """
    Recursively convert NCX navPoints to HTML list items.
    
    Args:
        nav_points: List of navPoint elements
        parent_ol: Parent <ol> element to append to
        ncx_ns: NCX namespace dictionary
    """
    for nav_point in nav_points:
        nav_label = nav_point.find("ncx:navLabel", ncx_ns)
        content = nav_point.find("ncx:content", ncx_ns)
        
        if nav_label is None or content is None:
            continue
        
        label_text = nav_label.find("ncx:text", ncx_ns)
        if label_text is None:
            continue
        
        text = label_text.text or ""
        src = content.get("src", "")
        
        # Create list item
        li = ET.SubElement(parent_ol, "li")
        a = ET.SubElement(li, "a", href=src)
        a.text = text
        
        # Handle nested navPoints
        child_nav_points = nav_point.findall("ncx:navPoint", ncx_ns)
        if child_nav_points:
            child_ol = ET.SubElement(li, "ol")
            _convert_nav_points(child_nav_points, child_ol, ncx_ns)


def add_nav_to_manifest(opf_tree: ET.ElementTree, nav_path: Path, opf_dir: Path) -> None:
    """
    Add nav.xhtml to OPF manifest with properties="nav".
    
    Args:
        opf_tree: OPF ElementTree to modify
        nav_path: Path to nav.xhtml (absolute)
        opf_dir: Directory containing OPF
    """
    root = opf_tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf"}
    
    manifest = root.find(".//opf:manifest", ns)
    if manifest is None:
        raise ValueError("No manifest found in OPF")
    
    # Calculate relative path from OPF
    try:
        nav_relative = nav_path.relative_to(opf_dir)
    except ValueError:
        nav_relative = nav_path
    
    # Check if nav already exists
    for item in manifest.findall("opf:item", ns):
        if item.get("properties") == "nav":
            # Update existing nav item
            item.set("href", str(nav_relative))
            item.set("media-type", "application/xhtml+xml")
            return
    
    # Add new nav item
    item = ET.SubElement(manifest, "item")
    item.set("id", "nav")
    item.set("href", str(nav_relative))
    item.set("media-type", "application/xhtml+xml")
    item.set("properties", "nav")
