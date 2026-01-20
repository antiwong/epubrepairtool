"""CSS parsing and manipulation utilities."""

from typing import List, Optional

try:
    import tinycss2
    TINYCSS2_AVAILABLE = True
except ImportError:
    TINYCSS2_AVAILABLE = False


def parse_css(css_text: str) -> List:
    """
    Parse CSS text into ruleset representation.
    
    Args:
        css_text: CSS source text
    
    Returns:
        List of Rule objects (from tinycss2)
    
    Raises:
        ImportError: If tinycss2 is not available
        CSSParseError: If CSS is malformed (non-fatal, log and continue)
    """
    if not TINYCSS2_AVAILABLE:
        raise ImportError(
            "tinycss2 must be installed. Install with: pip install tinycss2"
        )
    
    # tinycss2.parse_stylesheet returns a list of rules directly
    rules = tinycss2.parse_stylesheet(css_text, skip_comments=True, skip_whitespace=True)
    
    return rules


def find_rules_by_selector(rules: List, selector_pattern: str) -> List:
    """
    Find rules matching a selector pattern.
    
    Args:
        rules: List of parsed rules
        selector_pattern: CSS selector pattern (exact match)
    
    Returns:
        List of matching rules
    """
    matching = []
    for rule in rules:
        if hasattr(rule, "prelude"):
            # tinycss2 rules have a prelude (selector) and content (declarations)
            try:
                selector_text = "".join(tinycss2.serialize(rule.prelude)).strip()
            except:
                # Fallback: try to get string representation
                selector_text = str(rule.prelude).strip()
            if selector_text == selector_pattern:
                matching.append(rule)
    return matching


def remove_property(rules: List, selector: str, property_name: str) -> int:
    """
    Remove CSS property from matching rules.
    
    Args:
        rules: List of parsed rules
        selector: Selector pattern to match
        property_name: Property to remove
    
    Returns:
        Number of properties removed
    """
    count = 0
    matching_rules = find_rules_by_selector(rules, selector)
    
    for rule in matching_rules:
        if hasattr(rule, "content"):
            # Filter out declarations with matching property name
            original_count = len(rule.content)
            rule.content = [
                decl for decl in rule.content
                if hasattr(decl, "name") and decl.name != property_name
            ]
            count += original_count - len(rule.content)
    
    return count


def modify_property(
    rules: List,
    selector: str,
    property_name: str,
    new_value: str
) -> int:
    """
    Modify CSS property value in matching rules.
    
    Args:
        rules: List of parsed rules
        selector: Selector pattern to match
        property_name: Property to modify
        new_value: New property value
    
    Returns:
        Number of properties modified
    """
    count = 0
    matching_rules = find_rules_by_selector(rules, selector)
    
    for rule in matching_rules:
        if hasattr(rule, "content"):
            for decl in rule.content:
                if hasattr(decl, "name") and decl.name == property_name:
                    # Create new declaration with new value
                    # Note: This is simplified; full implementation needs proper token handling
                    decl.value = tinycss2.parse_component_value_list(new_value)
                    count += 1
    
    return count


def serialize_css(rules: List) -> str:
    """
    Serialize rules back to CSS text.
    
    Args:
        rules: List of parsed rules
    
    Returns:
        CSS string (formatted, one rule per line)
    """
    if not TINYCSS2_AVAILABLE:
        raise ImportError("tinycss2 must be installed")
    
    lines = []
    for rule in rules:
        try:
            # tinycss2.serialize returns a generator of strings
            rule_text = "".join(tinycss2.serialize(rule))
        except:
            # Fallback: use string representation
            rule_text = str(rule)
        lines.append(rule_text)
    
    return "\n".join(lines)
