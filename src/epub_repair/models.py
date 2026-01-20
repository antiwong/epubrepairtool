"""Data models for EPUB structure representation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List


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
        xhtml_files = []
        for spine_item in self.spine_items:
            manifest_item = self.manifest_items.get(spine_item.idref)
            if manifest_item and manifest_item.media_type == "application/xhtml+xml":
                xhtml_files.append(spine_item.href)
        return xhtml_files
    
    def get_css_files(self) -> List[Path]:
        """
        Get all CSS files referenced in manifest.
        
        Returns:
            List of absolute paths to CSS files
        """
        css_files = []
        for manifest_item in self.manifest_items.values():
            if manifest_item.media_type == "text/css":
                css_path = self.resolve_path(str(manifest_item.href))
                css_files.append(css_path)
        return css_files
    
    def resolve_path(self, href: str) -> Path:
        """
        Resolve relative href to absolute path.
        
        Args:
            href: Relative path from OPF location
        
        Returns:
            Absolute path resolved from root_path
        """
        # OPF is typically in the same directory as content or in OEBPS/
        # Resolve href relative to OPF's parent directory
        opf_parent = self.opf_path.parent
        resolved = (opf_parent / href).resolve()
        
        # If not found, try relative to root
        if not resolved.exists():
            resolved = (self.root_path / href).resolve()
        
        return resolved
