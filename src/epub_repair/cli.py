"""Command-line interface for EPUB repair tool."""

import argparse
import sys
import tempfile
from pathlib import Path
from typing import Dict, Optional

from .epub_io import extract_epub, parse_container, parse_opf, repackage_epub
from .models import EpubBook
from .reporting import Reporter
from .rules import AGGRESSIVE_RULES, SAFE_RULES


def main() -> int:
    """Entry point for CLI application."""
    args = parse_args()
    
    try:
        summary = run_repair(
            input_path=Path(args.input),
            output_path=Path(args.output),
            mode=args.mode,
            report_path=Path(args.report) if args.report else None
        )
        
        # Print summary to console
        print("\nRepair Summary:")
        print("=" * 50)
        if summary["counters"]:
            for category, count in sorted(summary["counters"].items()):
                print(f"  {category}: {count}")
        print(f"\nTotal files modified: {summary['total_files_modified']}")
        
        return 0
    
    except FileNotFoundError as e:
        print(f"Error: File not found: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.
    
    Args:
        args: Optional argument list (defaults to sys.argv[1:])
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Repair formatting issues in reflowable EPUB files",
        prog="epub-format-fix"
    )
    
    parser.add_argument(
        "input",
        help="Path to input EPUB file"
    )
    
    parser.add_argument(
        "-o", "--output",
        required=True,
        help="Path to output EPUB file"
    )
    
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--safe",
        action="store_const",
        const="safe",
        dest="mode",
        default="safe",
        help="Apply safe normalization only (default)"
    )
    mode_group.add_argument(
        "--aggressive",
        action="store_const",
        const="aggressive",
        dest="mode",
        help="Apply aggressive normalization (includes safe rules)"
    )
    
    parser.add_argument(
        "--report",
        help="Path to output report file (JSON if .json, text otherwise)"
    )
    
    return parser.parse_args(args)


def run_repair(
    input_path: Path,
    output_path: Path,
    mode: str = "safe",
    report_path: Optional[Path] = None
) -> Dict:
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
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Select rule set
    if mode == "aggressive":
        rules = AGGRESSIVE_RULES
    else:
        rules = SAFE_RULES
    
    reporter = Reporter()
    
    # Extract EPUB to temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_epub(input_path, temp_path)
        
        # Parse EPUB structure
        container_path = temp_path / "META-INF" / "container.xml"
        if not container_path.exists():
            raise ValueError("META-INF/container.xml not found in EPUB")
        
        opf_relative_path = parse_container(container_path)
        opf_path = temp_path / opf_relative_path
        
        if not opf_path.exists():
            raise ValueError(f"OPF file not found: {opf_path}")
        
        spine_items, manifest_items = parse_opf(opf_path, temp_path)
        
        book = EpubBook(
            root_path=temp_path,
            opf_path=opf_path,
            spine_items=spine_items,
            manifest_items=manifest_items
        )
        
        # Apply rules
        for rule in rules:
            try:
                rule(book, reporter)
            except Exception as e:
                reporter.log_change(
                    Path("unknown"),
                    f"Rule {rule.__name__} failed: {e}"
                )
        
        # Repackage EPUB
        repackage_epub(temp_path, output_path)
    
    # Generate report
    summary = reporter.get_summary()
    summary["mode"] = mode
    
    if report_path:
        if report_path.suffix.lower() == ".json":
            reporter.write_json(report_path)
        else:
            reporter.write_text(report_path)
    
    return summary


if __name__ == "__main__":
    sys.exit(main())
