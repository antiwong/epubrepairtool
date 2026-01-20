# EPUB Tools Design Document

## Overview

This document provides detailed design specifications for both the EPUB Repair and EPUB Upgrade tools, including API designs, data structures, algorithms, error handling strategies, and implementation details.

## Table of Contents

1. [Module APIs](#module-apis)
2. [Data Structures](#data-structures)
3. [Rule Implementation Details](#rule-implementation-details)
4. [EPUB Upgrade Design](#epub-upgrade-design)
5. [Error Handling](#error-handling)
6. [Edge Cases](#edge-cases)
7. [Performance Considerations](#performance-considerations)
8. [Testing Strategy](#testing-strategy)

## Module APIs

### CLI Module (`cli.py`)

#### Function Signatures

```python
def main() -> int:
    """
    Entry point for CLI application.
    
    Returns:
        Exit code (0 for success, non-zero for errors)
    """

def parse_args(args: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Optional argument list (defaults to sys.argv[1:])
    
    Returns:
        Parsed arguments namespace with:
        - input: Path to input EPUB
        - output: Path to output EPUB
        - mode: 'safe' or 'aggressive'
        - report: Optional path to report file
    """

def run_repair(
    input_path: Path,
    output_path: Path,
    mode: str = "safe",
    report_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Execute the EPUB repair pipeline.
    
    Args:
        input_path: Path to input EPUB file
        output_path: Path to output EPUB file
        mode: 'safe' or 'aggressive'
        report_path: Optional path for report output
    
    Returns:
        Summary dictionary with repair statistics
    
    Raises:
        FileNotFoundError: If input file doesn't exist
        ValueError: If EPUB structure is invalid
        IOError: If file operations fail
    """
```

#### Argument Parsing

- Positional: `INPUT.epub` (required)
- Options:
  - `-o, --output OUTPUT.epub` (required)
  - `--safe` (default mode, mutually exclusive with `--aggressive`)
  - `--aggressive` (mutually exclusive with `--safe`)
  - `--report REPORT.json` or `--report REPORT.txt` (optional)

### EPUB IO Module (`epub_io.py`)

#### Function Signatures

```python
def extract_epub(epub_path: Path, temp_dir: Path) -> Path:
    """
    Extract EPUB ZIP to temporary directory.
    
    Args:
        epub_path: Path to EPUB file
        temp_dir: Temporary directory for extraction
    
    Returns:
        Path to extracted root directory
    
    Raises:
        zipfile.BadZipFile: If file is not a valid ZIP
        IOError: If extraction fails
    """

def parse_container(container_path: Path) -> Path:
    """
    Parse META-INF/container.xml to find OPF path.
    
    Args:
        container_path: Path to container.xml
    
    Returns:
        Path to OPF file (relative to EPUB root)
    
    Raises:
        XMLSyntaxError: If container.xml is malformed
        ValueError: If OPF reference not found
    """

def parse_opf(opf_path: Path, root_path: Path) -> Tuple[List[SpineItem], Dict[str, ManifestItem]]:
    """
    Parse OPF file to extract spine and manifest.
    
    Args:
        opf_path: Path to OPF file
        root_path: EPUB root directory for resolving relative paths
    
    Returns:
        Tuple of (spine_items, manifest_items)
    
    Raises:
        XMLSyntaxError: If OPF is malformed
        ValueError: If required elements missing
    """

def repackage_epub(temp_dir: Path, output_path: Path) -> None:
    """
    Create EPUB ZIP from temporary directory.
    
    Args:
        temp_dir: Temporary directory with EPUB contents
        output_path: Path to output EPUB file
    
    Raises:
        IOError: If ZIP creation fails
    
    Notes:
        - mimetype must be first entry (uncompressed)
        - Preserve directory structure
        - Use ZIP_DEFLATED compression (except mimetype)
    """
```

### Data Models (`models.py`)

#### Class Definitions

```python
@dataclass
class SpineItem:
    """Represents a spine item (reading order entry)."""
    idref: str
    href: Path  # Resolved absolute path
    
    def __post_init__(self):
        if not self.idref:
            raise ValueError("idref cannot be empty")

@dataclass
class ManifestItem:
    """Represents a manifest item (resource in EPUB)."""
    id: str
    href: Path  # Relative path from EPUB root
    media_type: str
    
    def __post_init__(self):
        if not self.id:
            raise ValueError("id cannot be empty")
        if not self.media_type:
            raise ValueError("media_type cannot be empty")

@dataclass
class EpubBook:
    """Represents an EPUB book structure."""
    root_path: Path
    opf_path: Path
    spine_items: List[SpineItem]
    manifest_items: Dict[str, ManifestItem]
    
    def get_xhtml_files(self) -> List[Path]:
        """
        Get all XHTML content files in spine order.
        
        Returns:
            List of absolute paths to XHTML files
        """
    
    def get_css_files(self) -> List[Path]:
        """
        Get all CSS files referenced in manifest.
        
        Returns:
            List of absolute paths to CSS files
        """
    
    def resolve_path(self, href: str) -> Path:
        """
        Resolve relative href to absolute path.
        
        Args:
            href: Relative path from OPF location
        
        Returns:
            Absolute path resolved from root_path
        """
```

### XHTML Parser (`xhtml_parser.py`)

#### Function Signatures

```python
def parse_xhtml(file_path: Path) -> etree._Element:
    """
    Parse XHTML file into lxml Element tree.
    
    Args:
        file_path: Path to XHTML file
    
    Returns:
        Root element of parsed tree
    
    Raises:
        XMLSyntaxError: If XHTML is malformed
        IOError: If file cannot be read
    
    Notes:
        - Uses lxml.html.HTMLParser with recover=True for tolerance
        - Ensures XML namespace handling
    """

def find_headings(tree: etree._Element) -> List[etree._Element]:
    """
    Find all heading elements (h1-h6) in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of heading elements in document order
    """

def find_paragraphs(tree: etree._Element) -> List[etree._Element]:
    """
    Find all paragraph elements in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of paragraph elements in document order
    """

def find_lists(tree: etree._Element) -> List[etree._Element]:
    """
    Find all list elements (ul, ol) in tree.
    
    Args:
        tree: Root element
    
    Returns:
        List of list elements in document order
"""

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
```

### CSS Processor (`css_processor.py`)

#### Function Signatures

```python
def parse_css(css_text: str) -> List[Rule]:
    """
    Parse CSS text into ruleset representation.
    
    Args:
        css_text: CSS source text
    
    Returns:
        List of Rule objects (from tinycss2)
    
    Raises:
        CSSParseError: If CSS is malformed (non-fatal, log and continue)
    """

def find_rules_by_selector(rules: List[Rule], selector: str) -> List[Rule]:
    """
    Find rules matching a selector pattern.
    
    Args:
        rules: List of parsed rules
        selector: CSS selector pattern (supports wildcards)
    
    Returns:
        List of matching rules
    """

def remove_property(rules: List[Rule], selector: str, property_name: str) -> int:
    """
    Remove CSS property from matching rules.
    
    Args:
        rules: List of parsed rules
        selector: Selector pattern to match
        property_name: Property to remove
    
    Returns:
        Number of properties removed
    """

def modify_property(
    rules: List[Rule],
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

def serialize_css(rules: List[Rule]) -> str:
    """
    Serialize rules back to CSS text.
    
    Args:
        rules: List of parsed rules
    
    Returns:
        CSS string (formatted, one rule per line)
    """
```

### Reporter (`reporting.py`)

#### Class Definition

```python
class Reporter:
    """Collects and reports repair statistics."""
    
    def __init__(self):
        self.counters: Dict[str, int] = {}
        self.changes: List[Dict[str, Any]] = []
    
    def increment(self, category: str, count: int = 1) -> None:
        """
        Increment counter for a category.
        
        Args:
            category: Category name (e.g., "headings.converted_fake_headings")
            count: Amount to increment (default 1)
        """
    
    def log_change(
        self,
        file_path: Path,
        description: str,
        details: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Log a specific change.
        
        Args:
            file_path: File where change occurred
            description: Human-readable description
            details: Optional additional metadata
        """
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all statistics and changes.
        
        Returns:
            Dictionary with:
            - counters: Dict of category -> count
            - changes: List of change records
            - total_files_modified: Count of unique files
        """
    
    def write_json(self, path: Path) -> None:
        """
        Write report as JSON.
        
        Args:
            path: Output file path
        """
    
    def write_text(self, path: Path) -> None:
        """
        Write report as human-readable text.
        
        Args:
            path: Output file path
        
        Format:
            EPUB Repair Report
            =================
            
            Summary:
            - Converted 45 fake headings to <h2>
            - Normalized 23 lists
            ...
            
            Changes by file:
            - chapter1.xhtml: Converted 3 headings, normalized 2 lists
            ...
        """
```

## Data Structures

### EPUB Structure Representation

```python
# In-memory representation
EpubBook {
    root_path: Path
    opf_path: Path
    spine_items: [
        SpineItem { idref: "ch1", href: Path("/tmp/epub/OEBPS/chapter1.xhtml") },
        SpineItem { idref: "ch2", href: Path("/tmp/epub/OEBPS/chapter2.xhtml") },
        ...
    ]
    manifest_items: {
        "ch1": ManifestItem { id: "ch1", href: Path("OEBPS/chapter1.xhtml"), media_type: "application/xhtml+xml" },
        "style1": ManifestItem { id: "style1", href: Path("OEBPS/style.css"), media_type: "text/css" },
        ...
    }
}
```

### Report Data Structure

```python
{
    "counters": {
        "headings.converted_fake_headings": 45,
        "headings.fixed_nesting": 3,
        "paragraphs.converted_divs": 12,
        "paragraphs.removed_br_breaks": 8,
        "lists.converted_paragraphs": 23,
        "breaks.normalized_scene_breaks": 5,
        "images.added_alt": 7,
        "css.removed_properties": 34,
        "css.modified_properties": 12
    },
    "changes": [
        {
            "file": "OEBPS/chapter1.xhtml",
            "description": "Converted 3 fake headings to <h2>",
            "rule": "headings",
            "details": {
                "elements": ["p.chapter-title", "p.section-title", "p.chapter-title"]
            }
        },
        ...
    ],
    "total_files_modified": 8,
    "mode": "safe"
}
```

## Rule Implementation Details

### Rule Function Pattern

All rules follow this pattern:

```python
def normalize_rule_name(book: EpubBook, reporter: Reporter) -> None:
    """
    Rule description.
    
    Algorithm:
    1. Iterate through XHTML files in spine order
    2. Parse each file
    3. Apply transformations
    4. Log changes via reporter
    5. (Optional) Modify CSS rulesets
    """
    for xhtml_path in book.get_xhtml_files():
        tree = parse_xhtml(xhtml_path)
        # Apply transformations
        changes = apply_transformations(tree)
        # Log changes
        for change in changes:
            reporter.log_change(xhtml_path, change.description)
            reporter.increment(change.category)
        # Write back (or defer to serialization phase)
```

### Headings Normalization (`rules/headings.py`)

#### Algorithm

1. **Detect Fake Headings**
   - Find `<p>` elements with classes like: `heading1`, `heading2`, `chapter`, `section`, `title`
   - Check for visual indicators: large font-size, bold, centered text
   - Identify patterns: first element in body, after `<hr>`, etc.

2. **Determine Heading Level**
   - Book title (first page, title-like class) → `<h1>`
   - Chapter titles (class="chapter", "chapter-title") → `<h2>`
   - Section titles (class="section", "subsection") → `<h3>`
   - Use context: if previous heading was h2, next similar is likely h3

3. **Convert and Fix Nesting**
   - Replace `<p class="heading1">` with `<h2>`
   - Move heading out of parent paragraph if nested
   - Preserve text content and attributes (except heading-related classes)

4. **Logging**
   - Count conversions by level
   - Log nesting fixes separately

#### Implementation Notes

- Use XPath or CSS selectors: `//p[contains(@class, 'heading')]`
- Preserve non-heading classes for styling
- Handle edge case: heading inside list item (move out)

### Paragraphs Normalization (`rules/paragraphs.py`)

#### Algorithm

1. **Convert Divs to Paragraphs**
   - Find `<div>` elements with body-text-like classes
   - Convert to `<p>` if they contain inline or text content
   - Preserve classes that are styling-related

2. **Remove Multiple `<br/>` Tags**
   - Find sequences of 2+ consecutive `<br/>` tags
   - Replace with proper paragraph separation
   - Handle edge case: `<br/>` at end of paragraph (remove)

3. **Normalize Indentation**
   - Detect inline `style="text-indent: ..."` on paragraphs
   - Move to CSS class or global rule
   - Standardize: no indent after headings, small indent (0.5em) for body paragraphs

#### Implementation Notes

- Be conservative: only convert divs that clearly contain paragraph content
- Preserve divs used for layout (containing multiple paragraphs)
- Use regex or tree traversal for `<br/>` detection

### Lists Normalization (`rules/lists.py`)

#### Algorithm

1. **Detect List-Like Paragraphs**
   - Find paragraphs starting with: `- `, `• `, `* `, `1. `, `2. `, etc.
   - Check for consecutive paragraphs with same pattern
   - Identify ordered vs unordered by prefix pattern

2. **Group into Lists**
   - Group consecutive list-like paragraphs
   - Create `<ul>` or `<ol>` wrapper
   - Convert each paragraph to `<li>`
   - Remove bullet/number prefix from text content

3. **Handle Nested Lists**
   - Detect indentation patterns (CSS or whitespace)
   - Create nested `<ul>`/`<ol>` structure

#### Implementation Notes

- Use regex: `^[-•*]\s+` or `^\d+\.\s+`
- Preserve paragraph classes if they indicate list item styling
- Handle edge case: mixed ordered/unordered in same group (split)

### Context Breaks (`rules/breaks.py`)

#### Algorithm

1. **Detect Scene Breaks**
   - Find sequences of empty paragraphs (2+)
   - Find sequences of `<br/>` tags (3+)
   - Find paragraphs with only decorative characters (★, ◆, etc.)

2. **Normalize to `<hr>`**
   - Replace with single `<hr class="scene-break"/>`
   - Add CSS rule for scene-break styling (centered, small margin)

3. **Remove Redundant Whitespace**
   - Collapse multiple empty paragraphs to one
   - Remove excessive margins/padding from CSS

#### Implementation Notes

- Use text content analysis: `len(element.text.strip()) == 0`
- Detect decorative characters: `re.match(r'^[★◆●▪▫·\s]+$', text)`
- CSS rule: `.scene-break { margin: 1em 0; text-align: center; }`

### Images Normalization (`rules/images.py`)

#### Algorithm

1. **Add Missing Alt Attributes**
   - Find `<img>` tags without `alt` attribute
   - Add `alt=""` (empty string acceptable for decorative images)
   - Optionally extract from filename or context

2. **Normalize Sizing**
   - Remove fixed `width`/`height` attributes
   - Add CSS rule: `img { max-width: 100%; height: auto; }`
   - Preserve aspect ratio

#### Implementation Notes

- Empty alt is valid for decorative images
- Use CSS for responsive sizing
- Handle edge case: images with explicit dimensions needed for layout

### CSS Cleanup (`rules/css_cleanup.py`)

#### Safe Mode

1. **Remove Aggressive Font Sizing**
   - Find `font-size` on `body` or `html` with absolute units (px, pt)
   - Remove or convert to relative units (em, rem)
   - Preserve relative sizes

2. **Normalize Line Height**
   - Remove fixed `line-height` values that are too restrictive
   - Allow reader to control line spacing

3. **Fix Layout Properties**
   - Remove `display: flex`, `display: grid` from content flows
   - Replace with `display: block`
   - Preserve flex/grid in non-content contexts if safe

4. **Normalize Heading Margins**
   - Ensure `h1`-`h3` have consistent margins
   - Use relative units (em) instead of absolute

#### Aggressive Mode

Additional actions:
1. **Remove Font Families**
   - Remove `font-family` declarations (except for special cases)
   - Let reading system choose fonts

2. **Remove Embedded Fonts**
   - Identify `@font-face` rules
   - Remove if not essential (keep icon fonts, etc.)
   - Update manifest to remove font files

#### Implementation Notes

- Use CSS parser to walk rulesets
- Be selective: only modify rules that affect content flow
- Preserve accessibility-related styles

## Error Handling

### Error Categories

1. **Input Errors**
   - Invalid EPUB file (not a ZIP)
   - Missing required files (container.xml, OPF)
   - Malformed XML (container, OPF, XHTML)
   - File not found

2. **Processing Errors**
   - CSS parse errors (non-fatal, log and continue)
   - XHTML parse errors (attempt recovery)
   - Rule application failures (log and continue)

3. **Output Errors**
   - Cannot write output file
   - ZIP creation failures
   - Report file write failures

### Error Handling Strategy

```python
# Error handling pattern
try:
    book = extract_and_parse_epub(input_path)
except zipfile.BadZipFile:
    print("Error: Input file is not a valid EPUB (ZIP) file", file=sys.stderr)
    return 1
except FileNotFoundError as e:
    print(f"Error: File not found: {e}", file=sys.stderr)
    return 1
except XMLSyntaxError as e:
    print(f"Error: Malformed XML: {e}", file=sys.stderr)
    return 1

# Non-fatal errors (log and continue)
for css_file in book.get_css_files():
    try:
        rules = parse_css(css_file.read_text())
    except CSSParseError as e:
        reporter.log_change(css_file, f"CSS parse warning: {e}")
        continue  # Skip this file
```

### Error Recovery

- **Malformed XHTML**: Use parser recovery mode, log warnings
- **Malformed CSS**: Skip problematic rules, log warnings
- **Missing Files**: Log warning, continue with available files
- **Rule Failures**: Catch exceptions, log error, continue with next rule

## Edge Cases

### EPUB Structure Edge Cases

1. **Multiple OPF Files**
   - Current design assumes single OPF (per EPUB 2/3 spec)
   - If multiple found, use first one and log warning

2. **Circular References**
   - Spine items referencing non-existent manifest entries
   - Handle gracefully: skip missing items, log warning

3. **Relative Path Resolution**
   - OPF in subdirectory, hrefs relative to OPF location
   - Use `pathlib` for proper resolution

4. **Non-Standard Media Types**
   - XHTML files with wrong media type
   - Detect by extension or content, log warning

### Content Edge Cases

1. **Empty Documents**
   - XHTML files with no body content
   - Preserve structure, skip content rules

2. **Mixed Content**
   - Paragraphs containing both text and block elements
   - Handle carefully: may indicate layout structure

3. **Nested Lists in Fake Lists**
   - Paragraph-based lists with indentation indicating nesting
   - Detect and create proper nested structure

4. **Images in Headings**
   - Headings containing images (logos, etc.)
   - Preserve images, ensure alt text

5. **CSS @import Rules**
   - External stylesheet imports
   - Follow imports, process imported files

6. **Inline Styles**
   - Heavy use of inline `style` attributes
   - Optionally extract to CSS classes (future enhancement)

### Performance Edge Cases

1. **Very Large EPUBs**
   - Thousands of XHTML files
   - Process in batches, use streaming where possible

2. **Very Large Files**
   - Single XHTML file with millions of elements
   - Use efficient tree traversal, avoid deep copies

3. **Memory Constraints**
   - Load files on-demand rather than all at once
   - Process and write immediately, don't keep all in memory

## Performance Considerations

### Optimization Strategies

1. **Lazy Loading**
   - Parse XHTML/CSS only when needed by rules
   - Cache parsed trees for multiple rule passes

2. **Batch Processing**
   - Process multiple files in parallel (future enhancement)
   - Use multiprocessing for CPU-bound operations

3. **Efficient Tree Traversal**
   - Use XPath for targeted queries
   - Avoid full tree walks when possible

4. **Memory Management**
   - Write modified files immediately after rule application
   - Don't keep all DOM trees in memory simultaneously

### Performance Targets

- Small EPUB (< 10 files): < 1 second
- Medium EPUB (10-100 files): < 5 seconds
- Large EPUB (100-1000 files): < 30 seconds

## Testing Strategy

### Unit Tests

Each module should have comprehensive unit tests:

```python
# tests/test_headings.py
def test_detect_fake_headings():
    """Test detection of fake heading patterns."""
    
def test_convert_to_semantic_headings():
    """Test conversion of fake headings to h1-h3."""
    
def test_fix_nested_headings():
    """Test moving headings out of paragraphs."""

# tests/test_epub_io.py
def test_extract_epub():
    """Test EPUB extraction."""
    
def test_parse_container():
    """Test container.xml parsing."""
    
def test_parse_opf():
    """Test OPF parsing and path resolution."""
```

### Integration Tests

Test rule pipeline end-to-end:

```python
# tests/test_integration.py
def test_safe_mode_pipeline():
    """Test full pipeline in safe mode."""
    
def test_aggressive_mode_pipeline():
    """Test full pipeline in aggressive mode."""
    
def test_report_generation():
    """Test report generation (JSON and text)."""
```

### Test Data

Create minimal synthetic EPUBs:

```
test_data/
  simple_epub/
    mimetype
    META-INF/
      container.xml
    OEBPS/
      content.opf
      chapter1.xhtml  # Contains fake headings, fake lists
      chapter2.xhtml  # Contains multiple <br/> breaks
      style.css       # Contains aggressive CSS
```

### Test Coverage Goals

- Unit tests: > 90% coverage
- Integration tests: Cover all rule combinations
- Edge case tests: Cover identified edge cases

## Implementation Phases

### Phase 1: Core Infrastructure
1. Project structure and dependencies
2. EPUB IO module (extract, parse, repackage)
3. Data models
4. Basic CLI

### Phase 2: Parsing and Processing
1. XHTML parser
2. CSS processor
3. Reporter

### Phase 3: Rules (Safe Mode)
1. Headings normalization
2. Paragraphs normalization
3. Lists normalization
4. Breaks normalization
5. Images normalization
6. CSS cleanup (safe)

### Phase 4: Aggressive Mode
1. CSS cleanup (aggressive)
2. Additional aggressive rules (if needed)

### Phase 5: Testing and Polish
1. Comprehensive unit tests
2. Integration tests
3. Documentation
4. Error handling improvements
