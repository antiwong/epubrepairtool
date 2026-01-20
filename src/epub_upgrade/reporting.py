"""Reporting utilities for EPUB upgrade operations."""

import json
from pathlib import Path
from typing import List, Optional


class Reporter:
    """Collects and reports upgrade statistics and information."""
    
    def __init__(self):
        self.data = {
            "original_version": None,
            "raw_original_version": None,
            "new_version": None,
            "nav_converted": False,
            "ncx_source": None,
            "warnings": [],
            "notes": [],
        }
    
    def set_versions(self, original: str, raw_original: str, new: Optional[str] = None):
        """
        Set version information.
        
        Args:
            original: Normalized version ("2" or "3")
            raw_original: Full version string (e.g., "2.0", "3.0")
            new: New version if upgraded (optional)
        """
        self.data["original_version"] = original
        self.data["raw_original_version"] = raw_original
        self.data["new_version"] = new if new else original
    
    def mark_nav_converted(self, ncx_source: str):
        """
        Mark that NCX was converted to nav.xhtml.
        
        Args:
            ncx_source: Path to source NCX file
        """
        self.data["nav_converted"] = True
        self.data["ncx_source"] = ncx_source
    
    def warn(self, message: str):
        """
        Add a warning message.
        
        Args:
            message: Warning message
        """
        self.data["warnings"].append(message)
    
    def note(self, message: str):
        """
        Add a note/info message.
        
        Args:
            message: Note message
        """
        self.data["notes"].append(message)
    
    def to_json(self) -> dict:
        """
        Get report data as dictionary.
        
        Returns:
            Dictionary with all report data
        """
        return self.data.copy()
    
    def write_json(self, path: Path) -> None:
        """
        Write report as JSON file.
        
        Args:
            path: Output file path
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_json(), f, indent=2, ensure_ascii=False)
    
    def print_summary(self) -> None:
        """Print a human-readable summary to stdout."""
        print("\nEPUB Upgrade Report")
        print("=" * 50)
        print(f"Original version: {self.data['raw_original_version']} ({self.data['original_version']})")
        
        if self.data["new_version"] != self.data["original_version"]:
            print(f"New version: {self.data['new_version']}")
        else:
            print("Version unchanged (already EPUB 3)")
        
        if self.data["nav_converted"]:
            print(f"Navigation: Converted NCX ({self.data['ncx_source']}) to nav.xhtml")
        else:
            print("Navigation: No conversion needed")
        
        if self.data["warnings"]:
            print("\nWarnings:")
            for warning in self.data["warnings"]:
                print(f"  - {warning}")
        
        if self.data["notes"]:
            print("\nNotes:")
            for note in self.data["notes"]:
                print(f"  - {note}")
