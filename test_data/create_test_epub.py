"""Script to create a minimal test EPUB with formatting issues."""

import zipfile
from pathlib import Path

def create_test_epub(output_path: Path):
    """Create a minimal EPUB with formatting issues for testing."""
    
    # Create temporary directory structure
    temp_dir = Path("/tmp/test_epub")
    temp_dir.mkdir(exist_ok=True)
    
    # mimetype (must be first, uncompressed)
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
    <dc:title>Test EPUB</dc:title>
    <dc:identifier id="bookid">test-epub-001</dc:identifier>
  </metadata>
  <manifest>
    <item id="chapter1" href="chapter1.xhtml" media-type="application/xhtml+xml"/>
    <item id="style" href="style.css" media-type="text/css"/>
  </manifest>
  <spine toc="ncx">
    <itemref idref="chapter1"/>
  </spine>
</package>"""
    (oebps / "content.opf").write_text(opf_content)
    
    # chapter1.xhtml with formatting issues
    chapter_xhtml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml">
<head>
  <title>Chapter 1</title>
  <link rel="stylesheet" type="text/css" href="style.css"/>
</head>
<body>
  <p class="heading1">Chapter One</p>
  <p>This is a paragraph with some text.</p>
  <div class="body-text">This should be a paragraph.</div>
  <p>- First item</p>
  <p>- Second item</p>
  <p>- Third item</p>
  <br/><br/><br/>
  <p>More text here.</p>
  <img src="test.jpg" />
</body>
</html>"""
    (oebps / "chapter1.xhtml").write_text(chapter_xhtml)
    
    # style.css with aggressive CSS
    css_content = """body {
  font-size: 12px;
  line-height: 1.0;
  font-family: "Times New Roman", serif;
}

p.heading1 {
  font-size: 24px;
  font-weight: bold;
}

div.body-text {
  text-indent: 20px;
}"""
    (oebps / "style.css").write_text(css_content)
    
    # Create EPUB ZIP
    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        # Add mimetype first, uncompressed
        zip_file.write(temp_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
        
        # Add all other files
        for file_path in temp_dir.rglob("*"):
            if file_path.is_file() and file_path.name != "mimetype":
                arcname = file_path.relative_to(temp_dir)
                zip_file.write(file_path, arcname)
    
    print(f"Created test EPUB: {output_path}")

if __name__ == "__main__":
    output = Path("test_book.epub")
    create_test_epub(output)
    print(f"Test EPUB created: {output.absolute()}")
