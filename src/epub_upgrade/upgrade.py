"""High-level EPUB 2 → EPUB 3 upgrade orchestration."""

from pathlib import Path
from xml.etree import ElementTree as ET

from .epub_io import get_opf_path, load_opf, save_opf
from .nav_conversion import add_nav_to_manifest, convert_ncx_to_nav_xhtml, find_ncx_in_manifest
from .reporting import Reporter
from .versioning import detect_epub_version


def upgrade_to_epub3(
    extracted_root: Path,
    target_version: str,
    reporter: Reporter,
    force_rewrite: bool = False
) -> None:
    """
    Mutate the extracted EPUB directory in-place to become EPUB 3.
    
    Args:
        extracted_root: Root directory of extracted EPUB
        target_version: Target version (e.g., "3.0")
        reporter: Reporter instance for logging
        force_rewrite: If True, upgrade even if already EPUB 3
    """
    # Load OPF and detect version
    opf_path = get_opf_path(extracted_root)
    opf_tree = load_opf(opf_path)
    normalized_version, raw_version = detect_epub_version(opf_tree)
    
    # If already EPUB 3 and not forcing rewrite, just return
    if normalized_version == "3" and not force_rewrite:
        reporter.note("Already EPUB 3, no upgrade needed")
        return
    
    root = opf_tree.getroot()
    ns = {"opf": "http://www.idpf.org/2007/opf", "dc": "http://purl.org/dc/elements/1.1/"}
    
    # 1. Update package version
    root.set("version", target_version)
    
    # 2. Ensure required attributes
    if not root.get("xml:lang") and not root.get("lang"):
        # Try to get language from metadata
        metadata = root.find(".//opf:metadata", ns)
        if metadata is not None:
            lang_elem = metadata.find("dc:language", ns)
            if lang_elem is not None and lang_elem.text:
                root.set("xml:lang", lang_elem.text.strip())
            else:
                root.set("xml:lang", "en")
                reporter.warn("No language found, defaulting to 'en'")
        else:
            root.set("xml:lang", "en")
            reporter.warn("No metadata found, defaulting language to 'en'")
    
    # 3. Metadata sanity checks
    metadata = root.find(".//opf:metadata", ns)
    if metadata is None:
        # Create metadata element if missing
        metadata = ET.SubElement(root, "metadata", xmlns_dc="http://purl.org/dc/elements/1.1/")
        reporter.warn("No metadata element found, created empty one")
    
    # Check for required metadata fields
    has_title = metadata.find("dc:title", ns) is not None
    has_identifier = metadata.find("dc:identifier", ns) is not None
    has_language = metadata.find("dc:language", ns) is not None
    
    if not has_title:
        title = ET.SubElement(metadata, "dc:title")
        title.text = "Unknown Title"
        reporter.warn("Missing dc:title, added placeholder")
    
    if not has_identifier:
        identifier = ET.SubElement(metadata, "dc:identifier", id="bookid")
        identifier.text = "unknown-id"
        reporter.warn("Missing dc:identifier, added placeholder")
    
    if not has_language:
        language = ET.SubElement(metadata, "dc:language")
        language.text = "en"
        reporter.warn("Missing dc:language, added placeholder 'en'")
    
    # 4. Navigation conversion (NCX → nav.xhtml)
    opf_dir = opf_path.parent
    ncx_path = find_ncx_in_manifest(opf_tree, extracted_root, opf_path)
    
    if ncx_path:
        try:
            nav_relative = convert_ncx_to_nav_xhtml(ncx_path, extracted_root, opf_dir)
            add_nav_to_manifest(opf_tree, extracted_root / nav_relative, opf_dir)
            reporter.mark_nav_converted(str(ncx_path.relative_to(extracted_root)))
        except Exception as e:
            reporter.warn(f"Failed to convert NCX to nav.xhtml: {e}")
    else:
        # Check if nav.xhtml already exists
        nav_path = opf_dir / "nav.xhtml"
        if nav_path.exists():
            reporter.note("nav.xhtml already exists, no conversion needed")
        else:
            reporter.warn("No NCX found and no nav.xhtml exists - EPUB 3 requires navigation")
    
    # 5. Content document adjustments (minimal)
    # Ensure XHTML files have lang attribute
    spine = root.find(".//opf:spine", ns)
    if spine is not None:
        manifest = root.find(".//opf:manifest", ns)
        if manifest is not None:
            # Get language from package or metadata
            lang = root.get("xml:lang") or root.get("lang") or "en"
            
            for itemref in spine.findall("opf:itemref", ns):
                idref = itemref.get("idref", "")
                item = manifest.find(f".//opf:item[@id='{idref}']", ns)
                if item is not None:
                    href = item.get("href", "")
                    media_type = item.get("media-type", "")
                    
                    if media_type == "application/xhtml+xml" and href:
                        content_path = (opf_dir / href).resolve()
                        if content_path.exists():
                            _ensure_xhtml_lang(content_path, lang)
    
    # 6. Save updated OPF
    save_opf(opf_tree, opf_path)


def _ensure_xhtml_lang(xhtml_path: Path, lang: str) -> None:
    """
    Ensure XHTML file has lang attribute on html element.
    
    Args:
        xhtml_path: Path to XHTML file
        lang: Language code to use
    """
    try:
        tree = ET.parse(xhtml_path)
        root = tree.getroot()
        
        # Check if html element has lang or xml:lang
        if not root.get("lang") and not root.get("{http://www.w3.org/XML/1998/namespace}lang"):
            root.set("lang", lang)
            tree.write(
                xhtml_path,
                encoding="utf-8",
                xml_declaration=True,
                method="xml"
            )
    except Exception:
        # Silently fail - don't break upgrade for content issues
        pass
