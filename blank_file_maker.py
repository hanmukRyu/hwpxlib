from zipfile import ZipFile, ZIP_DEFLATED
from datetime import datetime

MIMETYPE = "application/hwp+zip"

VERSION_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<hv:HCFVersion xmlns:hv=\"http://www.hancom.co.kr/hwpml/2011/version\" "
    "targetApplication=\"WORDPROCESSOR\" major=\"5\" minor=\"0\" micro=\"5\" "
    "buildNumber=\"0\" xmlVersion=\"1.4\" application=\"hwpxlib\" appVersion=\"unknown\"/>"
)

MANIFEST_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<odf:manifest xmlns:odf=\"urn:oasis:names:tc:opendocument:xmlns:manifest:1.0\"/>"
)

CONTAINER_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<ocf:container xmlns:ocf=\"urn:oasis:names:tc:opendocument:xmlns:container\" "
    "xmlns:hpf=\"http://www.hancom.co.kr/schema/2011/hpf\">"
    "<ocf:rootfiles><ocf:rootfile full-path=\"Contents/content.hpf\" "
    "media-type=\"application/hwpml-package+xml\"/></ocf:rootfiles></ocf:container>"
)

HEADER_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<hh:head xmlns:ha=\"http://www.hancom.co.kr/hwpml/2011/app\" "
    "xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\"><hh:mainInfo/></hh:head>"
)

SECTION_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<hs:sec xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" "
    "xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\">"
    "<hp:p><hp:run><hp:t/></hp:run></hp:p></hs:sec>"
)

SETTINGS_XML = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<ha:HWPApplicationSetting xmlns:ha=\"http://www.hancom.co.kr/hwpml/2011/app\" "
    "xmlns:config=\"urn:oasis:names:tc:opendocument:xmlns:config:1.0\">"
    "<ha:CaretPosition listIDRef=\"0\" paraIDRef=\"0\" pos=\"0\"/></ha:HWPApplicationSetting>"
)

CONTENT_TEMPLATE = (
    "<?xml version=\"1.0\" encoding=\"UTF-8\" standalone=\"yes\" ?>"
    "<opf:package xmlns:ha=\"http://www.hancom.co.kr/hwpml/2011/app\" "
    "xmlns:hp=\"http://www.hancom.co.kr/hwpml/2011/paragraph\" "
    "xmlns:hs=\"http://www.hancom.co.kr/hwpml/2011/section\" "
    "xmlns:opf=\"http://www.idpf.org/2007/opf/\" version=\"\" unique-identifier=\"\">"
    "<opf:metadata><opf:title/><opf:language>ko</opf:language>"
    "<opf:meta name=\"CreatedDate\" content=\"{now}\"/>"
    "<opf:meta name=\"ModifiedDate\" content=\"{now}\"/></opf:metadata>"
    "<opf:manifest><opf:item id=\"header\" href=\"Contents/header.xml\" media-type=\"application/xml\"/>"
    "<opf:item id=\"section0\" href=\"Contents/section0.xml\" media-type=\"application/xml\"/>"
    "<opf:item id=\"settings\" href=\"settings.xml\" media-type=\"application/xml\"/></opf:manifest>"
    "<opf:spine><opf:itemref idref=\"header\"/><opf:itemref idref=\"section0\"/></opf:spine></opf:package>"
)

def make_blank(path: str) -> None:
    """Create a minimal HWPX file at the given path."""
    now = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    content_hpf = CONTENT_TEMPLATE.format(now=now)
    with ZipFile(path, "w", ZIP_DEFLATED) as zf:
        zf.writestr("mimetype", MIMETYPE)
        zf.writestr("version.xml", VERSION_XML)
        zf.writestr("META-INF/manifest.xml", MANIFEST_XML)
        zf.writestr("META-INF/container.xml", CONTAINER_XML)
        zf.writestr("Contents/content.hpf", content_hpf)
        zf.writestr("Contents/header.xml", HEADER_XML)
        zf.writestr("Contents/section0.xml", SECTION_XML)
        zf.writestr("settings.xml", SETTINGS_XML)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python blank_file_maker.py <output.hwpx>")
    else:
        make_blank(sys.argv[1])
