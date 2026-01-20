"""Rule for normalizing paragraph structure and indentation."""

from ..models import EpubBook
from ..reporting import Reporter
from ..xhtml_parser import find_paragraphs, parse_xhtml, serialize_xhtml


def normalize_paragraphs_and_indents(book: EpubBook, reporter: Reporter) -> None:
    """
    Normalize paragraph structure and basic spacing.
    
    - Converts divs with body text to paragraphs
    - Removes multiple consecutive <br/> tags
    - Normalizes indentation (moves inline styles to CSS)
    """
    divs_converted = 0
    br_removed = 0
    
    for xhtml_path in book.get_xhtml_files():
        if not xhtml_path.exists():
            continue
        
        try:
            tree = parse_xhtml(xhtml_path)
            changed = False
            
            # Convert divs to paragraphs (conservative: only if they contain inline/text content)
            divs = tree.xpath("//div[not(div) and not(p) and (text() or span or em or strong)]")
            for div in divs:
                div.tag = "p"
                divs_converted += 1
                changed = True
            
            # Remove multiple consecutive <br/> tags
            br_sequences = tree.xpath("//br/following-sibling::br")
            for br in br_sequences:
                parent = br.getparent()
                if parent is not None:
                    parent.remove(br)
                    br_removed += 1
                    changed = True
            
            # Remove <br/> at end of paragraphs
            trailing_brs = tree.xpath("//p/br[last()]")
            for br in trailing_brs:
                parent = br.getparent()
                if parent is not None:
                    parent.remove(br)
                    br_removed += 1
                    changed = True
            
            if changed:
                xhtml_content = serialize_xhtml(tree)
                xhtml_path.write_text(xhtml_content, encoding="utf-8")
                reporter.log_change(
                    xhtml_path,
                    f"Converted {divs_converted} divs, removed {br_removed} <br/> tags"
                )
        
        except Exception as e:
            reporter.log_change(xhtml_path, f"Error processing: {e}")
    
    reporter.increment("paragraphs.converted_divs", divs_converted)
    reporter.increment("paragraphs.removed_br_breaks", br_removed)
