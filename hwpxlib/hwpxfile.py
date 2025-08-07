"""Python representations of the HWPX file structure.

This module provides lightweight data classes for representing the
structure of a HWPX file.  The real HWPX specification is quite
complex; these classes merely mirror the high level fields that appear
in a HWPX file and are meant to be extended as needed.  Each class
includes a :py:meth:`clone` helper that returns a deep copy of the
instance, making it convenient to duplicate files or components safely.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional
from copy import deepcopy


class CloneMixin:
    """Mixin that provides ``clone`` and ``copy`` helpers using ``deepcopy``."""

    def clone(self):
        """Return a deep copy of this instance."""
        return deepcopy(self)

    def copy(self):
        """Alias for :meth:`clone` for API familiarity."""
        return self.clone()


@dataclass
class Version(CloneMixin):
    """Version information for a HWPX file."""

    value: str = ""


@dataclass
class Manifest(CloneMixin):
    """Manifest describing included items."""

    items: List[Any] = field(default_factory=list)


@dataclass
class Container(CloneMixin):
    """Container information for packaging details."""

    data: Any = None


@dataclass
class Content(CloneMixin):
    """Primary document content."""

    data: Any = None


@dataclass
class Header(CloneMixin):
    """Document header information."""

    data: Any = None


@dataclass
class MasterPages(CloneMixin):
    """Collection of master pages."""

    pages: List[Any] = field(default_factory=list)


@dataclass
class Sections(CloneMixin):
    """Document sections."""

    sections: List[Any] = field(default_factory=list)


@dataclass
class Settings(CloneMixin):
    """Document settings."""

    options: dict = field(default_factory=dict)


@dataclass
class History(CloneMixin):
    """Revision history entries."""

    entries: List[Any] = field(default_factory=list)


@dataclass
class Charts(CloneMixin):
    """Embedded charts."""

    items: List[Any] = field(default_factory=list)


@dataclass
class HWPXFile(CloneMixin):
    """High level representation of a HWPX file."""

    version: Optional[Version] = None
    manifest: Optional[Manifest] = None
    container: Optional[Container] = None
    content: Optional[Content] = None
    header: Optional[Header] = None
    master_pages: MasterPages = field(default_factory=MasterPages)
    sections: Sections = field(default_factory=Sections)
    settings: Optional[Settings] = None
    history: History = field(default_factory=History)
    charts: Charts = field(default_factory=Charts)
    unparsed_xml: Optional[str] = None
