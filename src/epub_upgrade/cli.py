"""Command-line interface for EPUB upgrade tool."""

import argparse
import sys
import tempfile
from pathlib import Path

from .epub_io import copy_epub, extract_epub, repackage_epub, verify_epub_file
from .reporting import Reporter
from .upgrade import upgrade_to_epub3
from .epub_io import get_opf_path
from .versioning import detect_epub_version, load_opf


def main() -> int:
    """Entry point for CLI application."""
    args = parse_args()
    
    try:
        input_path = Path(args.input)
        output_path = Path(args.output)
        target_version = args.target_version
        report_path = Path(args.report) if args.report else None
        force_rewrite = args.force_rewrite
        dry_run = args.dry_run
        
        # Verify input file
        verify_epub_file(input_path)
        
        # Extract to temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            extract_epub(input_path, temp_path)
            
            # Load OPF and detect version
            opf_path = get_opf_path(temp_path)
            opf_tree = load_opf(opf_path)
            normalized_version, raw_version = detect_epub_version(opf_tree)
            
            # Initialize reporter
            reporter = Reporter()
            reporter.set_versions(normalized_version, raw_version)
            
            if dry_run:
                # Dry run: only detect and report
                print(f"\nEPUB Version Detection (Dry Run)")
                print("=" * 50)
                print(f"Input file: {input_path}")
                print(f"Detected version: {raw_version} ({normalized_version})")
                
                if normalized_version == "3":
                    print("Status: Already EPUB 3, no upgrade needed")
                else:
                    print(f"Status: Would upgrade to EPUB {target_version}")
                
                if report_path:
                    reporter.write_json(report_path)
                    print(f"\nReport written to: {report_path}")
                
                return 0
            
            # Determine if upgrade is needed
            needs_upgrade = normalized_version != "3" or force_rewrite
            
            if not needs_upgrade:
                # Already EPUB 3, just copy
                copy_epub(input_path, output_path)
                reporter.note("File already EPUB 3, copied unchanged")
            else:
                # Perform upgrade
                upgrade_to_epub3(temp_path, target_version, reporter, force_rewrite)
                reporter.set_versions(normalized_version, raw_version, target_version)
                
                # Repackage EPUB
                repackage_epub(temp_path, output_path)
            
            # Print summary
            reporter.print_summary()
            
            # Write report if requested
            if report_path:
                reporter.write_json(report_path)
                print(f"\nReport written to: {report_path}")
            
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


def parse_args(args=None):
    """
    Parse command-line arguments.
    
    Args:
        args: Optional argument list (defaults to sys.argv[1:])
    
    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Detect EPUB version and upgrade EPUB 2 to EPUB 3",
        prog="epub-upgrade"
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
    
    parser.add_argument(
        "--target-version",
        default="3.0",
        help="Target EPUB version (default: 3.0)"
    )
    
    parser.add_argument(
        "--report",
        help="Path to output JSON report file"
    )
    
    parser.add_argument(
        "--force-rewrite",
        action="store_true",
        help="Rewrite even if already EPUB 3 (e.g., normalize nav document)"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run detection and analysis only, do not write output file"
    )
    
    return parser.parse_args(args)


if __name__ == "__main__":
    sys.exit(main())
