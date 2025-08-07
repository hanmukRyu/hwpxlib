from hwpxlib import HwpxArchive


def test_read_write_roundtrip(tmp_path):
    original = HwpxArchive.read("testFile/tool/blank.hwpx")
    out_path = tmp_path / "copy.hwpx"
    original.write(out_path)
    reread = HwpxArchive.read(out_path)
    assert original.files.keys() == reread.files.keys()
    for key in original.files:
        assert original.files[key] == reread.files[key]
