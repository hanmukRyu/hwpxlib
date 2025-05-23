package kr.dogfoot.hwpxlib.writer.header_xml;

import kr.dogfoot.hwpxlib.commonstrings.AttributeNames;
import kr.dogfoot.hwpxlib.commonstrings.ElementNames;
import kr.dogfoot.hwpxlib.commonstrings.Namespaces;
import kr.dogfoot.hwpxlib.object.common.HWPXObject;
import kr.dogfoot.hwpxlib.object.content.header_xml.BeginNum;
import kr.dogfoot.hwpxlib.object.content.header_xml.HeaderXMLFile;
import kr.dogfoot.hwpxlib.writer.common.ElementWriter;
import kr.dogfoot.hwpxlib.writer.common.ElementWriterManager;
import kr.dogfoot.hwpxlib.writer.common.ElementWriterSort;

public class HeaderWriter extends ElementWriter {
    public HeaderWriter(ElementWriterManager elementWriterManager) {
        super(elementWriterManager);
    }

    @Override
    public ElementWriterSort sort() {
        return ElementWriterSort.Header;
    }

    @Override
    public void write(HWPXObject object) {
        HeaderXMLFile headerXMLFile = (HeaderXMLFile) object;
        switchList(headerXMLFile.switchList());

        xsb()
                .clear()
                .openElement(ElementNames.hh_head)
                .elementWriter(this)
                .namespace(Namespaces.ha)
                .namespace(Namespaces.hp)
                .namespace(Namespaces.hp10)
                .namespace(Namespaces.hs)
                .namespace(Namespaces.hc)
                .namespace(Namespaces.hh)
                .namespace(Namespaces.hhs)
                .namespace(Namespaces.hm)
                .namespace(Namespaces.hpf)
                .namespace(Namespaces.dc)
                .namespace(Namespaces.opf)
                .namespace(Namespaces.ooxmlchart)
                .namespace(Namespaces.hwpunitchar)
                .namespace(Namespaces.epub)
                .namespace(Namespaces.config)
                .attribute(AttributeNames.version, headerXMLFile.version())
                .attribute(AttributeNames.secCnt, headerXMLFile.secCnt());

        if (headerXMLFile.beginNum() != null) {
            beginNum(headerXMLFile.beginNum());
        }

        if (headerXMLFile.refList() != null) {
            writeChild(ElementWriterSort.RefList, headerXMLFile.refList());
        }

        if (headerXMLFile.forbiddenWordList() != null) {
            writeChild(ElementWriterSort.ForbiddenWordList, headerXMLFile.forbiddenWordList());
        }

        if (headerXMLFile.compatibleDocument() != null) {
            writeChild(ElementWriterSort.CompatibleDocument, headerXMLFile.compatibleDocument());
        }

        if (headerXMLFile.docOption() != null) {
            writeChild(ElementWriterSort.DocOption, headerXMLFile.docOption());
        }

        if (headerXMLFile.metaTag() != null) {
            hasOnlyText(ElementNames.hh_metaTag, headerXMLFile.metaTag());
        }

        if (headerXMLFile.trackChangeConfig() != null) {
            writeChild(ElementWriterSort.TrackChangeConfig, headerXMLFile.trackChangeConfig());
        }

        xsb().closeElement();
        releaseMe();
    }

    private void beginNum(BeginNum beginNum) {
        xsb()
                .openElement(ElementNames.hh_beginNum)
                .attribute(AttributeNames.page, beginNum.page())
                .attribute(AttributeNames.footnote, beginNum.footnote())
                .attribute(AttributeNames.endnote, beginNum.endnote())
                .attribute(AttributeNames.pic, beginNum.pic())
                .attribute(AttributeNames.tbl, beginNum.tbl())
                .attribute(AttributeNames.equation, beginNum.equation())
                .closeElement();
    }

    @Override
    protected void childInSwitch(HWPXObject child) {
        switch (child._objectType()) {
            case hh_beginNum:
                beginNum((BeginNum) child);
                break;
            case hh_refList:
                writeChild(ElementWriterSort.RefList, child);
                break;
            case hh_forbiddenWordList:
                writeChild(ElementWriterSort.ForbiddenWordList, child);
                break;
            case hh_compatibleDocument:
                writeChild(ElementWriterSort.CompatibleDocument, child);
                break;
            case hh_docOption:
                writeChild(ElementWriterSort.DocOption, child);
                break;
            case hh_trackchageConfig:
                writeChild(ElementWriterSort.TrackChangeConfig, child);
                break;
        }
    }
}
