from zipfile import ZipFile
from pathlib import Path
import xml.etree.ElementTree as ET

HP_NAMESPACE = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def extract_text(path: str) -> str:
    """Return the concatenated text of all paragraphs in an HWPX file."""
    result: list[str] = []
    with ZipFile(path) as zf:
        section_files = [name for name in zf.namelist() if name.startswith("Contents/section") and name.endswith(".xml")]
        for section in section_files:
            xml_data = zf.read(section)
            root = ET.fromstring(xml_data)
            for t in root.iter(HP_NAMESPACE + "t"):
                if t.text:
                    result.append(t.text)
    return "".join(result)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python text_extractor.py <file.hwpx>")
    else:
        print(extract_text(sys.argv[1]))
