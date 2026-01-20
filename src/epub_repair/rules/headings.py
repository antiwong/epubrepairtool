"""Rule for normalizing headings to semantic HTML."""

from ..models import EpubBook
from ..reporting import Reporter
from ..xhtml_parser import find_headings, parse_xhtml, serialize_xhtml


def normalize_headings(book: EpubBook, reporter: Reporter) -> None:
    """
    Normalize fake headings to semantic h1-h3 elements.
    
    Detects fake headings (e.g., <p class="heading1">) and converts them
    to proper semantic headings. Ensures proper heading hierarchy and
    fixes nesting issues.
    """
    converted_count = 0
    nesting_fixes = 0
    
    for xhtml_path in book.get_xhtml_files():
        if not xhtml_path.exists():
            reporter.log_change(xhtml_path, f"File not found, skipping")
            continue
        
        try:
            tree = parse_xhtml(xhtml_path)
            
            # Find fake headings (paragraphs with heading-like classes)
            fake_heading_patterns = [
                "//p[contains(@class, 'heading')]",
                "//p[contains(@class, 'chapter')]",
                "//p[contains(@class, 'section')]",
                "//p[contains(@class, 'title')]",
            ]
            
            for pattern in fake_heading_patterns:
                fake_headings = tree.xpath(pattern)
                for p_elem in fake_headings:
                    # Determine heading level based on class
                    level = _determine_heading_level(p_elem)
                    if level:
                        # Convert to semantic heading
                        _convert_to_heading(p_elem, level, tree)
                        converted_count += 1
            
            # Fix nested headings
            nested_headings = tree.xpath("//p//h1 | //p//h2 | //p//h3 | //p//h4 | //p//h5 | //p//h6")
            for heading in nested_headings:
                parent = heading.getparent()
                if parent is not None and parent.tag == "p":
                    # Move heading out of paragraph
                    parent.addprevious(heading)
                    # Remove empty paragraph if it has no other content
                    if not parent.text and len(parent) == 0:
                        parent.getparent().remove(parent)
                    nesting_fixes += 1
            
            # Write back if changes were made
            if converted_count > 0 or nesting_fixes > 0:
                xhtml_content = serialize_xhtml(tree)
                xhtml_path.write_text(xhtml_content, encoding="utf-8")
                reporter.log_change(
                    xhtml_path,
                    f"Converted {converted_count} fake headings, fixed {nesting_fixes} nesting issues"
                )
        
        except Exception as e:
            reporter.log_change(xhtml_path, f"Error processing: {e}")
    
    reporter.increment("headings.converted_fake_headings", converted_count)
    reporter.increment("headings.fixed_nesting", nesting_fixes)


def _determine_heading_level(element) -> int:
    """Determine appropriate heading level (1-3) based on element class."""
    classes = element.get("class", "").lower()
    
    if "heading1" in classes or "h1" in classes or "title" in classes:
        return 1
    elif "heading2" in classes or "h2" in classes or "chapter" in classes:
        return 2
    elif "heading3" in classes or "h3" in classes or "section" in classes:
        return 3
    else:
        # Default to h2 for chapter-like content
        return 2


def _convert_to_heading(element, level: int, tree) -> None:
    """Convert a paragraph element to a heading element."""
    from lxml import etree
    
    # Create new heading element
    tag = f"h{level}"
    heading = etree.Element(tag)
    
    # Copy text content and children
    if element.text:
        heading.text = element.text
    for child in element:
        heading.append(child)
        if child.tail:
            # Preserve tail text
            if len(heading) > 0:
                heading[-1].tail = (heading[-1].tail or "") + child.tail
            else:
                heading.text = (heading.text or "") + child.tail
    
    # Copy relevant attributes (exclude heading-related classes)
    for attr, value in element.attrib.items():
        if attr != "class" or "heading" not in value.lower():
            heading.set(attr, value)
    
    # Replace the paragraph with the heading
    parent = element.getparent()
    if parent is not None:
        parent.replace(element, heading)
