"""Reporter for collecting and outputting repair statistics."""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


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
        self.counters[category] = self.counters.get(category, 0) + count
    
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
        change = {
            "file": str(file_path),
            "description": description,
        }
        if details:
            change["details"] = details
        self.changes.append(change)
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary of all statistics and changes.
        
        Returns:
            Dictionary with:
            - counters: Dict of category -> count
            - changes: List of change records
            - total_files_modified: Count of unique files
        """
        unique_files = set(change["file"] for change in self.changes)
        return {
            "counters": self.counters,
            "changes": self.changes,
            "total_files_modified": len(unique_files),
        }
    
    def write_json(self, path: Path) -> None:
        """
        Write report as JSON.
        
        Args:
            path: Output file path
        """
        summary = self.get_summary()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
    
    def write_text(self, path: Path) -> None:
        """
        Write report as human-readable text.
        
        Args:
            path: Output file path
        """
        summary = self.get_summary()
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("EPUB Repair Report\n")
            f.write("=" * 50 + "\n\n")
            
            f.write("Summary:\n")
            if summary["counters"]:
                for category, count in sorted(summary["counters"].items()):
                    f.write(f"  - {category}: {count}\n")
            else:
                f.write("  (No changes recorded)\n")
            
            f.write(f"\nTotal files modified: {summary['total_files_modified']}\n\n")
            
            if summary["changes"]:
                f.write("Changes by file:\n")
                # Group changes by file
                changes_by_file: Dict[str, List[str]] = {}
                for change in summary["changes"]:
                    file_path = change["file"]
                    if file_path not in changes_by_file:
                        changes_by_file[file_path] = []
                    changes_by_file[file_path].append(change["description"])
                
                for file_path, descriptions in sorted(changes_by_file.items()):
                    f.write(f"\n  {file_path}:\n")
                    for desc in descriptions:
                        f.write(f"    - {desc}\n")
