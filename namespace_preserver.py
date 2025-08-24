"""XML 네임스페이스 보존을 위한 유틸리티 모듈.

이 모듈은 HWPX XML 파일의 원본 네임스페이스를 요소별로 보존하고,
수정 시 원본 네임스페이스를 복원하는 기능을 제공합니다.
"""

import re
from typing import Dict, Tuple, Optional, Any
from xml.etree import ElementTree as ET
import logging

logger = logging.getLogger(__name__)


def extract_element_namespace_info(elem: ET.Element) -> Dict[str, Any]:
    """XML 요소의 네임스페이스 정보를 추출합니다.
    
    Args:
        elem: XML 요소
        
    Returns:
        네임스페이스 정보를 담은 딕셔너리
    """
    namespace_info = {
        'tag': elem.tag,
        'attrib': dict(elem.attrib),
        'nsmap': {}
    }
    
    # 태그에서 네임스페이스 추출
    if elem.tag.startswith('{'):
        namespace, local_name = elem.tag[1:].split('}', 1)
        namespace_info['namespace'] = namespace
        namespace_info['local_name'] = local_name
    else:
        namespace_info['namespace'] = None
        namespace_info['local_name'] = elem.tag
    
    # 속성에서 xmlns 선언 추출
    for key, value in elem.attrib.items():
        if key.startswith('xmlns'):
            if ':' in key:
                # xmlns:prefix="uri" 형태
                prefix = key.split(':', 1)[1]
                namespace_info['nsmap'][prefix] = value
            else:
                # xmlns="uri" 형태 (기본 네임스페이스)
                namespace_info['nsmap'][''] = value
    
    return namespace_info


def get_element_xml_string(elem: ET.Element, encoding: str = 'unicode') -> str:
    """요소의 원본 XML 문자열을 생성합니다.
    
    Args:
        elem: XML 요소
        encoding: 인코딩 방식
        
    Returns:
        XML 문자열
    """
    return ET.tostring(elem, encoding=encoding, method='xml')


def preserve_element_with_namespace(elem: ET.Element, namespace_info: Dict[str, Any]) -> ET.Element:
    """네임스페이스 정보를 사용하여 요소를 재구성합니다.
    
    Args:
        elem: 수정할 XML 요소
        namespace_info: 보존된 네임스페이스 정보
        
    Returns:
        네임스페이스가 복원된 요소
    """
    # 원본 태그와 속성으로 새 요소 생성
    new_elem = ET.Element(namespace_info['tag'])
    
    # 원본 속성 복원
    for key, value in namespace_info['attrib'].items():
        new_elem.set(key, value)
    
    # xmlns 선언 복원
    for prefix, uri in namespace_info.get('nsmap', {}).items():
        if prefix:
            new_elem.set(f'xmlns:{prefix}', uri)
        else:
            new_elem.set('xmlns', uri)
    
    # 텍스트와 꼬리 복사
    new_elem.text = elem.text
    new_elem.tail = elem.tail
    
    # 자식 요소들 복사
    for child in elem:
        new_elem.append(child)
    
    return new_elem


def create_namespace_preserving_writer(original_xml: str) -> Tuple[Dict[int, Dict[str, Any]], Dict[str, str]]:
    """원본 XML에서 네임스페이스 정보를 추출하여 보존합니다.
    
    Args:
        original_xml: 원본 XML 문자열
        
    Returns:
        (요소 인덱스별 네임스페이스 정보, 전역 네임스페이스 맵)
    """
    element_namespaces = {}
    global_nsmap = {}
    
    try:
        root = ET.fromstring(original_xml)
        
        # 루트 요소의 네임스페이스 추출
        root_ns_info = extract_element_namespace_info(root)
        global_nsmap.update(root_ns_info.get('nsmap', {}))
        
        # 모든 요소의 네임스페이스 정보 수집
        index = 0
        for elem in root.iter():
            ns_info = extract_element_namespace_info(elem)
            element_namespaces[index] = ns_info
            
            # 새로운 네임스페이스 선언이 있으면 전역 맵에 추가
            for prefix, uri in ns_info.get('nsmap', {}).items():
                if prefix not in global_nsmap:
                    global_nsmap[prefix] = uri
            
            index += 1
            
    except ET.ParseError as e:
        logger.error(f"XML 파싱 오류: {e}")
        
    return element_namespaces, global_nsmap


def apply_namespace_to_modified_xml(modified_tree: ET.ElementTree, 
                                   element_namespaces: Dict[int, Dict[str, Any]],
                                   global_nsmap: Dict[str, str]) -> str:
    """수정된 XML 트리에 원본 네임스페이스를 적용합니다.
    
    Args:
        modified_tree: 수정된 XML 트리
        element_namespaces: 요소별 네임스페이스 정보
        global_nsmap: 전역 네임스페이스 맵
        
    Returns:
        네임스페이스가 복원된 XML 문자열
    """
    # 네임스페이스 등록
    for prefix, uri in global_nsmap.items():
        if prefix:
            ET.register_namespace(prefix, uri)
        else:
            # 기본 네임스페이스
            ET.register_namespace('', uri)
    
    # XML 문자열로 변환
    xml_str = ET.tostring(modified_tree.getroot(), encoding='unicode', xml_declaration=True)
    
    # 네임스페이스 접두사 복원 (정규식 사용)
    for prefix, uri in global_nsmap.items():
        if prefix:
            # ns0:tag -> prefix:tag 형태로 변경
            xml_str = re.sub(r'\bns\d+:', f'{prefix}:', xml_str)
    
    return xml_str


def preserve_original_xml_line(xml_line: str) -> Dict[str, Any]:
    """XML 라인의 원본 형태를 보존합니다.
    
    Args:
        xml_line: 원본 XML 라인
        
    Returns:
        라인 정보를 담은 딕셔너리
    """
    line_info = {
        'original': xml_line,
        'namespaces': {},
        'prefixes': []
    }
    
    # xmlns 선언 추출
    xmlns_pattern = r'xmlns(?::(\w+))?="([^"]+)"'
    for match in re.finditer(xmlns_pattern, xml_line):
        prefix = match.group(1) or ''
        uri = match.group(2)
        line_info['namespaces'][prefix] = uri
    
    # 사용된 네임스페이스 접두사 추출
    prefix_pattern = r'</?(\w+):'
    for match in re.finditer(prefix_pattern, xml_line):
        prefix = match.group(1)
        if prefix not in line_info['prefixes']:
            line_info['prefixes'].append(prefix)
    
    return line_info


def restore_xml_line_namespaces(modified_line: str, line_info: Dict[str, Any]) -> str:
    """수정된 XML 라인에 원본 네임스페이스를 복원합니다.
    
    Args:
        modified_line: 수정된 XML 라인
        line_info: 원본 라인 정보
        
    Returns:
        네임스페이스가 복원된 XML 라인
    """
    result = modified_line
    
    # ns0, ns1 등을 원본 접두사로 변경
    for i, prefix in enumerate(line_info.get('prefixes', [])):
        result = re.sub(f'\\bns{i}:', f'{prefix}:', result)
    
    # xmlns 선언 복원
    for prefix, uri in line_info.get('namespaces', {}).items():
        if prefix:
            xmlns_decl = f'xmlns:{prefix}="{uri}"'
        else:
            xmlns_decl = f'xmlns="{uri}"'
        
        # 선언이 없으면 추가
        if xmlns_decl not in result:
            # 첫 번째 태그에 추가
            result = re.sub(r'(<\w+[^>]*)(>)', rf'\1 {xmlns_decl}\2', result, count=1)
    
    return result