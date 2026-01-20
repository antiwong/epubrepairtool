"""Rule for normalizing scene breaks and spacing."""

from ..models import EpubBook
from ..reporting import Reporter
from ..xhtml_parser import parse_xhtml, serialize_xhtml


def normalize_context_breaks(book: EpubBook, reporter: Reporter) -> None:
    """
    Normalize scene/section breaks and remove unwanted page breaks.
    
    - Detects runs of empty paragraphs or repeated <br/> tags used as scene breaks
    - Removes page breaks (empty spaces) except those before chapter headings
    - Only keeps page breaks between chapters (before h1/h2 headings)
    """
    scene_breaks_created = 0
    page_breaks_removed = 0
    
    for xhtml_path in book.get_xhtml_files():
        if not xhtml_path.exists():
            continue
        
        try:
            tree = parse_xhtml(xhtml_path)
            changed = False
            
            # Find and remove page breaks (empty paragraphs/spacing)
            # Keep only those before chapter headings (h1, h2)
            paragraphs = tree.xpath("//p")
            paragraphs_to_remove = []
            
            for i, p in enumerate(paragraphs):
                text = (p.text or "").strip()
                
                # Check if this is a potential page break
                is_page_break = False
                if not text and len(p) == 0:
                    # Empty paragraph
                    is_page_break = True
                elif p.get("class", "").lower() in ("page-break", "pagebreak", "break"):
                    # Has page-break class
                    is_page_break = True
                elif "page-break" in p.get("style", "").lower() or "pagebreak" in p.get("style", "").lower():
                    # Has page-break in style
                    is_page_break = True
                
                if is_page_break:
                    # Check if this page break should be kept (before/after chapter)
                    is_before_chapter = False
                    
                    # Check if next sibling is a chapter heading
                    next_sibling = p.getnext()
                    if next_sibling is not None and next_sibling.tag in ("h1", "h2"):
                        heading_text = (next_sibling.text or "").strip().lower()
                        # Check if it looks like a chapter
                        if any(keyword in heading_text for keyword in ["chapter", "part", "book"]):
                            is_before_chapter = True
                        # Also check if it's early in document (likely first chapter)
                        elif i < 3:
                            is_before_chapter = True
                    
                    # Check if this is the first element in body (likely before first chapter)
                    if not is_before_chapter:
                        parent = p.getparent()
                        if parent is not None:
                            # Check if this is one of the first few elements in body
                            body_children = list(parent)
                            if p in body_children:
                                p_index = body_children.index(p)
                                # If it's in first 3 elements and next is a heading, keep it
                                if p_index < 3 and next_sibling is not None and next_sibling.tag in ("h1", "h2"):
                                    is_before_chapter = True
                    
                    # Remove if NOT before a chapter
                    if not is_before_chapter:
                        paragraphs_to_remove.append(p)
            
            # Remove identified page breaks
            for p in paragraphs_to_remove:
                parent = p.getparent()
                if parent is not None:
                    parent.remove(p)
                    page_breaks_removed += 1
                    changed = True
            
            # Find sequences of empty paragraphs (2+) - these are scene breaks
            paragraphs = tree.xpath("//p")
            i = 0
            while i < len(paragraphs):
                empty_count = 0
                start_idx = i
                
                # Count consecutive empty paragraphs
                while i < len(paragraphs):
                    p = paragraphs[i]
                    text = (p.text or "").strip()
                    if not text and len(p) == 0:
                        empty_count += 1
                        i += 1
                    else:
                        break
                
                # Replace 2+ empty paragraphs with <hr> (scene break)
                if empty_count >= 2:
                    from lxml import etree
                    hr = etree.Element("hr")
                    hr.set("class", "scene-break")
                    
                    # Remove empty paragraphs and insert <hr>
                    parent = paragraphs[start_idx].getparent()
                    if parent is not None:
                        for j in range(empty_count):
                            parent.remove(paragraphs[start_idx + j])
                        parent.insert(start_idx, hr)
                        scene_breaks_created += 1
                        changed = True
                
                if i < len(paragraphs):
                    i += 1
            
            # Find sequences of 3+ <br/> tags - these are scene breaks
            br_sequences = tree.xpath("//br[count(following-sibling::br) >= 2]")
            for br in br_sequences:
                parent = br.getparent()
                if parent is not None:
                    # Count consecutive <br/> tags
                    br_count = 1
                    next_sibling = br.getnext()
                    while next_sibling is not None and next_sibling.tag == "br":
                        br_count += 1
                        next_sibling = next_sibling.getnext()
                    
                    # Check if this is before a chapter heading
                    is_before_chapter = False
                    next_elem = br.getnext()
                    if next_elem is not None and next_elem.tag in ("h1", "h2"):
                        heading_text = (next_elem.text or "").strip().lower()
                        if any(keyword in heading_text for keyword in ["chapter", "part", "book"]):
                            is_before_chapter = True
                    
                    # Only convert to <hr> if NOT before chapter (scene break, not page break)
                    if br_count >= 3 and not is_before_chapter:
                        from lxml import etree
                        hr = etree.Element("hr")
                        hr.set("class", "scene-break")
                        
                        # Replace <br/> tags with <hr>
                        parent.replace(br, hr)
                        for _ in range(br_count - 1):
                            next_br = hr.getnext()
                            if next_br is not None and next_br.tag == "br":
                                parent.remove(next_br)
                        
                        scene_breaks_created += 1
                        changed = True
                    elif br_count >= 3 and is_before_chapter:
                        # Remove excessive <br/> before chapter (keep only one for spacing)
                        for _ in range(br_count - 1):
                            next_br = br.getnext()
                            if next_br is not None and next_br.tag == "br":
                                parent.remove(next_br)
                        page_breaks_removed += br_count - 1
                        changed = True
            
            # Remove CSS page-break properties from non-chapter elements
            # (This will be handled by CSS cleanup, but we can also remove inline styles here)
            elements_with_page_break = tree.xpath("//*[contains(@style, 'page-break') or contains(@style, 'pagebreak')]")
            for elem in elements_with_page_break:
                # Keep page-break only if it's before a chapter heading
                next_sibling = elem.getnext()
                is_before_chapter = False
                if next_sibling is not None and next_sibling.tag in ("h1", "h2"):
                    heading_text = (next_sibling.text or "").strip().lower()
                    if any(keyword in heading_text for keyword in ["chapter", "part", "book"]):
                        is_before_chapter = True
                
                if not is_before_chapter:
                    # Remove page-break from style
                    style = elem.get("style", "")
                    # Simple removal - could be enhanced
                    new_style = style.replace("page-break-before: always;", "").replace("page-break-after: always;", "")
                    new_style = new_style.replace("page-break-before:always;", "").replace("page-break-after:always;", "")
                    new_style = new_style.replace("pagebreak: always;", "").replace("pagebreak:always;", "")
                    if new_style != style:
                        if new_style.strip():
                            elem.set("style", new_style)
                        else:
                            elem.attrib.pop("style", None)
                        page_breaks_removed += 1
                        changed = True
            
            if changed:
                xhtml_content = serialize_xhtml(tree)
                xhtml_path.write_text(xhtml_content, encoding="utf-8")
                changes = []
                if scene_breaks_created > 0:
                    changes.append(f"Created {scene_breaks_created} scene breaks")
                if page_breaks_removed > 0:
                    changes.append(f"Removed {page_breaks_removed} page breaks")
                if changes:
                    reporter.log_change(xhtml_path, "; ".join(changes))
        
        except Exception as e:
            reporter.log_change(xhtml_path, f"Error processing: {e}")
    
    reporter.increment("breaks.normalized_scene_breaks", scene_breaks_created)
    reporter.increment("breaks.removed_page_breaks", page_breaks_removed)
