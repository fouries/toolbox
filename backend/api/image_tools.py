import base64
import re
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from PIL import Image, ImageDraw, ImageFont, ImageOps

IMAGE_FORMATS = {"jpg": "JPEG", "jpeg": "JPEG", "png": "PNG", "webp": "WEBP"}
IMAGE_MIME_TYPES = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}
MAX_IMAGE_SIZE = 10 * 1024 * 1024


class ImageToolboxService:
    """本地图片工具：压缩、格式转换、尺寸调整、水印和 Base64。"""

    def process_base64(self, filename: str, content_base64: str, operation: str, options: Dict[str, Any] | None = None) -> Dict[str, Any]:
        options = options or {}
        operation = str(operation or "").strip().lower()
        try:
            raw = base64.b64decode(content_base64, validate=True)
        except Exception:
            return {"code": 400, "msg": "图片内容不是有效的 Base64"}
        if not raw:
            return {"code": 400, "msg": "图片内容为空"}
        if len(raw) > MAX_IMAGE_SIZE:
            return {"code": 400, "msg": "单张图片不能超过 10MB"}

        source_name = Path(filename or "image.jpg")
        try:
            image = Image.open(BytesIO(raw))
            image = ImageOps.exif_transpose(image)
        except Exception as exc:
            return {"code": 400, "msg": f"图片读取失败：{exc}"}

        if operation == "base64":
            mime = IMAGE_MIME_TYPES.get(source_name.suffix.lower().lstrip("."), "image/png")
            return {"code": 200, "msg": "success", "data": {"text": f"data:{mime};base64,{content_base64}", "size": len(raw)}}

        try:
            target_format = self._target_format(operation, options, source_name)
            image = self._ensure_mode(image, target_format)
            if operation == "resize":
                image = self._resize(image, options)
            elif operation == "watermark":
                image = self._watermark(image, str(options.get("watermark") or "小巧的工具箱"))
            elif operation == "compress":
                # 压缩保持尺寸，仅调整质量和输出格式
                pass
            elif operation == "convert":
                pass
            else:
                return {"code": 400, "msg": "暂不支持该图片操作"}
            content = self._encode_image(image, target_format, int(options.get("quality") or 75))
        except Exception as exc:
            return {"code": 400, "msg": f"图片处理失败：{exc}"}

        ext = "jpg" if target_format == "JPEG" else target_format.lower()
        stem = self._safe_stem(source_name.stem or "image")
        suffix = {"compress": "compressed", "convert": "converted", "resize": "resized", "watermark": "watermark"}.get(operation, "processed")
        return {
            "code": 200,
            "msg": "success",
            "filename": f"{stem}_{suffix}.{ext}",
            "media_type": IMAGE_MIME_TYPES.get(ext, "image/png"),
            "content": content,
        }

    def _target_format(self, operation: str, options: Dict[str, Any], source_name: Path) -> str:
        raw = str(options.get("target_format") or "").lower().strip().lstrip(".")
        if operation == "convert" and raw in IMAGE_FORMATS:
            return IMAGE_FORMATS[raw]
        source_ext = source_name.suffix.lower().lstrip(".")
        return IMAGE_FORMATS.get(source_ext, "JPEG")

    @staticmethod
    def _ensure_mode(image: Image.Image, target_format: str) -> Image.Image:
        if target_format == "JPEG":
            if image.mode in {"RGBA", "LA", "P"}:
                bg = Image.new("RGB", image.size, "white")
                if image.mode == "P":
                    image = image.convert("RGBA")
                bg.paste(image, mask=image.split()[-1] if image.mode in {"RGBA", "LA"} else None)
                return bg
            return image.convert("RGB")
        if image.mode == "P":
            return image.convert("RGBA")
        return image

    @staticmethod
    def _resize(image: Image.Image, options: Dict[str, Any]) -> Image.Image:
        width = int(options.get("width") or 0)
        height = int(options.get("height") or 0)
        if width <= 0 and height <= 0:
            raise ValueError("请输入宽度或高度")
        if width <= 0:
            width = max(1, int(image.width * (height / image.height)))
        if height <= 0:
            height = max(1, int(image.height * (width / image.width)))
        width = max(1, min(width, 4096))
        height = max(1, min(height, 4096))
        return image.resize((width, height), Image.Resampling.LANCZOS)

    @staticmethod
    def _watermark(image: Image.Image, text: str) -> Image.Image:
        base = image.convert("RGBA")
        overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
        draw = ImageDraw.Draw(overlay)
        font = ImageFont.load_default()
        text = text[:40] or "小巧的工具箱"
        bbox = draw.textbbox((0, 0), text, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        pad = max(10, min(base.size) // 60)
        x = max(pad, base.width - tw - pad * 2)
        y = max(pad, base.height - th - pad * 2)
        draw.rounded_rectangle((x - pad, y - pad, x + tw + pad, y + th + pad), radius=pad, fill=(0, 0, 0, 96))
        draw.text((x, y), text, fill=(255, 255, 255, 220), font=font)
        return Image.alpha_composite(base, overlay)

    @staticmethod
    def _encode_image(image: Image.Image, target_format: str, quality: int) -> bytes:
        quality = max(35, min(95, int(quality or 75)))
        buf = BytesIO()
        save_kwargs: Dict[str, Any] = {}
        if target_format in {"JPEG", "WEBP"}:
            save_kwargs.update({"quality": quality, "optimize": True})
        if target_format == "PNG":
            save_kwargs.update({"optimize": True})
        image.save(buf, format=target_format, **save_kwargs)
        return buf.getvalue()

    @staticmethod
    def _safe_stem(stem: str) -> str:
        cleaned = re.sub(r"[^\w\u4e00-\u9fff.-]+", "_", stem or "image").strip("._")
        return cleaned or "image"


_image_toolbox_service = ImageToolboxService()


def get_image_toolbox_service() -> ImageToolboxService:
    return _image_toolbox_service
