import json

from text_modifier import export_text_segments


def test_export_segments(tmp_path):
    out_json = tmp_path / "segments.json"
    export_text_segments("sample.hwpx", out_json)

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert data, "expected at least one text segment"

    first = data[0]
    assert {"index", "file", "attr", "text", "format", "phrase_id"} <= set(first.keys())
    assert isinstance(first["format"], dict)


def test_phrase_id_groups_runs(tmp_path):
    out_json = tmp_path / "segments.json"
    export_text_segments("sample.hwpx", out_json)

    data = json.loads(out_json.read_text(encoding="utf-8"))

    groups = {}
    for seg in data:
        if seg.get("phrase_id") is None or "paragraph" not in seg["format"]:
            continue
        key = (seg["phrase_id"], json.dumps(seg["format"]["paragraph"], sort_keys=True))
        groups.setdefault(key, []).append(seg)

    multi_segments = next((g for g in groups.values() if len(g) >= 2), None)
    assert multi_segments is not None, "expected at least one paragraph with multiple segments"
    pid = multi_segments[0]["phrase_id"]
    assert all(seg["phrase_id"] == pid for seg in multi_segments)
