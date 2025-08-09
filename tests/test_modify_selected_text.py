from text_modifier import enumerate_text_nodes, modify_selected_text
from reader import HWPXReader


def test_modify_selected_text(tmp_path):
    src = "testFile/tool/textextractor/multipara.hwpx"

    hwpx = HWPXReader.read(src)
    nodes = list(enumerate_text_nodes(hwpx))
    assert len(nodes) >= 2

    # pick a node with alphabetic characters to ensure modification
    target_index = 7
    out = tmp_path / "out.hwpx"
    count = modify_selected_text(src, out, {target_index: "REPLACED"})
    assert count == 1

    hwpx_out = HWPXReader.read(out)
    nodes_out = list(enumerate_text_nodes(hwpx_out))

    assert nodes_out[target_index][4] == "REPLACED"
    # Another index should stay the same
    assert nodes_out[0][4] == nodes[0][4]
