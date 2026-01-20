"""XHTML parsing and serialization utilities."""

from pathlib import Path
from typing import List

try:
    from lxml import etree, html
    LXML_AVAILABLE = True
except ImportError:
    LXML_AVAILABLE = False
    try:
        from bs4 import BeautifulSoup
        BS4_AVAILABLE = True
    except ImportError:
        BS4_AVAILABLE = False


def parse_xhtml(file_path: Path) -> etree._Element:
    """
    Parse XHTML file into lxml Element tree.
    
    Args:
        file_path: Path to XHTML file
    
    Returns:
        Root element of parsed tree
    
    Raises:
        ImportError: If neither lxml nor beautifulsoup4 is available
        XMLSyntaxError: If XHTML is malformed
        IOError: If file cannot be read
    
    Notes:
        - Uses lxml.html.HTMLParser with recover=True for tolerance
        - Falls back to BeautifulSoup if lxml not available
    """
    if not LXML_AVAILABLE and not BS4_AVAILABLE:
        raise ImportError(
            "Either lxml or beautifulsoup4 must be installed. "
            "Install with: pip install lxml or pip install beautifulsoup4"
        )
    
    content = file_path.read_text(encoding="utf-8")
    
    if LXML_AVAILABLE:
        # Use lxml with HTML parser for tolerance of malformed HTML
        parser = html.HTMLParser(recover=True, encoding="utf-8")
        tree = html.fromstring(content.encode("utf-8"), parser=parser)
        return tree
    else:
        # Fallback to BeautifulSoup
        soup = BeautifulSoup(content, "html.parser")
        # Convert to lxml-like structure (simplified)
        # Note: This is a basic fallback; full implementation would need more work
        raise NotImplementedError("BeautifulSoup fallback not yet implemented")


def find_headings(tree: etree._Element) -> List[etree._Element]:
    """
    Find all heading elements (h1-h6) in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of heading elements in document order
    """
    return tree.xpath(".//h1 | .//h2 | .//h3 | .//h4 | .//h5 | .//h6")


def find_paragraphs(tree: etree._Element) -> List[etree._Element]:
    """
    Find all paragraph elements in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of paragraph elements in document order
    """
    return tree.xpath(".//p")


def find_lists(tree: etree._Element) -> List[etree._Element]:
    """
    Find all list elements (ul, ol) in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of list elements in document order
    """
    return tree.xpath(".//ul | .//ol")


def serialize_xhtml(tree: etree._Element, pretty: bool = True) -> str:
    """
    Serialize Element tree to XHTML string.
    
    Args:
        tree: Root element
        pretty: Whether to pretty-print (indent)
    
    Returns:
        XHTML string (UTF-8 encoded)
    
    Notes:
        - Ensures XML declaration
        - Preserves namespace declarations
        - Outputs well-formed XHTML
    """
    if pretty:
        etree.indent(tree, space="  ")
    
    # Serialize to bytes first, then decode
    xml_bytes = etree.tostring(
        tree,
        encoding="utf-8",
        xml_declaration=True,
        method="xml",
        pretty_print=pretty
    )
    return xml_bytes.decode("utf-8")
