"""HWPX 파일의 텍스트를 수정하는 유틸리티 함수들.

이 모듈은 HWPX 파일에서 텍스트를 읽고 수정한 뒤 저장하는 고수준 API를 제공합니다.
가능하다면 :mod:`compatible_writer` 의 저장 함수를 사용하고, 그렇지 않으면 ZIP 기반
로직으로 직접 저장하여 네임스페이스를 보존합니다. `reader` 와
`text_extractor` 모듈을 조합하여 사용합니다.

추가로, 문서의 모든 텍스트 노드를 순회하여 인덱스와 함께 열거하거나, 특정
인덱스의 텍스트만 선택적으로 교체하는 고급 기능을 제공합니다. 이는 문장 단위의
세밀한 수정 작업을 수행할 때 유용합니다.

사용 예::

    from text_modifier import list_sentences, modify_selected_text

    list_sentences("input.hwpx")  # 각 문장의 인덱스를 확인

    replacements = {
        3: "세 번째 문장을 새로 작성합니다.",
    }
    modify_selected_text("input.hwpx", "output.hwpx", replacements)
"""

from typing import Callable, Dict, Any, Iterable, Tuple, Union
import re

from reader import HWPXReader
from text_extractor import extract_text
from writer import save_modified_hwpx

HP_NAMESPACE = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def enumerate_text_nodes(hwpx) -> Iterable[Tuple[int, str, Any, str, str]]:
    """Yield all text nodes from ``hwpx`` in reading order.

    Parameters
    ----------
    hwpx:
        :class:`reader.HWPXFile` 객체. ``HWPXReader.read`` 로 획득한다.

    Yields
    ------
    ``(index, file_name, element, attr_name, text)`` 튜플
        ``element`` 는 :mod:`xml.etree.ElementTree` 의 요소이며, ``attr_name`` 은
        ``"text"`` 또는 ``"tail"`` 이다. ``index`` 는 문서 전반에서의 순번이다.
    """

    idx = 0
    for file_name, tree in hwpx.content_files.items():
        for elem in tree.iter():
            if elem.text is not None:
                yield idx, file_name, elem, "text", elem.text
                idx += 1
            if elem.tail is not None:
                yield idx, file_name, elem, "tail", elem.tail
                idx += 1

# Note: helper functions `_modify_text_preserve_formatting` and
# `_modify_text_simple` were removed. If future features require them,
# they can be restored from the Git history.


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


def modify_selected_text(
    input_path: str,
    output_path: str,
    replacements: Dict[Union[int, Tuple[str, int]], Union[str, Callable[[str], str]]],
) -> int:
    """선택된 인덱스의 텍스트만 교체합니다.

    ``replacements`` 딕셔너리는 전역 인덱스 ``int`` 또는 ``(file_name, index)``
    튜플을 키로 사용하며, 값으로는 교체할 문자열 또는 콜백 함수를 지정합니다.
    콜백 함수는 기존 문자열을 인자로 받아 새 문자열을 반환해야 합니다.

    Returns
    -------
    int
        실제로 변경된 텍스트 노드 수
    """

    hwpx = HWPXReader.read(input_path)

    if not hasattr(hwpx, "modified_files"):
        hwpx.modified_files = set()

    modified_count = 0

    for idx, file_name, elem, attr, text in enumerate_text_nodes(hwpx):
        key = (file_name, idx)
        repl = None
        if key in replacements:
            repl = replacements[key]
        elif idx in replacements:
            repl = replacements[idx]
        if repl is None:
            continue

        new_text = repl(text) if callable(repl) else repl
        if new_text != text:
            setattr(elem, attr, new_text)
            hwpx.modified_files.add(file_name)
            modified_count += 1

    _save_modified_hwpx(hwpx, output_path, input_path)
    return modified_count


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


def list_sentences(file_path: str) -> None:
    """문서의 모든 문장을 인덱스와 함께 출력합니다."""

    hwpx = HWPXReader.read(file_path)
    for idx, _file, _elem, _attr, text in enumerate_text_nodes(hwpx):
        print(f"{idx}: {text}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python text_modifier.py list <input.hwpx>")
        print("  python text_modifier.py stats <input.hwpx>")
        print("  python text_modifier.py replace <input.hwpx> <output.hwpx> <search> <replace>")
        print("  python text_modifier.py upper <input.hwpx> <output.hwpx>")
        print("  python text_modifier.py lower <input.hwpx> <output.hwpx>")
    else:
        command = sys.argv[1]

        if command == "list" and len(sys.argv) >= 3:
            list_sentences(sys.argv[2])

        elif command == "stats" and len(sys.argv) >= 3:
            input_file = sys.argv[2]
            stats = get_hwpx_text_stats(input_file)
            print("HWPX 파일 텍스트 통계:")
            for key, value in stats.items():
                print(f"  {key}: {value:,}")

        elif len(sys.argv) >= 4:
            input_file = sys.argv[2]
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

        else:
            print("알 수 없는 명령어입니다.")
