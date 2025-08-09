import json

from text_modifier import export_text_segments


def test_export_segments(tmp_path):
    out_json = tmp_path / "segments.json"
    export_text_segments("sample.hwpx", out_json)

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data, "expected at least one text segment"

    first = data[0]
    assert {"index", "file", "attr", "text", "format"} <= set(first.keys())
    assert isinstance(first["format"], dict)
