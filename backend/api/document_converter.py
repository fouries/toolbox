import html
import re
from html.parser import HTMLParser
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, List

from docx import Document
from docx.shared import Inches
from fastapi import UploadFile
from PIL import Image, ImageOps
from pypdf import PdfReader
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer


IMAGE_INPUTS = {"jpg", "jpeg", "png", "webp"}
SUPPORTED_INPUTS = {"txt", "html", "htm", "docx", "pdf", *IMAGE_INPUTS}
SUPPORTED_TARGETS = {"txt", "html", "docx", "pdf"}
TARGET_ALIASES = {"word": "docx", "text": "txt", "htm": "html"}
OUTPUT_MIME_TYPES = {
    "txt": "text/plain; charset=utf-8",
    "html": "text/html; charset=utf-8",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "pdf": "application/pdf",
}


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: List[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"p", "br", "div", "li", "h1", "h2", "h3", "tr"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data:
            self.parts.append(data)

    def get_text(self) -> str:
        text = html.unescape("".join(self.parts))
        lines = [re.sub(r"\s+", " ", line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)


class DocumentConverterService:
    """Lightweight document conversion service for common text-oriented formats.

    Supported conversions are text-preserving. PDF conversion extracts selectable
    text from PDF pages; scanned image PDFs need OCR and are intentionally out of
    scope for this lightweight toolbox feature.
    """

    def __init__(self, max_file_size: int = 5 * 1024 * 1024) -> None:
        self.max_file_size = max_file_size

    async def convert(self, upload: UploadFile, target_format: str) -> Dict[str, Any]:
        source_name = Path(upload.filename or "document")
        source_ext = source_name.suffix.lower().lstrip(".")
        source_ext = "html" if source_ext == "htm" else source_ext
        target = TARGET_ALIASES.get(str(target_format or "").lower().strip(), str(target_format or "").lower().strip())

        if source_ext not in SUPPORTED_INPUTS:
            return {"code": 400, "msg": "暂时支持 TXT、HTML、DOCX、PDF、JPG、PNG、WEBP 文件"}
        if target not in SUPPORTED_TARGETS:
            return {"code": 400, "msg": "目标格式支持 txt、html、docx、pdf"}
        if source_ext == target:
            return {"code": 400, "msg": "请选择不同的目标格式"}
        if source_ext in IMAGE_INPUTS and target not in {"pdf", "docx"}:
            return {"code": 400, "msg": "图片转换暂时支持转 PDF 或 Word"}

        content = await upload.read()
        if not content:
            return {"code": 400, "msg": "文件内容为空"}
        if len(content) > self.max_file_size:
            return {"code": 400, "msg": f"文件大小不能超过 {self.max_file_size // 1024 // 1024}MB"}

        try:
            if source_ext in IMAGE_INPUTS:
                output = self._render_image(content, target, source_name.stem or "image")
            else:
                text = self._extract_text(content, source_ext)
                if not text.strip():
                    return {"code": 400, "msg": "未能从文档中提取到文本内容，扫描版 PDF 暂不支持"}
                output = self._render(text, target, source_name.stem or "document")
        except Exception as exc:  # pragma: no cover - defensive API guard
            return {"code": 400, "msg": f"文档转换失败：{exc}"}

        filename = f"{self._safe_stem(source_name.stem)}.{target}"
        return {
            "code": 200,
            "msg": "success",
            "filename": filename,
            "media_type": OUTPUT_MIME_TYPES[target],
            "content": output,
        }

    def _extract_text(self, content: bytes, source_ext: str) -> str:
        if source_ext == "txt":
            return self._decode_text(content)
        if source_ext == "html":
            parser = _TextExtractor()
            parser.feed(self._decode_text(content))
            return parser.get_text()
        if source_ext == "docx":
            doc = Document(BytesIO(content))
            lines: List[str] = []
            lines.extend(p.text for p in doc.paragraphs if p.text.strip())
            for table in doc.tables:
                for row in table.rows:
                    row_text = "\t".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                    if row_text:
                        lines.append(row_text)
            return "\n".join(lines)
        if source_ext == "pdf":
            reader = PdfReader(BytesIO(content))
            return "\n".join(page.extract_text() or "" for page in reader.pages)
        raise ValueError("不支持的源文件格式")

    def _render(self, text: str, target: str, title: str) -> bytes:
        if target == "txt":
            return text.encode("utf-8")
        if target == "html":
            body = "\n".join(f"<p>{html.escape(line)}</p>" for line in text.splitlines() if line.strip())
            return (
                "<!doctype html><html><head><meta charset=\"utf-8\">"
                f"<title>{html.escape(title)}</title></head><body>{body}</body></html>"
            ).encode("utf-8")
        if target == "docx":
            buf = BytesIO()
            doc = Document()
            for line in text.splitlines():
                doc.add_paragraph(line)
            doc.save(buf)
            return buf.getvalue()
        if target == "pdf":
            return self._text_to_pdf(text, title)
        raise ValueError("不支持的目标格式")

    def _text_to_pdf(self, text: str, title: str) -> bytes:
        buf = BytesIO()
        doc = SimpleDocTemplate(buf, pagesize=A4, title=title)
        styles = getSampleStyleSheet()
        try:
            pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
            body_style = ParagraphStyle("ToolboxBody", parent=styles["BodyText"], fontName="STSong-Light", fontSize=10, leading=15)
        except Exception:
            body_style = styles["BodyText"]
        story = []
        for line in text.splitlines():
            escaped = html.escape(line) or " "
            story.append(Paragraph(escaped, body_style))
            story.append(Spacer(1, 6))
        doc.build(story or [Paragraph(" ", body_style)])
        return buf.getvalue()

    def _render_image(self, content: bytes, target: str, title: str) -> bytes:
        image = self._open_image(content)
        if target == "pdf":
            return self._image_to_pdf(image, title)
        if target == "docx":
            return self._image_to_docx(image, title)
        raise ValueError("图片转换暂时支持转 PDF 或 Word")

    @staticmethod
    def _open_image(content: bytes) -> Image.Image:
        image = Image.open(BytesIO(content))
        image = ImageOps.exif_transpose(image)
        if image.mode in {"RGBA", "LA", "P"}:
            bg = Image.new("RGB", image.size, "white")
            if image.mode == "P":
                image = image.convert("RGBA")
            bg.paste(image, mask=image.split()[-1] if image.mode in {"RGBA", "LA"} else None)
            return bg
        return image.convert("RGB")

    def _image_to_pdf(self, image: Image.Image, title: str) -> bytes:
        buf = BytesIO()
        page_width, page_height = A4
        margin = 36
        draw_width = page_width - margin * 2
        draw_height = page_height - margin * 2
        ratio = min(draw_width / image.width, draw_height / image.height)
        width = image.width * ratio
        height = image.height * ratio
        x = (page_width - width) / 2
        y = (page_height - height) / 2
        from reportlab.pdfgen import canvas

        page = canvas.Canvas(buf, pagesize=A4)
        page.setTitle(title)
        image_buffer = BytesIO()
        image.save(image_buffer, format="JPEG", quality=92)
        image_buffer.seek(0)
        page.drawImage(ImageReader(image_buffer), x, y, width=width, height=height, preserveAspectRatio=True, mask="auto")
        page.showPage()
        page.save()
        return buf.getvalue()

    @staticmethod
    def _image_to_docx(image: Image.Image, title: str) -> bytes:
        buf = BytesIO()
        doc = Document()
        doc.add_heading(title, level=1)
        image_buffer = BytesIO()
        image.save(image_buffer, format="JPEG", quality=92)
        image_buffer.seek(0)
        doc.add_picture(image_buffer, width=Inches(6))
        doc.save(buf)
        return buf.getvalue()

    @staticmethod
    def _decode_text(content: bytes) -> str:
        for encoding in ("utf-8", "utf-8-sig", "gb18030"):
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode("utf-8", errors="ignore")

    @staticmethod
    def _safe_stem(stem: str) -> str:
        cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", stem or "document").strip("._")
        return cleaned or "document"


_document_converter_service = DocumentConverterService()


def get_document_converter_service() -> DocumentConverterService:
    return _document_converter_service
