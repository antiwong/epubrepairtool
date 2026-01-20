# EPUB Upgrade Tool

A Python tool for detecting EPUB versions and upgrading EPUB 2 files to EPUB 3.

## Features

- **Version Detection**: Automatically detects EPUB 2.0, 2.0.1, 3.0, 3.2, etc.
- **EPUB 2 → EPUB 3 Conversion**: Upgrades EPUB 2 files to clean EPUB 3
- **NCX to nav.xhtml**: Converts legacy NCX navigation to EPUB 3 nav.xhtml
- **Metadata Validation**: Ensures required metadata fields are present
- **Dry Run Mode**: Preview what would be changed without modifying files

## Installation

The tool is installed as part of the epub-repair package:

```bash
pip install -e .
```

## Usage

### Basic Upgrade

Upgrade an EPUB 2 file to EPUB 3:

```bash
epub-upgrade input.epub -o output.epub
```

### Check Version (Dry Run)

Check the version without modifying the file:

```bash
epub-upgrade input.epub -o output.epub --dry-run
```

### Generate Report

Create a JSON report of the upgrade process:

```bash
epub-upgrade input.epub -o output.epub --report upgrade_report.json
```

### Force Rewrite EPUB 3

Normalize an existing EPUB 3 file (e.g., regenerate nav.xhtml):

```bash
epub-upgrade input.epub -o output.epub --force-rewrite
```

### Target Version

Specify a target version (default is 3.0):

```bash
epub-upgrade input.epub -o output.epub --target-version 3.2
```

## What Gets Upgraded?

### EPUB 2 → EPUB 3 Conversion

1. **Package Version**: Updates `<package version="2.0">` to `version="3.0"`
2. **Language Attribute**: Ensures `xml:lang` is set on package element
3. **Metadata**: Validates and adds missing required fields:
   - `dc:title` (required)
   - `dc:identifier` (required)
   - `dc:language` (required)
4. **Navigation**: Converts NCX (`toc.ncx`) to EPUB 3 `nav.xhtml`
5. **Content Documents**: Ensures XHTML files have `lang` attributes

### NCX → nav.xhtml Conversion

- Parses the existing `toc.ncx` file
- Extracts the navigation hierarchy
- Creates a new `nav.xhtml` with proper EPUB 3 structure
- Adds `properties="nav"` to manifest item
- Preserves the full navigation tree

## Report Format

The JSON report includes:

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
  "notes": []
}
```

## Limitations

- **Reflowable EPUBs Only**: Designed for reflowable EPUBs, not fixed-layout
- **No DRM Support**: Cannot process DRM-protected files
- **No Validation**: Assumes input EPUB is structurally valid
- **Minimal Content Changes**: Focuses on structure, not formatting

## Integration with EPUB Repair

This tool is designed to work alongside the EPUB Repair tool:

1. **First**: Upgrade EPUB 2 → EPUB 3 using `epub-upgrade`
2. **Then**: Repair formatting using `epub-format-fix`

Example workflow:

```bash
# Step 1: Upgrade version
epub-upgrade old_book.epub -o upgraded.epub

# Step 2: Repair formatting
epub-format-fix upgraded.epub -o final.epub
```

## Examples

### Example 1: Simple Upgrade

```bash
epub-upgrade book_v2.epub -o book_v3.epub
```

Output:
```
EPUB Upgrade Report
==================================================
Original version: 2.0 (2)
New version: 3.0
Navigation: Converted NCX (OEBPS/toc.ncx) to nav.xhtml
```

### Example 2: Check Version

```bash
epub-upgrade book.epub -o output.epub --dry-run
```

Output:
```
EPUB Version Detection (Dry Run)
==================================================
Input file: book.epub
Detected version: 3.0 (3)
Status: Already EPUB 3, no upgrade needed
```

## Error Handling

The tool will:
- Report missing metadata and add placeholders
- Warn if NCX conversion fails
- Skip content document updates if files are malformed
- Preserve all original files except those explicitly modified

## Technical Details

- Uses Python's `xml.etree.ElementTree` for XML processing
- Preserves EPUB container structure (mimetype first, uncompressed)
- Maintains file ordering and directory structure
- Handles both EPUB 2.0 and 2.0.1 formats
