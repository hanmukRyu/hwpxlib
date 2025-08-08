#!/usr/bin/env python3
"""
압축 방식을 원본과 동일하게 유지하는 개선된 Writer
"""

import zipfile
from typing import Dict, Optional
import re

class CompatibleHwpxWriter:
    """원본 파일의 압축 방식을 유지하는 HWPX Writer"""
    
    def __init__(self, 
                 version_xml: str,
                 container_xml: str, 
                 manifest_xml: str,
                 content_hpf: str,
                 files: Dict[str, bytes],
                 mimetype: str,
                 compression_info: Optional[Dict[str, int]] = None):
        self.version_xml = version_xml
        self.container_xml = container_xml
        self.manifest_xml = manifest_xml
        self.content_hpf = content_hpf
        self.files = files
        self.mimetype = mimetype
        self.compression_info = compression_info or {}  # 파일별 압축 방식 정보
    
    def write(self, output_path: str) -> None:
        """HWPX 파일을 원본과 동일한 압축 방식으로 저장합니다."""
        
        with zipfile.ZipFile(output_path, "w") as zf:
            # 1. mimetype을 첫 번째로 압축 없이 저장
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, self.mimetype)
            
            # 2. 핵심 XML 파일들 저장
            core_files = {
                "version.xml": self.version_xml,
                "META-INF/container.xml": self.container_xml,
                "META-INF/manifest.xml": self.manifest_xml,
                "Contents/content.hpf": self.content_hpf,
            }
            
            for filename, content in core_files.items():
                # 원본의 압축 방식 사용
                compress_type = self.compression_info.get(filename, zipfile.ZIP_DEFLATED)
                
                info = zipfile.ZipInfo(filename)
                info.compress_type = compress_type
                zf.writestr(info, self._encode(content))
            
            # 3. 나머지 파일들 저장
            for filename, data in self.files.items():
                # 원본의 압축 방식 사용
                compress_type = self.compression_info.get(filename, zipfile.ZIP_DEFLATED)
                
                info = zipfile.ZipInfo(filename)
                info.compress_type = compress_type
                zf.writestr(info, self._encode(data))
    
    def _encode(self, data) -> bytes:
        """데이터를 바이트로 인코딩합니다."""
        if isinstance(data, str):
            return data.encode("utf-8")
        elif isinstance(data, bytes):
            return data
        else:
            raise TypeError(f"지원하지 않는 데이터 타입: {type(data)}")

def extract_compression_info(hwpx_file_path: str) -> Dict[str, int]:
    """원본 HWPX 파일에서 각 파일의 압축 방식 정보를 추출합니다."""
    compression_info = {}
    
    try:
        with zipfile.ZipFile(hwpx_file_path, 'r') as zf:
            for info in zf.infolist():
                compression_info[info.filename] = info.compress_type
    except Exception as e:
        print(f"압축 정보 추출 실패: {e}")
    
    return compression_info

# 수정된 저장 함수
def save_modified_hwpx_compatible(hwpx, output_path: str, original_path: str) -> None:
    """원본과 호환되는 방식으로 수정된 HWPX 파일을 저장합니다 (네임스페이스 보존)."""
    from xml.etree import ElementTree as ET
    
    # 원본 파일의 압축 정보 추출
    compression_info = extract_compression_info(original_path)
    
    # 네임스페이스 보존: 원본 XML 문자열 우선 사용, 없으면 ElementTree에서 생성
    version_xml = hwpx.original_xml_strings.get("version.xml",
        ET.tostring(hwpx.version_xml.getroot(), encoding="unicode", xml_declaration=True))
    
    container_xml = hwpx.original_xml_strings.get("META-INF/container.xml",
        ET.tostring(hwpx.container_xml.getroot(), encoding="unicode", xml_declaration=True))
    
    manifest_xml = hwpx.original_xml_strings.get("META-INF/manifest.xml",
        ET.tostring(hwpx.manifest_xml.getroot(), encoding="unicode", xml_declaration=True))
    
    content_hpf = hwpx.original_xml_strings.get("Contents/content.hpf",
        ET.tostring(hwpx.content_hpf.getroot(), encoding="unicode", xml_declaration=True))
    
    # 모든 파일을 all_files에서 시작 (복사본 생성)
    files = dict(hwpx.all_files)
    
    # 수정된 XML 파일들로 덮어쓰기 (바이너리로 저장)
    files["version.xml"] = version_xml.encode("utf-8")
    files["META-INF/container.xml"] = container_xml.encode("utf-8") 
    files["META-INF/manifest.xml"] = manifest_xml.encode("utf-8")
    files["Contents/content.hpf"] = content_hpf.encode("utf-8")
    
    # 수정된 콘텐츠 파일들 덮어쓰기 (네임스페이스 보존)
    for name, tree in hwpx.content_files.items():
        # 텍스트 수정이 있었는지 확인 (modified_files 속성 확인)
        has_text_modifications = hasattr(hwpx, 'modified_files') and name in getattr(hwpx, 'modified_files', set())
        
        if name in hwpx.original_xml_strings and not has_text_modifications:
            # 텍스트 수정이 없는 경우 원본 XML 문자열 사용 (네임스페이스 보존)
            xml_content = hwpx.original_xml_strings[name]
        else:
            # 텍스트 수정이 있거나 원본이 없는 경우 ElementTree 사용
            xml_content = ET.tostring(tree.getroot(), encoding="unicode", xml_declaration=True)
        files[name] = xml_content.encode("utf-8")
    
    # 핵심 파일들을 files에서 제거 (Writer가 별도로 처리)
    core_files = {
        "version.xml": files.pop("version.xml", b""),
        "META-INF/container.xml": files.pop("META-INF/container.xml", b""),
        "META-INF/manifest.xml": files.pop("META-INF/manifest.xml", b""),
        "Contents/content.hpf": files.pop("Contents/content.hpf", b""),
        "mimetype": files.pop("mimetype", b"")
    }
    
    # 호환 가능한 Writer로 저장
    writer = CompatibleHwpxWriter(
        version_xml=version_xml,
        container_xml=container_xml,
        manifest_xml=manifest_xml,
        content_hpf=content_hpf,
        files=files,  # 핵심 파일들 제외한 나머지 파일들
        mimetype="application/hwp+zip",
        compression_info=compression_info  # 원본 압축 정보
    )
    
    writer.write(output_path)
