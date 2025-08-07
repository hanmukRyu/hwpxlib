from __future__ import annotations

from dataclasses import dataclass
from typing import Dict
from zipfile import ZipFile


@dataclass
class HwpxArchive:
    """Representation of an ``.hwpx`` archive.

    The archive is stored as a mapping of file names to their byte contents.
    """

    files: Dict[str, bytes]

    @classmethod
    def read(cls, path: str) -> "HwpxArchive":
        """Read a ``.hwpx`` file and return an :class:`HwpxArchive`."""
        with ZipFile(path, "r") as zf:
            files = {name: zf.read(name) for name in zf.namelist()}
        return cls(files)

    def write(self, path: str) -> None:
        """Write the archive to ``path``."""
        with ZipFile(path, "w") as zf:
            for name, data in self.files.items():
                zf.writestr(name, data)


def read_hwpx(path: str) -> HwpxArchive:
    """Convenience function to read a ``.hwpx`` archive."""
    return HwpxArchive.read(path)


def write_hwpx(archive: HwpxArchive, path: str) -> None:
    """Convenience function to write a :class:`HwpxArchive` to disk."""
    archive.write(path)
