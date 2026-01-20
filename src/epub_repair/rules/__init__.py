"""Rule engine for EPUB formatting repair."""

from . import breaks, css_cleanup, headings, images, lists, paragraphs

# Safe rules - conservative formatting fixes
SAFE_RULES = [
    headings.normalize_headings,
    paragraphs.normalize_paragraphs_and_indents,
    lists.normalize_lists,
    breaks.normalize_context_breaks,
    images.normalize_images,
    css_cleanup.simplify_css_safe,
]

# Aggressive rules - includes safe rules plus more invasive fixes
AGGRESSIVE_RULES = SAFE_RULES + [
    css_cleanup.simplify_css_aggressive,
]
