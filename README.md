# EPUB Tools - Repair & Upgrade

A comprehensive Python toolkit for EPUB files, providing both formatting repair and version upgrade capabilities. Focuses on semantic structure (XHTML) and styling (CSS) normalization, plus EPUB 2 → EPUB 3 conversion.

## Features

### EPUB Format Repair
- **Graphical User Interface**: Simple, user-friendly GUI for easy EPUB repair
- **Command-Line Interface**: Full-featured CLI for automation and scripting
- **Semantic Structure Repair**: Converts fake headings to proper `<h1>`-`<h3>` elements
- **Paragraph Normalization**: Fixes paragraph structure and removes excessive `<br/>` tags
- **List Conversion**: Converts visual lists to semantic `<ul>`/`<ol>` structures
- **Scene Break Normalization**: Replaces multiple breaks with semantic `<hr>` elements
- **Page Break Management**: Removes unwanted page breaks, keeps only chapter breaks
- **Image Accessibility**: Ensures images have alt attributes
- **CSS Cleanup**: Removes aggressive CSS that interferes with reader settings

### EPUB Version Upgrade
- **Version Detection**: Automatically detects EPUB 2.0, 2.0.1, 3.0, 3.2, etc.
- **EPUB 2 → EPUB 3 Conversion**: Upgrades EPUB 2 files to clean EPUB 3
- **NCX to nav.xhtml**: Converts legacy NCX navigation to EPUB 3 nav.xhtml
- **Metadata Validation**: Ensures required metadata fields are present
- **Dry Run Mode**: Preview what would be changed without modifying files

## Quick Start

**New to EPUB Repair?** Check out the [Quick Start Guide](docs/QUICKSTART.md) for step-by-step instructions!

**Quick command:**
```bash
epub-format-fix input.epub -o output.epub
```

## Installation

```bash
pip install -e .
```

Or with development dependencies:

```bash
pip install -e ".[dev]"
```

## Requirements

- Python 3.11+
- lxml (for XHTML parsing)
- tinycss2 (for CSS parsing)

## Usage

### Graphical User Interface (GUI)

Launch the GUI application:

**Option 1: Using the launch script (recommended)**
```bash
./start_gui.sh        # macOS/Linux
start_gui.bat         # Windows
python start_gui.py   # Any platform
```

**Option 2: Direct command**
```bash
epub-repair-gui
```

**Option 3: Python module**
```bash
python -m epub_repair.gui
```

The GUI provides:
- **Tabbed Interface**: Separate tabs for Format Repair and Version Upgrade
- File browser for selecting input and output EPUB files
- Mode selection (Safe or Aggressive) for repair
- Upgrade options (target version, force rewrite, dry run)
- Optional report generation for both tools
- Real-time progress and results display

### Command-Line Interface

#### Basic Usage

```bash
epub-format-fix input.epub -o output.epub
```

#### Safe Mode (Default)

Applies conservative formatting fixes:

```bash
epub-format-fix input.epub -o output.epub --safe
```

#### Aggressive Mode

Applies more invasive CSS cleanup:

```bash
epub-format-fix input.epub -o output.epub --aggressive
```

#### Generate Report

Generate a JSON or text report of changes:

```bash
epub-format-fix input.epub -o output.epub --report report.json
epub-format-fix input.epub -o output.epub --report report.txt
```

### EPUB Version Upgrade

#### Basic Upgrade

Upgrade an EPUB 2 file to EPUB 3:

```bash
epub-upgrade input.epub -o output.epub
```

#### Check Version (Dry Run)

Check the version without modifying the file:

```bash
epub-upgrade input.epub -o output.epub --dry-run
```

#### Generate Upgrade Report

Create a JSON report of the upgrade process:

```bash
epub-upgrade input.epub -o output.epub --report upgrade_report.json
```

#### Force Rewrite EPUB 3

Normalize an existing EPUB 3 file:

```bash
epub-upgrade input.epub -o output.epub --force-rewrite
```

#### Target Version

Specify a target version (default is 3.0):

```bash
epub-upgrade input.epub -o output.epub --target-version 3.2
```

## What It Does

### Format Repair

The repair tool fixes common formatting issues in EPUB files:

- **Headings**: Converts `<p class="heading1">` to proper `<h2>` elements
- **Paragraphs**: Converts `<div>` elements to `<p>` where appropriate
- **Lists**: Groups list-like paragraphs into semantic `<ul>`/`<ol>` structures
- **Breaks**: Normalizes scene breaks using `<hr>` elements
- **Page Breaks**: Removes unwanted page breaks, keeps only chapter breaks
- **Images**: Adds missing alt attributes for accessibility
- **CSS**: Removes aggressive font sizing, fixed line-heights, and modern layout features that break older readers

### Version Upgrade

The upgrade tool converts EPUB 2 to EPUB 3:

- **Version Detection**: Identifies EPUB version from OPF package element
- **Package Update**: Updates `<package version="2.0">` to `version="3.0"`
- **Navigation Conversion**: Converts NCX (`toc.ncx`) to EPUB 3 `nav.xhtml`
- **Metadata Validation**: Ensures required metadata fields (title, identifier, language)
- **Content Compliance**: Ensures XHTML files have proper `lang` attributes

## What It Does NOT Do

- Does not modify textual content
- Does not handle fixed-layout EPUBs (reflowable only)
- Does not remove DRM or modify protected content
- Does not validate EPUB structure (assumes valid input)
- Does not modify cover images or metadata

## Project Structure

```
epub-repair/
├── src/
│   ├── epub_repair/            # Format repair tool
│   │   ├── __init__.py
│   │   ├── cli.py              # Command-line interface
│   │   ├── gui.py              # Graphical user interface
│   │   ├── epub_io.py           # EPUB extraction and repackaging
│   │   ├── models.py            # Data models
│   │   ├── xhtml_parser.py      # XHTML parsing utilities
│   │   ├── css_processor.py     # CSS parsing utilities
│   │   ├── reporting.py         # Report generation
│   │   └── rules/               # Formatting repair rules
│   │       ├── __init__.py
│   │       ├── headings.py
│   │       ├── paragraphs.py
│   │       ├── lists.py
│   │       ├── breaks.py
│   │       ├── images.py
│   │       └── css_cleanup.py
│   └── epub_upgrade/            # Version upgrade tool
│       ├── __init__.py
│       ├── cli.py              # Command-line interface
│       ├── epub_io.py           # EPUB I/O utilities
│       ├── versioning.py        # Version detection
│       ├── nav_conversion.py    # NCX to nav.xhtml conversion
│       ├── upgrade.py           # Upgrade orchestration
│       └── reporting.py         # Report generation
├── tests/                       # Unit and integration tests
├── docs/                        # Documentation
├── pyproject.toml              # Project configuration
├── start_gui.sh                # GUI launch script (macOS/Linux)
├── start_gui.bat               # GUI launch script (Windows)
├── start_gui.py                # GUI launch script (cross-platform)
└── README.md
```

## Workflow: Upgrade + Repair

For best results, use both tools in sequence:

```bash
# Step 1: Upgrade EPUB 2 → EPUB 3
epub-upgrade old_book.epub -o upgraded.epub

# Step 2: Repair formatting
epub-format-fix upgraded.epub -o final.epub
```

Or use the GUI which provides both tools in a single interface!

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
black src/ tests/
```

### Type Checking

```bash
mypy src/
```

## License

MIT
