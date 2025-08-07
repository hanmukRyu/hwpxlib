"""Simple HWPX reader implemented in Python.

This module provides a minimal reader that understands the structure of an
HWPX file which is essentially a ZIP archive.  It mirrors a subset of the
behaviour of the Java ``HWPXReader`` in this repository.  Only a tiny portion of
that implementation is required for the tests used in this kata and therefore
only the most important features are ported.

The :func:`read` function is the main entry point.  It verifies the ``mimetype``
entry, parses well known XML files and collects binary attachments and chart
files.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional
import zipfile
from xml.etree import ElementTree as ET


MIMETYPE = "application/hwp+zip"


@dataclass
class ManifestItem:
    """Representation of an ``opf:item`` inside ``content.hpf``."""

    href: str
    media_type: str


@dataclass
class HWPXFile:
    """In memory representation of an ``.hwpx`` archive."""

    version_xml: Optional[ET.ElementTree] = None
    container_xml: Optional[ET.ElementTree] = None
    manifest_xml: Optional[ET.ElementTree] = None
    content_hpf: Optional[ET.ElementTree] = None
    content_files: Dict[str, ET.ElementTree] = field(default_factory=dict)
    binary_files: Dict[str, bytes] = field(default_factory=dict)
    charts: Dict[str, bytes] = field(default_factory=dict)


class HWPXReader:
    """High level reader for ``.hwpx`` files."""

    @staticmethod
    def read(path: str) -> HWPXFile:
        """Read a ``.hwpx`` file and return a populated :class:`HWPXFile`.

        Parameters
        ----------
        path:
            Path to the ``.hwpx`` file on disk.
        """

        with zipfile.ZipFile(path) as zf:
            _check_mimetype(zf)

            hwpx = HWPXFile()
            hwpx.version_xml = _read_xml(zf, "version.xml")
            hwpx.container_xml = _read_xml(zf, "META-INF/container.xml")
            hwpx.manifest_xml = _read_xml(zf, "META-INF/manifest.xml")

            package_path, attachments = _parse_container(hwpx.container_xml)
            for attach in attachments:
                try:
                    hwpx.binary_files[attach] = zf.read(attach)
                except KeyError:
                    pass

            if package_path:
                hwpx.content_hpf = _read_xml(zf, package_path)
                for item in _parse_content_manifest(hwpx.content_hpf):
                    if item.media_type == "application/xml":
                        tree = _read_xml(zf, item.href)
                        if tree is not None:
                            hwpx.content_files[item.href] = tree
                            _extract_charts(tree, zf, hwpx)
                    else:
                        try:
                            hwpx.binary_files[item.href] = zf.read(item.href)
                        except KeyError:
                            pass

            return hwpx


# ---------------------------------------------------------------------------
# helpers


def _check_mimetype(zf: zipfile.ZipFile) -> None:
    """Ensure the archive contains the proper ``mimetype`` entry."""

    try:
        data = zf.read("mimetype")
    except KeyError as exc:  # pragma: no cover - defensive
        raise ValueError("Not a valid HWPX file: missing mimetype") from exc

    if data.decode("utf-8").strip() != MIMETYPE:
        raise ValueError("Not a valid HWPX file: incorrect mimetype")


def _read_xml(zf: zipfile.ZipFile, name: str) -> Optional[ET.ElementTree]:
    try:
        with zf.open(name) as fp:
            return ET.parse(fp)
    except KeyError:
        return None


def _parse_container(container_xml: Optional[ET.ElementTree]) -> (Optional[str], List[str]):
    """Extract package path and attachment file paths from ``container.xml``."""

    package_path: Optional[str] = None
    attachments: List[str] = []

    if container_xml is None:
        return package_path, attachments

    root = container_xml.getroot()
    for elem in root.findall('.//{*}rootfile'):
        full_path = elem.attrib.get('full-path')
        media_type = elem.attrib.get('media-type')
        if media_type == "application/hwpml-package+xml":
            package_path = full_path
        elif full_path:
            attachments.append(full_path)

    return package_path, attachments


def _parse_content_manifest(content_hpf: Optional[ET.ElementTree]) -> List[ManifestItem]:
    items: List[ManifestItem] = []
    if content_hpf is None:
        return items

    root = content_hpf.getroot()
    for elem in root.findall('.//{*}manifest/{*}item'):
        href = elem.attrib.get('href')
        media_type = elem.attrib.get('media-type', '')
        if href:
            items.append(ManifestItem(href, media_type))
    return items


def _extract_charts(tree: ET.ElementTree, zf: zipfile.ZipFile, hwpx: HWPXFile) -> None:
    """Locate chart references in ``tree`` and load their binary data."""

    for elem in tree.iter():
        chart_ref = elem.attrib.get('chartIDRef')
        if chart_ref and chart_ref not in hwpx.charts:
            try:
                hwpx.charts[chart_ref] = zf.read(chart_ref)
            except KeyError:
                # Missing chart is not fatal – ignore silently like Java version.
                pass
