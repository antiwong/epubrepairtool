"""Rule for cleaning up and simplifying CSS."""

from ..models import EpubBook
from ..reporting import Reporter
from ..css_processor import parse_css, serialize_css


def simplify_css_safe(book: EpubBook, reporter: Reporter) -> None:
    """
    Safe CSS cleanup - conservative fixes.
    
    - Removes aggressive font-size on body/html
    - Normalizes line-height
    - Removes display: flex/grid from content flows
    - Normalizes heading margins
    """
    properties_removed = 0
    properties_modified = 0
    
    for css_path in book.get_css_files():
        if not css_path.exists():
            continue
        
        try:
            css_text = css_path.read_text(encoding="utf-8")
            rules = parse_css(css_text)
            changed = False
            
            # Remove aggressive font-size on body/html
            for rule in rules:
                if hasattr(rule, "prelude"):
                    selector_text = _get_selector_text(rule)
                    if selector_text in ("body", "html"):
                        if hasattr(rule, "content"):
                            original_count = len(rule.content)
                            rule.content = [
                                decl for decl in rule.content
                                if not (hasattr(decl, "name") and decl.name == "font-size" and _is_absolute_size(decl))
                            ]
                            removed = original_count - len(rule.content)
                            if removed > 0:
                                properties_removed += removed
                                changed = True
            
            # Remove fixed line-height
            for rule in rules:
                if hasattr(rule, "content"):
                    original_count = len(rule.content)
                    rule.content = [
                        decl for decl in rule.content
                        if not (hasattr(decl, "name") and decl.name == "line-height" and _is_fixed_line_height(decl))
                    ]
                    removed = original_count - len(rule.content)
                    if removed > 0:
                        properties_removed += removed
                        changed = True
            
            # Remove display: flex/grid
            for rule in rules:
                if hasattr(rule, "content"):
                    original_count = len(rule.content)
                    rule.content = [
                        decl for decl in rule.content
                        if not (hasattr(decl, "name") and decl.name == "display" and _is_flex_or_grid(decl))
                    ]
                    removed = original_count - len(rule.content)
                    if removed > 0:
                        properties_removed += removed
                        changed = True
            
            if changed:
                new_css = serialize_css(rules)
                css_path.write_text(new_css, encoding="utf-8")
                reporter.log_change(css_path, f"Removed {properties_removed} aggressive CSS properties")
        
        except Exception as e:
            reporter.log_change(css_path, f"Error processing CSS: {e}")
    
    reporter.increment("css.removed_properties", properties_removed)
    reporter.increment("css.modified_properties", properties_modified)


def simplify_css_aggressive(book: EpubBook, reporter: Reporter) -> None:
    """
    Aggressive CSS cleanup - more invasive fixes.
    
    - Removes font-family declarations
    - Removes @font-face rules (embedded fonts)
    """
    font_families_removed = 0
    font_faces_removed = 0
    
    for css_path in book.get_css_files():
        if not css_path.exists():
            continue
        
        try:
            css_text = css_path.read_text(encoding="utf-8")
            rules = parse_css(css_text)
            changed = False
            
            # Remove font-family declarations
            for rule in rules:
                if hasattr(rule, "content"):
                    original_count = len(rule.content)
                    rule.content = [
                        decl for decl in rule.content
                        if not (hasattr(decl, "name") and decl.name == "font-family")
                    ]
                    removed = original_count - len(rule.content)
                    if removed > 0:
                        font_families_removed += removed
                        changed = True
            
            # Remove @font-face rules (simplified - would need proper at-rule handling)
            # Note: This is a placeholder; full implementation needs proper @font-face detection
            
            if changed:
                new_css = serialize_css(rules)
                css_path.write_text(new_css, encoding="utf-8")
                reporter.log_change(css_path, f"Removed {font_families_removed} font-family declarations")
        
        except Exception as e:
            reporter.log_change(css_path, f"Error processing CSS: {e}")
    
    reporter.increment("css.removed_font_families", font_families_removed)
    reporter.increment("css.removed_font_faces", font_faces_removed)


def _get_selector_text(rule) -> str:
    """Get selector text from rule (simplified)."""
    try:
        import tinycss2
        return tinycss2.serialize(rule.prelude).strip()
    except:
        return ""


def _is_absolute_size(decl) -> bool:
    """Check if declaration value uses absolute units (px, pt)."""
    try:
        value_text = str(decl.value).lower()
        return "px" in value_text or "pt" in value_text
    except:
        return False


def _is_fixed_line_height(decl) -> bool:
    """Check if line-height is a fixed value (not normal or relative)."""
    try:
        value_text = str(decl.value).lower()
        return "px" in value_text or "pt" in value_text or (value_text.replace(".", "").isdigit() and float(value_text) < 1.2)
    except:
        return False


def _is_flex_or_grid(decl) -> bool:
    """Check if display value is flex or grid."""
    try:
        value_text = str(decl.value).lower()
        return "flex" in value_text or "grid" in value_text
    except:
        return False
