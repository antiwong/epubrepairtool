"""Rule for normalizing lists to semantic HTML."""

import re
from ..models import EpubBook
from ..reporting import Reporter
from ..xhtml_parser import find_paragraphs, parse_xhtml, serialize_xhtml


def normalize_lists(book: EpubBook, reporter: Reporter) -> None:
    """
    Convert visual lists to semantic lists.
    
    Detects paragraphs that look like lists and groups them into
    proper <ul>/<ol> structures.
    """
    lists_created = 0
    
    for xhtml_path in book.get_xhtml_files():
        if not xhtml_path.exists():
            continue
        
        try:
            tree = parse_xhtml(xhtml_path)
            paragraphs = find_paragraphs(tree)
            
            # Pattern to detect list-like paragraphs
            unordered_pattern = re.compile(r'^[-•*]\s+')
            ordered_pattern = re.compile(r'^\d+\.\s+')
            
            i = 0
            while i < len(paragraphs):
                p = paragraphs[i]
                text = (p.text or "").strip()
                
                # Check if this paragraph looks like a list item
                is_unordered = bool(unordered_pattern.match(text))
                is_ordered = bool(ordered_pattern.match(text))
                
                if is_unordered or is_ordered:
                    # Find consecutive list-like paragraphs
                    list_items = []
                    j = i
                    while j < len(paragraphs):
                        p_item = paragraphs[j]
                        text_item = (p_item.text or "").strip()
                        
                        if is_unordered and unordered_pattern.match(text_item):
                            list_items.append((p_item, False))
                            j += 1
                        elif is_ordered and ordered_pattern.match(text_item):
                            list_items.append((p_item, True))
                            j += 1
                        else:
                            break
                    
                    if list_items:
                        # Create list element
                        from lxml import etree
                        list_tag = "ol" if is_ordered else "ul"
                        list_elem = etree.Element(list_tag)
                        
                        # Convert paragraphs to list items
                        for p_elem, was_ordered in list_items:
                            li = etree.Element("li")
                            
                            # Remove bullet/number prefix
                            text_content = (p_elem.text or "").strip()
                            if was_ordered:
                                text_content = re.sub(r'^\d+\.\s+', '', text_content)
                            else:
                                text_content = re.sub(r'^[-•*]\s+', '', text_content)
                            
                            li.text = text_content
                            
                            # Copy children
                            for child in p_elem:
                                li.append(child)
                            
                            list_elem.append(li)
                            
                            # Remove original paragraph
                            parent = p_elem.getparent()
                            if parent is not None:
                                parent.remove(p_elem)
                        
                        # Insert list before first removed paragraph's position
                        if list_items:
                            first_p = list_items[0][0]
                            parent = first_p.getparent()
                            if parent is not None:
                                # Find insertion point (before next sibling or at end)
                                parent.insert(parent.index(first_p) if first_p in parent else len(parent), list_elem)
                        
                        lists_created += 1
                        i = j
                        continue
                
                i += 1
            
            if lists_created > 0:
                xhtml_content = serialize_xhtml(tree)
                xhtml_path.write_text(xhtml_content, encoding="utf-8")
                reporter.log_change(xhtml_path, f"Created {lists_created} semantic lists")
        
        except Exception as e:
            reporter.log_change(xhtml_path, f"Error processing: {e}")
    
    reporter.increment("lists.converted_paragraphs", lists_created)
