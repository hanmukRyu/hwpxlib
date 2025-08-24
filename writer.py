import logging
import zipfile
from typing import Dict, Union, Optional
from xml.etree import ElementTree as ET

from reader import MIMETYPE

FileContent = Union[str, bytes]

class HwpxWriter:
    """Create an HWPX package and write it as a ZIP archive."""

    def __init__(
        self,
        version_xml: str,
        container_xml: str,
        manifest_xml: str,
        content_hpf: str,
        files: Dict[str, FileContent],
        mimetype: str = "application/haansofthwp",
    ) -> None:
        self.version_xml = version_xml
        self.container_xml = container_xml
        self.manifest_xml = manifest_xml
        self.content_hpf = content_hpf
        self.files = files
        self.mimetype = mimetype

    def _encode(self, data: FileContent) -> bytes:
        """Encode XML strings as UTF-8."""
        if isinstance(data, bytes):
            return data
        return data.encode("utf-8")

    def write(self, output: str) -> None:
        """Write a new HWPX file to *output*.

        The writer stores the mimetype file uncompressed as the first
        entry, then writes mandatory XML files followed by any referenced
        or additional XML/binary files such as chart XML or attachments.
        """

        # Determine files referenced by the content manifest.
        referenced = set()
        try:
            tree = ET.fromstring(self.content_hpf)
            ns = {"opf": "http://www.idpf.org/2007/opf"}
            for item in tree.findall(".//opf:item", ns):
                href = item.get("href")
                if href:
                    referenced.add(href)
        except ET.ParseError:
            # If content_hpf is malformed we simply skip reference parsing.
            referenced = set()

        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as zf:
            # Store mimetype uncompressed as first entry.
            info = zipfile.ZipInfo("mimetype")
            info.compress_type = zipfile.ZIP_STORED
            zf.writestr(info, self.mimetype)

            # Core package files.
            zf.writestr("version.xml", self._encode(self.version_xml))
            zf.writestr("META-INF/container.xml", self._encode(self.container_xml))
            zf.writestr("META-INF/manifest.xml", self._encode(self.manifest_xml))
            zf.writestr("Contents/content.hpf", self._encode(self.content_hpf))

            # Referenced files from manifest.
            for path in referenced:
                if path not in self.files:
                    raise KeyError(f"Referenced file '{path}' not provided")
                zf.writestr(path, self._encode(self.files[path]))

            # Any remaining files (charts, attachments, etc.).
            for path, data in self.files.items():
                if path in referenced:
                    continue
                zf.writestr(path, self._encode(data))


def _register_hwpx_namespaces() -> None:
    """Register HWPX and common namespaces to preserve prefixes."""
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

    ET.register_namespace('dc', 'http://purl.org/dc/elements/1.1/')
    ET.register_namespace('config', 'urn:oasis:names:tc:opendocument:xmlns:config:1.0')
    ET.register_namespace('epub', 'http://www.idpf.org/2007/ops')
    ET.register_namespace('opf', 'http://www.idpf.org/2007/opf/')
    ET.register_namespace('ocf', 'urn:oasis:names:tc:opendocument:xmlns:container')
    ET.register_namespace('odf', 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0')


def save_modified_hwpx(hwpx, output_path: str, original_path: Optional[str] = None,
                       use_compatible: bool = True) -> None:
    """Save a modified HWPX file while preserving namespaces and compression."""

    _register_hwpx_namespaces()

    if use_compatible and original_path:
        try:
            from compatible_writer import save_modified_hwpx_compatible
            print(f"[DEBUG] compatible_writer 호출 시작")
            print(f"[DEBUG] modified_files: {getattr(hwpx, 'modified_files', set())}")
            save_modified_hwpx_compatible(hwpx, output_path, original_path)
            print(f"[DEBUG] compatible_writer 호출 완료")
            return
        except ImportError:
            logging.debug("compatible_writer not available; falling back to ZIP writer")
        except Exception as exc:  # pragma: no cover - defensive
            logging.warning("compatible writer failed: %s", exc)
            print(f"[DEBUG] compatible_writer 실패: {exc}")

    # Determine original XML strings or serialize trees
    version_xml = hwpx.original_xml_strings.get(
        "version.xml",
        ET.tostring(hwpx.version_xml.getroot(), encoding="utf-8", xml_declaration=True).decode("utf-8"),
    )
    container_xml = hwpx.original_xml_strings.get(
        "META-INF/container.xml",
        ET.tostring(hwpx.container_xml.getroot(), encoding="utf-8", xml_declaration=True).decode("utf-8"),
    )
    manifest_xml = hwpx.original_xml_strings.get(
        "META-INF/manifest.xml",
        ET.tostring(hwpx.manifest_xml.getroot(), encoding="utf-8", xml_declaration=True).decode("utf-8"),
    )
    content_hpf = hwpx.original_xml_strings.get(
        "Contents/content.hpf",
        ET.tostring(hwpx.content_hpf.getroot(), encoding="utf-8", xml_declaration=True).decode("utf-8"),
    )

    compression_info: Dict[str, int] = {}
    if original_path:
        try:
            with zipfile.ZipFile(original_path, 'r') as orig_zf:
                for info in orig_zf.infolist():
                    compression_info[info.filename] = info.compress_type
        except Exception as exc:  # pragma: no cover - defensive
            logging.warning("Error reading compression info: %s", exc)

    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        info = zipfile.ZipInfo("mimetype")
        info.compress_type = zipfile.ZIP_STORED
        zf.writestr(info, MIMETYPE)

        for filename, content in [
            ("version.xml", version_xml),
            ("META-INF/container.xml", container_xml),
            ("META-INF/manifest.xml", manifest_xml),
            ("Contents/content.hpf", content_hpf),
        ]:
            info = zipfile.ZipInfo(filename)
            info.compress_type = compression_info.get(filename, zipfile.ZIP_DEFLATED)
            zf.writestr(info, content.encode("utf-8"))

        processed = {
            "mimetype",
            "version.xml",
            "META-INF/container.xml",
            "META-INF/manifest.xml",
            "Contents/content.hpf",
        }

        for name, tree in hwpx.content_files.items():
            print(f"[DEBUG writer.py] 파일 {name} 처리 중...")
            if hasattr(hwpx, 'modified_files') and name in getattr(hwpx, 'modified_files', set()):
                xml_content = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)
                print(f"[DEBUG writer.py] {name}: 수정됨 - ElementTree 사용")
            elif name in hwpx.original_xml_strings:
                xml_content = hwpx.original_xml_strings[name].encode("utf-8")
                print(f"[DEBUG writer.py] {name}: 수정 안됨 - 원본 XML 사용")
            else:
                xml_content = ET.tostring(tree.getroot(), encoding="utf-8", xml_declaration=True)
                print(f"[DEBUG writer.py] {name}: 기본 - ElementTree 사용")

            info = zipfile.ZipInfo(name)
            info.compress_type = compression_info.get(name, zipfile.ZIP_DEFLATED)
            zf.writestr(info, xml_content)
            processed.add(name)

        for filename, data in hwpx.all_files.items():
            if filename not in processed:
                info = zipfile.ZipInfo(filename)
                info.compress_type = compression_info.get(filename, zipfile.ZIP_DEFLATED)
                zf.writestr(info, data)

