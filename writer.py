import zipfile
from typing import Dict, Union
from xml.etree import ElementTree as ET

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
