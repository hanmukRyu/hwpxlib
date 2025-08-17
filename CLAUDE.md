# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Common Development Commands

### Testing
```bash
# Run individual test files
cd tests
python step1_validate_originals.py   # Validate original HWPX files
python step2_test_reader.py          # Test HWPXReader functionality
python step3_test_writer.py          # Test HwpxWriter functionality
python final_test.py                 # Run comprehensive tests

# Run specific functional tests
python test_reader_writer.py         # Basic read/write functionality
python test_roundtrip.py            # Roundtrip testing
python test_export_segments.py      # Test segment export
python test_apply_segments.py       # Test segment application
```

### Text Modifier CLI
```bash
# Export text segments from HWPX to JSON
python text_modifier.py export input.hwpx output.json

# Apply modified segments back to HWPX
python text_modifier.py apply input.hwpx segments.json output.hwpx

# Delete specific XML elements from HWPX
python text_modifier.py delete input.hwpx output.hwpx --elements elem1 elem2
```

### Installation
```bash
pip install -e .  # Install in development mode
```

## Architecture Overview

This is a Python library for reading, writing, and modifying HWPX files (Korean Hangul Word Processor format). HWPX files are ZIP archives containing XML documents that define document structure and content.

### Core Components

1. **hwpxlib/archive.py** - `HwpxArchive` class provides Python-style interface mimicking Java Reader/Writer
2. **reader.py** - `HWPXReader` class for parsing HWPX ZIP archives and loading XML content
3. **writer.py** - `HwpxWriter` and `save_modified_hwpx` for creating/modifying HWPX files
4. **compatible_writer.py** - Alternative writer that preserves Hangul program compatibility
5. **text_extractor.py** - Simple text extraction utilities
6. **text_modifier.py** - Advanced text segment extraction/modification with formatting preservation

### Key Data Structures

**HWPX File Structure:**
- ZIP archive containing XML files in `Contents/` directory
- Main content in `Contents/section0.xml`, `Contents/section1.xml`, etc.
- Metadata in `version.xml`, `container.xml`, `content.hpf`, `manifest.xml`
- Binary attachments in `BinData/` directory

**Text Segments JSON Format:**
```json
{
  "index": 0,
  "file": "Contents/section0.xml",
  "attr": "text",
  "text": "Hello",
  "phrase_id": "0",
  "format": {
    "elem": {},
    "run": {},
    "paragraph": {}
  }
}
```

### Processing Flow

1. **Reading:** HWPX ZIP → Extract XML files → Parse with ElementTree → HWPXFile object
2. **Text Extraction:** Iterate XML elements → Extract text/tail → Build segment list
3. **Modification:** Load segments → Apply text changes → Preserve formatting
4. **Writing:** Modified XML trees → Repackage as ZIP → Save as HWPX

### Namespace Handling

The library handles multiple XML namespaces:
- `hp`: `http://www.hancom.co.kr/hwpml/2011/paragraph` (paragraphs)
- `hh`: `http://www.hancom.co.kr/hwpml/2011/head` (headers)
- `hc`: `http://www.hancom.co.kr/hwpml/2011/core` (core elements)

### Test Structure

Tests are organized in steps for progressive validation:
- `step1-3`: Core reader/writer functionality
- `step4-7`: Advanced features and compatibility
- `test_*.py`: Functional tests for specific features
- Test data in `testFile/reader_writer/` includes various document types

## Python-Java Compatibility

This Python implementation provides a simplified interface compatible with the original Java library design, focusing on core read/write operations while maintaining file format integrity.