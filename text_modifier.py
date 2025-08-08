"""HWPX 파일의 텍스트를 수정하는 유틸리티 함수들

이 모듈은 HWPX 파일에서 텍스트를 읽고, 수정하고, 저장하는 고수준 API를 제공합니다.
기존의 reader, writer, text_extractor 모듈들을 조합하여 사용합니다.
"""

from typing import Callable, Optional, Dict, Any
import xml.etree.ElementTree as ET
from xml.etree import ElementTree
import re

from reader import HWPXReader, MIMETYPE
from writer import HwpxWriter
from text_extractor import extract_text

HP_NAMESPACE = "{http://www.hancom.co.kr/hwpml/2011/paragraph}"


def _register_hwpx_namespaces():
    """HWPX 파일에서 사용되는 네임스페이스들을 등록하여 prefix를 보존합니다."""
    # 한글 HWPX 네임스페이스들
    ET.register_namespace('ha', 'http://www.hancom.co.kr/hwpml/2011/app')
    ET.register_namespace('hp', 'http://www.hancom.co.kr/hwpml/2011/paragraph')
    ET.register_namespace('hp10', 'http://www.hancom.co.kr/hwpml/2016/paragraph')
    ET.register_namespace('hs', 'http://www.hancom.co.kr/hwpml/2011/section')
    ET.register_namespace('hc', 'http://www.hancom.co.kr/hwpml/2011/core')
    ET.register_namespace('hh', 'http://www.hancom.co.kr/hwpml/2011/head')
    ET.register_namespace('hhs', 'http://www.hancom.co.kr/hwpml/2011/history')
    ET.register_namespace('hm', 'http://www.hancom.co.kr/hwpml/2011/master-page')
    ET.register_namespace('hpf', 'http://www.hancom.co.kr/schema/2011/hpf')
    ET.register_namespace('hv', 'http://www.hancom.co.kr/hwpml/2011/version')
    ET.register_namespace('hwpunitchar', 'http://www.hancom.co.kr/hwpml/2016/HwpUnitChar')
    ET.register_namespace('ooxmlchart', 'http://www.hancom.co.kr/hwpml/2016/ooxmlchart')
    
    # 표준 네임스페이스들
    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
    ET.register_namespace('config', 'urn:oasis:names:tc:opendocument:xmlns:config:1.0')
    ET.register_namespace('epub', 'http://www.idpf.org/2007/ops')
    ET.register_namespace('opf', 'http://www.idpf.org/2007/opf/')
    ET.register_namespace('ocf', 'urn:oasis:names:tc:opendocument:xmlns:container')
    ET.register_namespace('odf', 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0')


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


def _modify_text_preserve_formatting(hwpx, text_modifier: Callable[[str], str]) -> None:
    """서식을 보존하면서 텍스트를 수정합니다."""
    for file_path, tree in hwpx.content_files.items():
        if file_path.startswith("Contents/section") and file_path.endswith(".xml"):
            root = tree.getroot()
            
            # 모든 텍스트 요소 찾기 및 수정
            for t_elem in root.iter(HP_NAMESPACE + "t"):
                if t_elem.text:
                    original_text = t_elem.text
                    modified_text = text_modifier(original_text)
                    t_elem.text = modified_text


def _modify_text_simple(hwpx, text_modifier: Callable[[str], str]) -> None:
    """간단한 텍스트 수정 (전체 텍스트를 한번에 처리)"""
    # 전체 텍스트 추출
    all_text = ""
    for file_path, tree in hwpx.content_files.items():
        if file_path.startswith("Contents/section") and file_path.endswith(".xml"):
            root = tree.getroot()
            for t_elem in root.iter(HP_NAMESPACE + "t"):
                if t_elem.text:
                    all_text += t_elem.text
    
    # 텍스트 수정
    modified_text = text_modifier(all_text)
    
    # 첫 번째 텍스트 요소에만 수정된 텍스트 배치, 나머지는 제거
    first_found = False
    for file_path, tree in hwpx.content_files.items():
        if file_path.startswith("Contents/section") and file_path.endswith(".xml"):
            root = tree.getroot()
            for t_elem in root.iter(HP_NAMESPACE + "t"):
                if t_elem.text:
                    if not first_found:
                        t_elem.text = modified_text
                        first_found = True
                    else:
                        t_elem.text = ""


def _save_modified_hwpx(hwpx, output_path: str, original_path: str = None) -> None:
    """수정된 HWPX 파일을 저장합니다 (네임스페이스 보존)."""
    
    # 한글 HWPX 네임스페이스 등록 (prefix 보존)
    _register_hwpx_namespaces()
    
    # 호환성 개선 Writer 사용 (네임스페이스 보존 기능 포함)
    if original_path:
        try:
            from compatible_writer import save_modified_hwpx_compatible
            save_modified_hwpx_compatible(hwpx, output_path, original_path)
            return
        except ImportError:
            pass
    
    # 개선된 방식: 원본 XML 문자열 사용 (네임스페이스 보존)
    # 수정되지 않은 XML들은 원본 문자열 사용, 수정된 것들만 새로 생성
    version_xml = hwpx.original_xml_strings.get("version.xml", 
        ET.tostring(hwpx.version_xml.getroot(), encoding="utf-8", xml_declaration=True).decode('utf-8'))
    
    container_xml = hwpx.original_xml_strings.get("META-INF/container.xml",
        ET.tostring(hwpx.container_xml.getroot(), encoding="utf-8", xml_declaration=True).decode('utf-8'))
    
    manifest_xml = hwpx.original_xml_strings.get("META-INF/manifest.xml",
        ET.tostring(hwpx.manifest_xml.getroot(), encoding="utf-8", xml_declaration=True).decode('utf-8'))
    
    content_hpf = hwpx.original_xml_strings.get("Contents/content.hpf",
        ET.tostring(hwpx.content_hpf.getroot(), encoding="utf-8", xml_declaration=True).decode('utf-8'))
    
    # HwpxWriter를 사용하지 않고 직접 ZIP 파일 생성 (네임스페이스 보존)
    import zipfile
    
    # 원본 파일의 압축 설정 추출
    compression_info = {}
    if original_path:
        try:
            with zipfile.ZipFile(original_path, 'r') as orig_zf:
                for info in orig_zf.infolist():
                    compression_info[info.filename] = info.compress_type
        except:
            pass
    
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Store mimetype uncompressed as first entry.
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        zf.writestr(info, MIMETYPE)

        # Core package files (원본 문자열 사용하고 원본 압축 설정 유지).
        for filename, content in [
            ("version.xml", version_xml),
            ("META-INF/container.xml", container_xml),
            ("META-INF/manifest.xml", manifest_xml),
            ("Contents/content.hpf", content_hpf)
        ]:
            info = zipfile.ZipInfo(filename)
            info.compress_type = compression_info.get(filename, zipfile.ZIP_DEFLATED)
            zf.writestr(info, content.encode("utf-8"))

        # 수정된 콘텐츠 파일들과 기타 파일들
        processed_files = {
            "mimetype", "version.xml", "META-INF/container.xml", 
            "META-INF/manifest.xml", "Contents/content.hpf"
        }
        
        # 수정된 콘텐츠 파일들 (section XML들)
        for name, tree in hwpx.content_files.items():
            # 수정된 파일인지 확인
            if hasattr(hwpx, 'modified_files') and name in hwpx.modified_files:
                # 수정된 파일은 새로 직렬화 (네임스페이스 prefix 보존)
                xml_content = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)
            elif name in hwpx.original_xml_strings:
                # 수정되지 않은 파일은 원본 문자열 사용
                xml_content = hwpx.original_xml_strings[name].encode('utf-8')
            else:
                # 원본 문자열이 없으면 새로 직렬화
                xml_content = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)
            
            info = zipfile.ZipInfo(name)
            info.compress_type = compression_info.get(name, zipfile.ZIP_DEFLATED)
            zf.writestr(info, xml_content)
            processed_files.add(name)

        # 나머지 파일들 (바이너리 파일들, 차트, 설정 등) - 원본 그대로
        for filename, data in hwpx.all_files.items():
            if filename not in processed_files:
                info = zipfile.ZipInfo(filename)
                info.compress_type = compression_info.get(filename, zipfile.ZIP_DEFLATED)
                zf.writestr(info, data)


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
    else:
        command = sys.argv[1]
        input_file = sys.argv[2]
        
        if command == "stats":
            stats = get_hwpx_text_stats(input_file)
            print("HWPX 파일 텍스트 통계:")
            for key, value in stats.items():
                print(f"  {key}: {value:,}")
        
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
