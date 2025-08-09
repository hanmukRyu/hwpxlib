import json

from text_modifier import enumerate_text_nodes, list_sentences
from reader import HWPXReader


def test_phrase_id_grouping():
    hwpx = HWPXReader.read("testFile/tool/textextractor/RectInPara.hwpx")
    by_pid = {}
    for idx, _file, _elem, _attr, text, pid in enumerate_text_nodes(hwpx):
        by_pid.setdefault(pid, []).append(text)
    counts = [len(v) for pid, v in by_pid.items() if pid is not None]
    assert max(counts) >= 5


def test_list_sentences_json_includes_phrase_id(capsys):
    list_sentences("testFile/tool/textextractor/RectInPara.hwpx", as_json=True)
    output = capsys.readouterr().out
    data = json.loads(output)
    assert all("phrase_id" in item for item in data)
