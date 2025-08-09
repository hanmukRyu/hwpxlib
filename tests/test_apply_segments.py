import json
from text_modifier import export_text_segments, apply_segments


def test_apply_segments(tmp_path):
    seg_path = tmp_path / "segments.json"
    export_text_segments("sample.hwpx", seg_path)
    segments = json.loads(seg_path.read_text(encoding="utf-8"))

    target = next(seg for seg in segments if seg["file"] == "Contents/section0.xml")
    target["text"] = "MODIFIED TEXT"

    mod_json = tmp_path / "modified.json"
    mod_json.write_text(json.dumps([target], ensure_ascii=False), encoding="utf-8")

    out_hwpx = tmp_path / "out.hwpx"
    apply_segments("sample.hwpx", mod_json, out_hwpx)

    verify_json = tmp_path / "verify.json"
    export_text_segments(out_hwpx, verify_json)
    updated_segments = json.loads(verify_json.read_text(encoding="utf-8"))
    updated = next(
        seg for seg in updated_segments if seg["file"] == target["file"] and seg["index"] == target["index"]
    )
    assert updated["text"] == "MODIFIED TEXT"
