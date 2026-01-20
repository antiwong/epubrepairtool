# EPUB Tools - Quick Start Guide

Get started with EPUB Tools in minutes! This guide covers both the Format Repair and Version Upgrade tools for EPUB files.

## Installation

### Prerequisites
- Python 3.11 or higher
- pip (Python package manager)

### Install the Tool

1. **Clone or download the project:**
   ```bash
   cd epub-repair
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

   This will install all required dependencies (lxml, tinycss2) automatically.

## Quick Start - Command Line

### EPUB Format Repair

### Basic Usage

The simplest way to repair an EPUB:

```bash
epub-format-fix input.epub -o output.epub
```

This will:
- Apply safe formatting fixes
- Create a repaired EPUB file
- Display a summary of changes

### Example

```bash
epub-format-fix my_book.epub -o my_book_fixed.epub
```

**Output:**
```
Repair Summary:
==================================================
  headings.converted_fake_headings: 12
  paragraphs.converted_divs: 5
  lists.converted_paragraphs: 8
  breaks.removed_page_breaks: 3
  images.added_alt: 2

Total files modified: 5
```

### Repair Modes

**Safe Mode (Default):**
Conservative fixes that preserve most styling:
```bash
epub-format-fix input.epub -o output.epub --safe
```

**Aggressive Mode:**
More invasive CSS cleanup (removes font families, embedded fonts):
```bash
epub-format-fix input.epub -o output.epub --aggressive
```

### Generate Reports

Create a detailed report of all changes:

**Text Report:**
```bash
epub-format-fix input.epub -o output.epub --report changes.txt
```

**JSON Report:**
```bash
epub-format-fix input.epub -o output.epub --report changes.json
```

### EPUB Version Upgrade

#### Basic Upgrade

Upgrade an EPUB 2 file to EPUB 3:

```bash
epub-upgrade input.epub -o output.epub
```

This will:
- Detect the EPUB version
- Convert EPUB 2 to EPUB 3 if needed
- Convert NCX navigation to nav.xhtml
- Validate and add missing metadata
- Display a summary of changes

#### Check Version (Dry Run)

Preview the version without making changes:

```bash
epub-upgrade input.epub -o output.epub --dry-run
```

**Output:**
```
EPUB Version Detection (Dry Run)
==================================================
Input file: input.epub
Detected version: 2.0 (2)
Status: Would upgrade to EPUB 3.0
```

#### Generate Upgrade Report

Create a JSON report of the upgrade:

```bash
epub-upgrade input.epub -o output.epub --report upgrade.json
```

#### Force Rewrite EPUB 3

Normalize an existing EPUB 3 file (regenerate nav.xhtml, etc.):

```bash
epub-upgrade input.epub -o output.epub --force-rewrite
```

## Quick Start - Graphical Interface

### Launch the GUI

**Easiest way (using launch script):**
```bash
./start_gui.sh        # macOS/Linux
start_gui.bat         # Windows
python start_gui.py   # Any platform
```

**Alternative methods:**
```bash
epub-repair-gui
# or
python -m epub_repair.gui
```

The launch scripts automatically activate the virtual environment if present.

### Using the GUI

The GUI provides a tabbed interface with two tabs:

1. **Format Repair Tab**
   - Select repair mode (Safe or Aggressive)
   - Optional report generation
   - Click "Repair EPUB" to start

2. **Version Upgrade Tab**
   - Enable upgrade checkbox
   - Select target version (3.0, 3.2, 3.3)
   - Options: Force rewrite, Dry run
   - Optional upgrade report
   - Click "Upgrade EPUB" to start

Both tabs share the same input/output file selection, making it easy to use both tools in sequence.

**Workflow Example:**
1. Select input EPUB file
2. Use "Version Upgrade" tab to upgrade EPUB 2 → EPUB 3
3. Switch to "Format Repair" tab to fix formatting issues
4. View results in the shared results panel

## What Gets Fixed?

### Automatic Repairs

The tool automatically fixes:

1. **Fake Headings** → Real semantic headings (`<h1>`, `<h2>`, `<h3>`)
   - Converts `<p class="heading1">` to proper `<h2>` elements
   - Ensures proper heading hierarchy

2. **Paragraph Structure**
   - Converts `<div>` elements to `<p>` where appropriate
   - Removes excessive `<br/>` tags

3. **Lists**
   - Converts visual lists (paragraphs with bullets) to semantic `<ul>`/`<ol>`
   - Removes manual bullet characters

4. **Page Breaks**
   - Removes unwanted empty spaces/page breaks
   - **Keeps page breaks only before chapters**

5. **Images**
   - Adds missing `alt` attributes for accessibility

6. **CSS Cleanup**
   - Removes aggressive font sizing that prevents reader resizing
   - Removes fixed line-heights
   - Removes modern layout features (flex/grid) that break older readers

### Version Upgrade - What Gets Upgraded

The upgrade tool converts EPUB 2 to EPUB 3:

1. **Package Version**: Updates `<package version="2.0">` to `version="3.0"`
2. **Language Attribute**: Ensures `xml:lang` is set on package element
3. **Metadata**: Validates and adds missing required fields:
   - `dc:title` (required)
   - `dc:identifier` (required)
   - `dc:language` (required)
4. **Navigation**: Converts NCX (`toc.ncx`) to EPUB 3 `nav.xhtml`
5. **Content Documents**: Ensures XHTML files have `lang` attributes

## Common Use Cases

### Fix a Single EPUB

**Repair only:**
```bash
epub-format-fix book.epub -o book_fixed.epub --report report.txt
```

**Upgrade then repair (recommended workflow):**
```bash
# Step 1: Upgrade version
epub-upgrade book.epub -o book_upgraded.epub --report upgrade.json

# Step 2: Repair formatting
epub-format-fix book_upgraded.epub -o book_fixed.epub --report repair.txt
```

### Batch Process Multiple Files

**On macOS/Linux:**
```bash
for file in *.epub; do
    epub-format-fix "$file" -o "fixed_${file}" --report "${file%.epub}_report.txt"
done
```

**On Windows (PowerShell):**
```powershell
Get-ChildItem *.epub | ForEach-Object {
    epub-format-fix $_.Name -o "fixed_$($_.Name)" --report "$($_.BaseName)_report.txt"
}
```

### Preview Changes Before Applying

1. Run with a report to see what will change:
   ```bash
   epub-format-fix input.epub -o output.epub --report preview.txt
   ```

2. Review the report file

3. If satisfied, the output EPUB is already created

## Understanding the Report

### Text Report Example

```
EPUB Repair Report
==================================================

Summary:
  - headings.converted_fake_headings: 12
  - paragraphs.converted_divs: 5
  - lists.converted_paragraphs: 8
  - breaks.removed_page_breaks: 3
  - images.added_alt: 2

Total files modified: 5

Changes by file:
  chapter1.xhtml:
    - Converted 3 fake headings
    - Created 2 semantic lists
  chapter2.xhtml:
    - Removed 2 page breaks
    - Added 1 alt attribute
```

### JSON Report Structure (Repair)

```json
{
  "counters": {
    "headings.converted_fake_headings": 12,
    "paragraphs.converted_divs": 5,
    ...
  },
  "changes": [
    {
      "file": "chapter1.xhtml",
      "description": "Converted 3 fake headings",
      "details": {...}
    }
  ],
  "total_files_modified": 5,
  "mode": "safe"
}
```

### Upgrade Report Structure

```json
{
  "original_version": "2",
  "raw_original_version": "2.0",
  "new_version": "3.0",
  "nav_converted": true,
  "ncx_source": "OEBPS/toc.ncx",
  "warnings": [
    "Missing dc:title, added placeholder"
  ],
  "notes": [
    "File already EPUB 3, copied unchanged"
  ]
}
```

## Troubleshooting

### "File not found" Error

- Check that the input file path is correct
- Use absolute paths if relative paths don't work
- Ensure the file has `.epub` extension

### "Malformed EPUB" Error

- The EPUB structure might be invalid
- Try opening it in an EPUB reader first to verify it's valid
- The tool assumes valid EPUB structure

### No Changes Reported

- Your EPUB might already be well-formatted
- Try `--aggressive` mode for more fixes
- Check the report file for details

### GUI Won't Launch

- Ensure Tkinter is available: `python3 -c "import tkinter"`
- On Linux, you may need: `sudo apt-get install python3-tk`
- Try the command-line interface instead

## Tips & Best Practices

1. **Always Keep Backups**
   - The tool creates a new file, but keep your originals safe
   - Use descriptive output names: `book_repaired.epub`

2. **Start with Safe Mode**
   - Test with `--safe` first
   - Use `--aggressive` only if needed

3. **Review Reports**
   - Check reports to understand what changed
   - Helps you learn what issues your EPUBs have

4. **Test in Your Reader**
   - Always test the repaired EPUB in your target reader
   - Verify formatting looks correct

5. **Batch Processing**
   - Use scripts for multiple files
   - Generate reports for each file to track changes

## What the Tool Does NOT Do

- ❌ Modify textual content
- ❌ Handle fixed-layout EPUBs (reflowable only)
- ❌ Remove DRM or modify protected content
- ❌ Validate EPUB structure (assumes valid input)
- ❌ Modify cover images or metadata

## Getting Help

### Command Help

```bash
epub-format-fix --help
```

### Check Installation

```bash
epub-format-fix --version  # If version command exists
python -c "import epub_repair; print('Installed successfully')"
```

## Next Steps

- Read the full [README.md](../README.md) for detailed information
- Check [architecture.md](architecture.md) for technical details
- Review [design.md](design.md) for implementation specifics

## Example Workflows

### Complete Workflow: Upgrade + Repair

```bash
# 1. Install
pip install -e .

# 2. Check EPUB version (dry run)
epub-upgrade old_book.epub -o temp.epub --dry-run

# 3. Upgrade EPUB 2 → EPUB 3
epub-upgrade old_book.epub -o upgraded.epub --report upgrade.json

# 4. Repair formatting
epub-format-fix upgraded.epub -o final.epub --report repair.txt

# 5. Review reports
cat upgrade.json
cat repair.txt

# 6. Test the final EPUB in your reader
```

### Quick Repair Only

```bash
# If already EPUB 3, just repair formatting
epub-format-fix my_book.epub -o my_book_fixed.epub --report report.txt
```

### Using the GUI

1. Launch GUI: `./start_gui.sh`
2. Select input EPUB file
3. **Version Upgrade Tab**: Upgrade EPUB 2 → EPUB 3 (if needed)
4. **Format Repair Tab**: Fix formatting issues
5. View results in the results panel

---

**Happy EPUB Processing!** 📚✨
