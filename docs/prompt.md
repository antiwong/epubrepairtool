Use this as a **single prompt** in Cursor (you can trim or tweak names). It is written assuming:

- Core engine in **Python** (CLI + library)  
- Focus on **reflowable EPUB** formatting repair (XHTML + CSS normalization)  
- Future‑friendly for adding a macOS GUI later

***

**Prompt for Cursor (EPUB formatting repair app)**

You are a senior engineer building a robust EPUB “formatting repair” engine and CLI tool in Python.  
The goal: take badly formatted **reflowable** EPUB files (messy XHTML + CSS) and output **clean, semantically structured, reader‑friendly** EPUBs, without changing the actual textual content.

### High‑level goals

- Input: one or more `.epub` files (reflowable only).  
- Process:  
  - Unpack EPUB → analyze internal XHTML + CSS → apply formatting repair rules → re‑pack as a valid EPUB.  
- Output:  
  - A repaired `.epub` file.  
  - A JSON or text report of what was fixed (e.g., “converted 132 fake headings to `<h2>`/`<h3>`, normalized 78 lists, simplified CSS in 3 files”).  
- Scope:  
  - Focus on **formatting** and **semantic structure** (XHTML + CSS), not content or cover design.  
  - Keep the layout **simple, reflowable, and compatible** with mainstream EPUB readers. [designrr](https://designrr.io/ebook-best-practices/)

### Project structure and tech stack

Create a Python project with this structure:

- `epub_repair/`
  - `__init__.py`
  - `cli.py` – command‑line entry point.
  - `epub_io.py` – EPUB open/inspect/write utilities (ZIP + basic structure).
  - `models.py` – lightweight model objects for key EPUB parts.
  - `xhtml_parser.py` – helpers to parse and serialize XHTML.
  - `css_processor.py` – helpers to parse and rewrite CSS.
  - `rules/`
    - `__init__.py`
    - `headings.py`
    - `paragraphs.py`
    - `lists.py`
    - `breaks.py`
    - `images.py`
    - `css_cleanup.py`
  - `reporting.py` – collects and outputs repair logs.
- `tests/` – unit tests for each rule file and for end‑to‑end flow.
- `pyproject.toml` / `setup.cfg` or `setup.py` – so this can be installed as a package.

Use Python 3.11+, standard libs, and well‑known parsing libraries (e.g., `lxml` or `beautifulsoup4` for XHTML, `tinycss2` or similar for CSS).

### EPUB understanding (for the tool)

Assume EPUB is a ZIP with:

- `mimetype` file containing `application/epub+zip`.  
- `META-INF/container.xml` referencing a single root OPF file.  
- One OPF package that describes manifest and spine (reading order). [barkerbooks](https://barkerbooks.com/how-to-create-epub-file/)

You **do not** need to implement full spec validation; assume the container is structurally sane or already pre‑validated by another tool. Focus on **content documents** (XHTML) and **stylesheets**.

### CLI requirements

Implement a CLI entry point `epub-format-fix` with arguments:

- `epub-format-fix INPUT.epub -o OUTPUT.epub [options]`

Options:

- `--safe` (default):  
  - Only apply “safe” normalization: headings, paragraphs/indents, lists, basic CSS simplification.  
- `--aggressive`:  
  - Additionally remove or down‑scope more invasive CSS (font‑family forcing, extreme margins, etc.).  
- `--report REPORT.json` or `--report REPORT.txt`:  
  - Emit a machine‑readable JSON report or a human‑readable text report.  

The CLI should:

1. Extract EPUB into a temp directory.  
2. Locate OPF and derive the **spine** (ordered list of content documents).  
3. Identify all XHTML files in the reading order, and all referenced CSS files.  
4. Apply rule pipeline.  
5. Write back updated XHTML/CSS, re‑zip to new EPUB, preserve original files aside from the modifications.  
6. Produce a summary report.

### Internal data model

Create simple classes in `models.py`:

- `EpubBook`  
  - `root_path` (filesystem path to extracted EPUB root).  
  - `opf_path` (path to OPF).  
  - `spine_items` (ordered list of `SpineItem`).  
  - `manifest_items` mapping IDs to `ManifestItem`.  

- `SpineItem`  
  - `idref`  
  - `href` (resolved to a content document path).  

- `ManifestItem`  
  - `id`  
  - `href`  
  - `media_type`  

You don’t need full metadata; only what’s needed to traverse and repair content.

### XHTML parsing and serialization

In `xhtml_parser.py`:

- Provide functions to:
  - Load an XHTML file into a DOM/tree.  
  - Return the root node and helpers to query elements (`find_headings`, `find_paragraphs`, etc.).  
  - Serialize back to **well‑formed** XHTML (indenting is nice but not mandatory).

Use a parser that can tolerate messy HTML and output valid XHTML (e.g., `lxml.html` with appropriate options).

### CSS parsing and serialization

In `css_processor.py`:

- Provide a thin wrapper around `tinycss2` or similar to:
  - Parse CSS into a ruleset representation (selectors + declarations).  
  - Allow walking and modifying rules (remove a property, change values, etc.).  
  - Serialize back to clean CSS text.

### Rule engine design

Create a **rule‑based pipeline** in `rules/__init__.py` with something like:

```python
from . import headings, paragraphs, lists, breaks, images, css_cleanup

SAFE_RULES = [
    headings.normalize_headings,
    paragraphs.normalize_paragraphs_and_indents,
    lists.normalize_lists,
    breaks.normalize_context_breaks,
    images.normalize_images,
    css_cleanup.simplify_css_safe,
]

AGGRESSIVE_RULES = SAFE_RULES + [
    css_cleanup.simplify_css_aggressive,
]
```

Each rule function signature:

```python
def rule(book: EpubBook, reporter: Reporter) -> None:
    ...
```

Where `Reporter` is a utility class that collects actions and statistics.

### Concrete rules to implement

Implement **at least** these rules initially:

#### 1. Headings normalization (`rules/headings.py`)

Goal: enforce a logical heading hierarchy and avoid “fake headings”.

- Detect “fake headings” such as `<p class="heading1">` or `<p class="chapter">` that visually look like headings.  
- Convert them to real headings (`<h1>`–`<h3>`) based on context and classes. Use book‑level rules like:  
  - Book title is `h1` (if present on title page).  
  - Chapter titles become `h2`.  
  - Subsections become `h3`.  
- Ensure heading elements are not nested inside paragraphs or inline elements; fix nesting as needed. [accessiblepublishing](https://www.accessiblepublishing.ca/common-epub-issues/)

Log changes like: “Converted 45 fake chapter headings to `<h2>`”.

#### 2. Paragraphs and indents (`rules/paragraphs.py`)

Goal: normalize paragraph structure and basic spacing.

- Ensure body text is in `<p>` elements, not `<div>` with random classes.  
- Remove multiple consecutive `<br/>` used to simulate paragraph breaks; use proper `<p>` separation instead. [accessiblepublishing](https://www.accessiblepublishing.ca/common-epub-issues/)
- For first‑line indents:
  - Prefer CSS (`text-indent`) applied via classes or global rules over inline styles.  
  - Optionally standardize on a small `text-indent` for first paragraphs after headings (or no indent after headings). [ross-harrison](https://ross-harrison.com/2024/09/21/epub-formatting-guide/)

#### 3. Lists normalization (`rules/lists.py`)

Goal: convert visual lists to semantic lists.

- Detect paragraphs that look like lists:  
  - Start with `- `, `• `, `* `, or “1. ” etc.  
- Group consecutive list‑like paragraphs into `<ul>`/`<ol>` with `<li>` items.  
- Remove the manual bullet characters from the text; use CSS `list-style` instead. [accessiblepublishing](https://www.accessiblepublishing.ca/working-with-indesign/)

#### 4. Context breaks and spacing (`rules/breaks.py`)

Goal: normalize scene/section breaks.

- Detect runs of empty paragraphs or repeated `<br/>` used as scene breaks and replace with:  
  - A single `<hr class="scene-break"/>` plus a CSS style (e.g., centered small ornament or small spacing). [accessiblepublishing](https://www.accessiblepublishing.ca/common-epub-issues/)
- Eliminate redundant whitespace that causes big ugly gaps.

#### 5. Images (`rules/images.py`)

Goal: basic semantic cleanup for images.

- Ensure `<img>` tags have at least `alt=""` so validators don’t complain and assistive tech has something defined. [accessiblepublishing](https://www.accessiblepublishing.ca/wp-content/uploads/2019/08/AP-NNELS_Accessible_Publishing_Best_Practices_August_2019.pdf)
- Normalize width/height attributes:
  - Prefer relative sizing (e.g., `max-width: 100%`) in CSS rather than absolute pixel widths where practical.  

#### 6. CSS cleanup (`rules/css_cleanup.py`)

Two modes: `simplify_css_safe` and `simplify_css_aggressive`.

- Common tasks:  
  - Remove or down‑scope rules that override reader settings too aggressively, e.g.:  
    - Hard `font-size` on `body` or `html` that prevents user resizing.  
    - Fixed `line-height` that harms readability.  
    - Excessive margins/padding that break reflow. [idpf](https://idpf.org/forum/topic-3217)
  - Replace modern layout features that break older readers:
    - Avoid or strip CSS `display: flex`, `grid`, etc. in content flows; fall back to block layout. [github](https://github.com/jgm/pandoc/issues/8379)
  - Normalize headings CSS:
    - Ensure `h1`–`h3` have clear, consistent margins above/below.  
    - Use relative units (`em`, `rem`) rather than absolute points where possible. [w3](https://www.w3.org/TR/epub-fxl-a11y/)

Aggressive mode can:

- Remove embedded web fonts that bloat the file if they are not essential.  
- Remove most `font-family` declarations to let the reading system choose fonts.  

### Reporter and report output

In `reporting.py`:

- Implement a `Reporter` class that rules call like:

```python
reporter.increment("headings.converted_fake_headings", count)
reporter.log_change(file, description)
```

- At the end of processing:
  - Produce a summary dict with counts per rule and list of notable changes.  
  - If `--report` is given:
    - Write JSON if filename ends with `.json`.  
    - Write a simple text summary otherwise.

### Tests

Add tests that:

- Feed in minimal synthetic EPUBs with:
  - Fake headings, fake lists, multiple `<br/>` breaks, over‑styled CSS.  
- Run the rule pipeline in `--safe` mode and assert:
  - DOM structure is transformed as expected (headings, lists, etc.).  
  - CSS is simplified but still present.  

Add an end‑to‑end test that:

- Takes a sample messy EPUB directory structure (you can simulate extracted EPUB in tests).  
- Runs the full pipeline and validates that:
  - XHTML parses cleanly afterwards.  
  - The report contains expected counters.

### Coding style and documentation

- Use type hints throughout.  
- Keep functions short and composable; no god functions.  
- Add docstrings that explain the intent of each rule in plain English.  
- Include a top‑level `README.md` describing:
  - What the tool does and does **not** do.  
  - The safe vs aggressive modes.  
  - Example CLI invocations.  
  - A brief note that this is tuned for **reflowable EPUB** formatting and semantic cleanup, not fixed layout or DRM‑locked files. [kitaboo](https://kitaboo.com/reflowable-or-fixed-layout-epub-which-is-better/)

***

Use this entire prompt as the **system or main instruction** in Cursor for generating the initial codebase.  
If the first pass is too large, ask Cursor to scaffold the project with empty modules and then iteratively implement each `rules/*.py` module and the CLI.