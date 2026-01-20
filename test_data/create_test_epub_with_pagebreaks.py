"""Script to create a test EPUB with page breaks."""

import zipfile
from pathlib import Path

def create_test_epub(output_path: Path):
    """Create a test EPUB with page breaks."""
    
    temp_dir = Path("/tmp/test_epub_pb")
    temp_dir.mkdir(exist_ok=True)
    
    # mimetype
    (temp_dir / "mimetype").write_text("application/epub+zip")
    
    # META-INF/container.xml
    meta_inf = temp_dir / "META-INF"
    meta_inf.mkdir(exist_ok=True)
    container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
    (meta_inf / "container.xml").write_text(container_xml)
    
    # OEBPS directory
    oebps = temp_dir / "OEBPS"
    oebps.mkdir(exist_ok=True)
    
    # content.opf
    opf_content = """<?xml version="1.0" encoding="UTF-8"?>
<package version="2.0" xmlns="http://www.idpf.org/2007/opf" unique-identifier="bookid">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:title>Test EPUB with Page Breaks</dc:title>
    <dc:identifier id="bookid">test-epub-pb-001</dc:identifier>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="chapter2" href="chapter2.xhtml" media-type="application/xhtml+xml"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
    <itemref idref="chapter2"/>
  </spine>
</package>"""
    (oebps / "content.opf").write_text(opf_content)
    
    # chapter1.xhtml with unwanted page breaks
    chapter1_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
</head>
<body>
  <h2>Chapter One</h2>
  <p>This is the first paragraph of chapter one.</p>
  <p></p>
  <p>This paragraph has unwanted spacing before it.</p>
  <p class="page-break"></p>
  <p>More text with unwanted page break.</p>
  <p style="page-break-before: always;"></p>
  <p>Another paragraph with page break style.</p>
  <p>End of chapter one content.</p>
</body>
</html>"""
    (oebps / "chapter1.xhtml").write_text(chapter1_xhtml)
    
    # chapter2.xhtml - page break before chapter should be kept
    chapter2_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 2</title>
</head>
<body>
  <p></p>
  <h2>Chapter Two</h2>
  <p>This is chapter two. The page break before it should be kept.</p>
  <p></p>
  <p>But this empty paragraph in the middle should be removed.</p>
  <p>More content here.</p>
</body>
</html>"""
    (oebps / "chapter2.xhtml").write_text(chapter2_xhtml)
    
    # Create EPUB ZIP
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.write(temp_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "mimetype":
                arcname = file_path.relative_to(temp_dir)
                zip_file.write(file_path, arcname)
    
    print(f"Created test EPUB with page breaks: {output_path}")

if __name__ == "__main__":
    output = Path("test_book_pagebreaks.epub")
    create_test_epub(output)
    print(f"Test EPUB created: {output.absolute()}")
