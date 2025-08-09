"""HWPX 파일의 텍스트를 수정하는 유틸리티 함수들.

이 모듈은 HWPX 파일에서 텍스트를 읽고 수정한 뒤 저장하는 고수준 API를 제공합니다.
가능하다면 :mod:`compatible_writer` 의 저장 함수를 사용하고, 그렇지 않으면 ZIP 기반
로직으로 직접 저장하여 네임스페이스를 보존합니다. `reader` 와
`text_extractor` 모듈을 조합하여 사용합니다.
"""

from typing import Callable, Dict, Any
import json
import re

from reader import HWPXReader
from text_extractor import extract_text
from writer import save_modified_hwpx

HP_NAMESPACE = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"

# Note: helper functions `_modify_text_preserve_formatting` and
# `_modify_text_simple` were removed. If future features require them,
# they can be restored from the Git history.


def enumerate_text_nodes(hwpx):
    """Yield all text nodes in ``hwpx`` along with their location information.

    Each yielded item is ``(index, file_name, element, attr, text)`` where
    ``attr`` is either ``"text"`` or ``"tail"`` indicating whether the string
    originated from ``elem.text`` or ``elem.tail``.
    """

    index = 0
    for file_name, tree in hwpx.content_files.items():
        for elem in tree.iter():
            if elem.text:
                yield index, file_name, elem, "text", elem.text
                index += 1
            if elem.tail:
                yield index, file_name, elem, "tail", elem.tail
                index += 1


def export_text_segments(hwpx_path: str, json_path: str) -> None:
    """Export text segments and their formatting information to ``json_path``.

    Parameters
    ----------
    hwpx_path:
        Path to the input ``.hwpx`` file.
    json_path:
        Path where the JSON array describing each segment will be written.
    """

    hwpx = HWPXReader.read(hwpx_path)

    # Build parent maps for quick lookup of run/paragraph elements.
    parent_maps = {
        name: {child: parent for parent in tree.iter() for child in parent}
        for name, tree in hwpx.content_files.items()
    }

    def _element_to_dict(elem):
        data = dict(elem.attrib)
        for child in elem:
            tag = child.tag.split('}', 1)[-1]
            if child.attrib:
                data[tag] = dict(child.attrib)
            elif child.text and child.text.strip():
                data[tag] = child.text
            else:
                data[tag] = {}
        return data

    segments = []
    for idx, file_name, elem, attr, text in enumerate_text_nodes(hwpx):
        parent_map = parent_maps[file_name]

        # Ascend the tree to find the surrounding <hp:r> and <hp:p> elements.
        parent = parent_map.get(elem)
        run = None
        paragraph = None
        while parent is not None and paragraph is None:
            tag = parent.tag
            if tag == HP_NAMESPACE + "r" and run is None:
                run = parent
            if tag == HP_NAMESPACE + "p":
                paragraph = parent
                break
            parent = parent_map.get(parent)

        phrase_id = paragraph.get("id") if paragraph is not None else None

        format_info = {"elem": dict(elem.attrib)}

        if run is not None:
            run_fmt = dict(run.attrib)
            rpr = run.find(HP_NAMESPACE + "rPr")
            if rpr is not None:
                run_fmt["rPr"] = _element_to_dict(rpr)
            format_info["run"] = run_fmt

        if paragraph is not None:
            para_fmt = dict(paragraph.attrib)
            ppr = paragraph.find(HP_NAMESPACE + "pPr")
            if ppr is not None:
                para_fmt["pPr"] = _element_to_dict(ppr)
            format_info["paragraph"] = para_fmt

        segments.append(
            {
                "index": idx,
                "file": file_name,
                "attr": attr,
                "text": text,
                "phrase_id": phrase_id,
                "format": format_info,
            }
        )

    with open(json_path, "w", encoding="utf-8") as fp:
        json.dump(segments, fp, ensure_ascii=False, indent=2)


def apply_segments(input_hwpx: str, segments_json: str, output_hwpx: str) -> None:
    """Apply text segments from ``segments_json`` to ``input_hwpx``.

    Parameters
    ----------
    input_hwpx:
        Path to the source ``.hwpx`` file.
    segments_json:
        JSON file produced by :func:`export_text_segments` describing
        replacements.  Each item must provide ``file``, ``index`` and
        ``text``.
    output_hwpx:
        Path where the modified HWPX will be written.
    """

    hwpx = HWPXReader.read(input_hwpx)

    if not hasattr(hwpx, "modified_files"):
        hwpx.modified_files = set()

    with open(segments_json, "r", encoding="utf-8") as fp:
        segments = json.load(fp)

    # Build a lookup of all text nodes keyed by (file, index).
    lookup = {
        (file_name, idx): (elem, attr)
        for idx, file_name, elem, attr, _ in enumerate_text_nodes(hwpx)
    }

    for seg in segments:
        key = (seg.get("file"), seg.get("index"))
        if key not in lookup:
            continue
        elem, attr = lookup[key]
        new_text = seg.get("text", "")
        if attr == "text":
            if elem.text != new_text:
                elem.text = new_text
                hwpx.modified_files.add(seg["file"])
        else:
            if elem.tail != new_text:
                elem.tail = new_text
                hwpx.modified_files.add(seg["file"])

    _save_modified_hwpx(hwpx, output_hwpx, input_hwpx)


def modify_hwpx_text(input_path: str, output_path: str, modifier_func) -> None:
    """HWPX 파일의 텍스트를 사용자 정의 함수로 수정합니다.
    
    Args:
        input_path: 입력 HWPX 파일 경로
        output_path: 출력 HWPX 파일 경로
        modifier_func: 텍스트를 수정하는 함수 (str -> str)
    """
    hwpx = HWPXReader.read(input_path)
    
    # 수정된 파일들을 추적하기 위한 세트 초기화
    if not hasattr(hwpx, 'modified_files'):
        hwpx.modified_files = set()
    
    # 각 section의 텍스트 수정
    for name, tree in hwpx.content_files.items():
        has_modifications = False
        for elem in tree.iter():
            if elem.text:
                original_text = elem.text
                modified_text = modifier_func(elem.text)
                if original_text != modified_text:
                    elem.text = modified_text
                    has_modifications = True
            if elem.tail:
                original_tail = elem.tail
                modified_tail = modifier_func(elem.tail)
                if original_tail != modified_tail:
                    elem.tail = modified_tail
                    has_modifications = True
        
        # 수정사항이 있으면 modified_files에 추가
        if has_modifications:
            hwpx.modified_files.add(name)
    
    _save_modified_hwpx(hwpx, output_path, input_path)


def replace_text_in_hwpx(
    input_path: str,
    output_path: str,
    search_text: str,
    replace_text: str,
    case_sensitive: bool = True
) -> int:
    """HWPX 파일에서 특정 텍스트를 찾아서 교체합니다.
    
    Args:
        input_path: 입력 HWPX 파일 경로
        output_path: 출력 HWPX 파일 경로
        search_text: 찾을 텍스트
        replace_text: 교체할 텍스트
        case_sensitive: 대소문자 구분 여부
        
    Returns:
        교체된 횟수
    """
    replace_count = 0
    
    def replacer(text: str) -> str:
        nonlocal replace_count
        if case_sensitive:
            new_text = text.replace(search_text, replace_text)
        else:
            # 대소문자 구분 없이 교체
            pattern = re.compile(re.escape(search_text), re.IGNORECASE)
            new_text = pattern.sub(replace_text, text)
        
        # 교체 횟수 계산
        if case_sensitive:
            replace_count += text.count(search_text)
        else:
            replace_count += len(pattern.findall(text))
        
        return new_text
    
    modify_hwpx_text(input_path, output_path, replacer)
    return replace_count


def get_hwpx_text_stats(file_path: str) -> Dict[str, Any]:
    """HWPX 파일의 텍스트 통계를 반환합니다.
    
    Args:
        file_path: HWPX 파일 경로
        
    Returns:
        텍스트 통계 딕셔너리
    """
    text = extract_text(file_path)
    
    return {
        "total_characters": len(text),
        "total_characters_no_spaces": len(text.replace(" ", "")),
        "total_words": len(text.split()),
        "total_lines": text.count("\n") + 1 if text else 0,
        "total_paragraphs": len([p for p in text.split("\n\n") if p.strip()]),
    }


def _save_modified_hwpx(hwpx, output_path: str, original_path: str = None) -> None:
    """수정된 HWPX 파일을 저장합니다."""

    save_modified_hwpx(hwpx, output_path, original_path)


# 편의 함수들
def uppercase_hwpx_text(input_path: str, output_path: str) -> None:
    """HWPX 파일의 모든 텍스트를 대문자로 변환합니다."""
    modify_hwpx_text(input_path, output_path, str.upper)


def lowercase_hwpx_text(input_path: str, output_path: str) -> None:
    """HWPX 파일의 모든 텍스트를 소문자로 변환합니다."""
    modify_hwpx_text(input_path, output_path, str.lower)


def remove_extra_spaces(input_path: str, output_path: str) -> None:
    """HWPX 파일에서 연속된 공백을 하나로 줄입니다."""
    def space_reducer(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip()
    
    modify_hwpx_text(input_path, output_path, space_reducer)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Usage:")
        print("  python text_modifier.py replace <input.hwpx> <output.hwpx> <search> <replace>")
        print("  python text_modifier.py upper <input.hwpx> <output.hwpx>")
        print("  python text_modifier.py lower <input.hwpx> <output.hwpx>")
        print("  python text_modifier.py stats <input.hwpx>")
        print("  python text_modifier.py export <input.hwpx> <segments.json>")
        print("  python text_modifier.py apply <input.hwpx> <segments.json> <output.hwpx>")
    else:
        command = sys.argv[1]
        input_file = sys.argv[2]

        if command == "stats":
            stats = get_hwpx_text_stats(input_file)
            print("HWPX 파일 텍스트 통계:")
            for key, value in stats.items():
                print(f"  {key}: {value:,}")
        elif command == "export" and len(sys.argv) >= 4:
            json_file = sys.argv[3]
            export_text_segments(input_file, json_file)
            print(f"텍스트 세그먼트를 {json_file} 파일로 내보냈습니다.")

        elif command == "apply" and len(sys.argv) >= 5:
            segments_file = sys.argv[3]
            output_file = sys.argv[4]
            apply_segments(input_file, segments_file, output_file)
            print(f"세그먼트를 적용하여 {output_file} 파일로 저장했습니다.")

        elif len(sys.argv) >= 4:
            output_file = sys.argv[3]

            if command == "replace" and len(sys.argv) >= 6:
                search_text = sys.argv[4]
                replace_text = sys.argv[5]
                count = replace_text_in_hwpx(input_file, output_file, search_text, replace_text)
                print(f"텍스트 교체 완료: {count}개 교체됨")

            elif command == "upper":
                uppercase_hwpx_text(input_file, output_file)
                print("대문자 변환 완료")

            elif command == "lower":
                lowercase_hwpx_text(input_file, output_file)
                print("소문자 변환 완료")

            else:
                print("알 수 없는 명령어입니다.")
