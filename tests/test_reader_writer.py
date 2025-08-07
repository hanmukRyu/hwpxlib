from xml.etree import ElementTree as ET

from reader import HWPXReader, MIMETYPE
from writer import HwpxWriter


def test_reader_parses_sample():
    hwpx = HWPXReader.read("testFile/tool/blank.hwpx")
    assert hwpx.version_xml is not None
    assert hwpx.content_hpf is not None
    assert "Contents/section0.xml" in hwpx.content_files


def test_writer_roundtrip(tmp_path):
    hwpx = HWPXReader.read("testFile/tool/blank.hwpx")
    version_xml = ET.tostring(hwpx.version_xml.getroot(), encoding="unicode")
    container_xml = ET.tostring(hwpx.container_xml.getroot(), encoding="unicode")
    manifest_xml = ET.tostring(hwpx.manifest_xml.getroot(), encoding="unicode")
    content_hpf = ET.tostring(hwpx.content_hpf.getroot(), encoding="unicode")
    files = {
        name: ET.tostring(tree.getroot(), encoding="unicode")
        for name, tree in hwpx.content_files.items()
    }
    writer = HwpxWriter(
        version_xml,
        container_xml,
        manifest_xml,
        content_hpf,
        files,
        MIMETYPE,
    )
    out_path = tmp_path / "out.hwpx"
    writer.write(out_path)
    reread = HWPXReader.read(out_path)
    assert set(reread.content_files.keys()) == set(hwpx.content_files.keys())
