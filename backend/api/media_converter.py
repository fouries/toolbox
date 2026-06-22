import base64
import json
import math
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, TypedDict
from urllib.parse import urlparse

import httpx

AUDIO_MIME_TYPES = {
    "mp3": "audio/mpeg",
    "wav": "audio/wav",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
}

SUPPORTED_AUDIO_EXTS = {"mp3", "wav", "m4a", "aac", "ogg", "flac"}
SUPPORTED_VIDEO_EXTS = {"mp4", "mov", "m4v", "webm", "avi", "mkv"}
MAX_FILE_SIZE = 50 * 1024 * 1024
MAX_URL_SIZE = 80 * 1024 * 1024


class MediaInputFile(TypedDict):
    filename: str
    content: bytes


class MediaConverterService:
    """基于 FFmpeg 的轻量音视频处理服务。"""

    def __init__(self) -> None:
        self.ffmpeg = shutil.which("ffmpeg") or ("/usr/bin/ffmpeg" if Path("/usr/bin/ffmpeg").exists() else None)
        self.ffprobe = shutil.which("ffprobe") or ("/usr/bin/ffprobe" if Path("/usr/bin/ffprobe").exists() else None)
        self.whisper_cli = shutil.which("whisper") or "/home/ubuntu/.local/bin/whisper"

    def process(self, operation: str, files: List[MediaInputFile], options: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.ffmpeg:
            return {"code": 400, "msg": "服务器未安装 FFmpeg，暂时无法处理音视频"}
        operation = str(operation or "").strip().lower()
        options = options or {}
        if not files:
            return {"code": 400, "msg": "请上传音频或视频文件"}
        for item in files:
            if len(item.get("content", b"")) > MAX_FILE_SIZE:
                return {"code": 400, "msg": f"{item.get('filename', '文件')} 超过 50MB 限制"}

        handlers = {
            "trim": self._trim_audio,
            "concat": self._concat_audio,
            "merge": self._merge_audio,
            "transcribe": self._transcribe_audio,
            "vocal_remove": self._vocal_remove,
            "volume": self._adjust_volume,
            "video_to_audio": self._video_to_audio,
        }
        handler = handlers.get(operation)
        if not handler:
            return {"code": 400, "msg": "暂不支持该音视频操作"}
        try:
            return handler(files, options)
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or b"").decode("utf-8", errors="ignore")[-300:]
            return {"code": 400, "msg": f"音视频处理失败：{detail or 'FFmpeg 执行失败'}"}
        except Exception as exc:
            return {"code": 400, "msg": f"音视频处理失败：{exc}"}

    async def extract_audio_from_url(self, url: str, target_format: str = "mp3") -> Dict[str, Any]:
        if not self.ffmpeg:
            return {"code": 400, "msg": "服务器未安装 FFmpeg，暂时无法处理音视频"}
        parsed = urlparse(str(url or "").strip())
        if parsed.scheme not in {"http", "https"}:
            return {"code": 400, "msg": "仅支持 http/https 视频直链"}
        target_format = self._normalize_audio_format(target_format)
        try:
            async with httpx.AsyncClient(timeout=30, follow_redirects=True) as client:
                async with client.stream("GET", url, headers={"User-Agent": "Mozilla/5.0"}) as response:
                    response.raise_for_status()
                    content_type = response.headers.get("content-type", "")
                    if content_type and not (content_type.startswith("video/") or content_type.startswith("audio/") or "octet-stream" in content_type):
                        return {"code": 400, "msg": "链接不像可直接下载的视频/音频文件，请提供 mp4/mov/webm 等直链"}
                    suffix = self._guess_suffix_from_url_or_type(url, content_type)
                    with tempfile.TemporaryDirectory() as tmp:
                        input_path = Path(tmp) / f"input{suffix}"
                        size = 0
                        with input_path.open("wb") as fh:
                            async for chunk in response.aiter_bytes(1024 * 256):
                                size += len(chunk)
                                if size > MAX_URL_SIZE:
                                    return {"code": 400, "msg": "链接文件超过 80MB 限制"}
                                fh.write(chunk)
                        output_path = Path(tmp) / f"url_audio.{target_format}"
                        self._run_ffmpeg(["-i", str(input_path), "-vn", *self._audio_output_args(target_format), str(output_path)])
                        return self._file_result(output_path, f"video_audio.{target_format}", target_format)
        except httpx.HTTPError as exc:
            return {"code": 400, "msg": f"读取链接失败：{exc}"}

    def _trim_audio(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        start = max(0.0, self._to_float(options.get("start"), 0.0))
        end = self._to_float(options.get("end"), 0.0)
        duration_args = []
        if end > start:
            duration_args = ["-t", str(end - start)]
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with self._single_input(files[0]) as (tmp, input_path):
            output_path = Path(tmp) / f"trimmed.{target_format}"
            self._run_ffmpeg(["-ss", str(start), "-i", str(input_path), *duration_args, *self._audio_output_args(target_format), str(output_path)])
            return self._file_result(output_path, f"{Path(files[0]['filename']).stem}_trimmed.{target_format}", target_format)

    def _concat_audio(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        if len(files) < 2:
            return {"code": 400, "msg": "音频拼接至少需要 2 个文件"}
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with tempfile.TemporaryDirectory() as tmp:
            input_paths = self._write_inputs(files, tmp)
            list_path = Path(tmp) / "inputs.txt"
            normalized = []
            for idx, input_path in enumerate(input_paths):
                norm_path = Path(tmp) / f"norm_{idx}.wav"
                self._run_ffmpeg(["-i", str(input_path), "-ac", "2", "-ar", "44100", str(norm_path)])
                normalized.append(norm_path)
            list_path.write_text("".join(f"file '{path.as_posix()}'\n" for path in normalized), encoding="utf-8")
            output_path = Path(tmp) / f"concat.{target_format}"
            self._run_ffmpeg(["-f", "concat", "-safe", "0", "-i", str(list_path), *self._audio_output_args(target_format), str(output_path)])
            return self._file_result(output_path, f"audio_concat.{target_format}", target_format)

    def _merge_audio(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        if len(files) < 2:
            return {"code": 400, "msg": "音频合并至少需要 2 个文件"}
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with tempfile.TemporaryDirectory() as tmp:
            input_paths = self._write_inputs(files, tmp)
            cmd = []
            for path in input_paths:
                cmd.extend(["-i", str(path)])
            cmd.extend(["-filter_complex", f"amix=inputs={len(input_paths)}:duration=longest:dropout_transition=0", *self._audio_output_args(target_format), str(Path(tmp) / f"merged.{target_format}")])
            output_path = Path(tmp) / f"merged.{target_format}"
            self._run_ffmpeg(cmd)
            return self._file_result(output_path, f"audio_merged.{target_format}", target_format)

    def _adjust_volume(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        volume = min(5.0, max(0.1, self._to_float(options.get("volume"), 1.0)))
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with self._single_input(files[0]) as (tmp, input_path):
            output_path = Path(tmp) / f"volume.{target_format}"
            self._run_ffmpeg(["-i", str(input_path), "-filter:a", f"volume={volume}", *self._audio_output_args(target_format), str(output_path)])
            return self._file_result(output_path, f"{Path(files[0]['filename']).stem}_volume.{target_format}", target_format)

    def _video_to_audio(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with self._single_input(files[0]) as (tmp, input_path):
            output_path = Path(tmp) / f"video_audio.{target_format}"
            self._run_ffmpeg(["-i", str(input_path), "-vn", *self._audio_output_args(target_format), str(output_path)])
            return self._file_result(output_path, f"{Path(files[0]['filename']).stem}_audio.{target_format}", target_format)

    def _vocal_remove(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        # 轻量版：利用立体声中置抵消做人声消除；不是 Demucs 级 AI 分离。
        mode = str(options.get("vocal_mode") or "instrumental").lower()
        target_format = self._normalize_audio_format(options.get("target_format", "mp3"))
        with self._single_input(files[0]) as (tmp, input_path):
            output_path = Path(tmp) / f"vocal_{mode}.{target_format}"
            if mode == "vocal":
                audio_filter = "pan=mono|c0=0.5*c0+0.5*c1"
                suffix = "vocal"
            else:
                audio_filter = "pan=stereo|c0=c0-c1|c1=c1-c0"
                suffix = "instrumental"
            self._run_ffmpeg(["-i", str(input_path), "-af", audio_filter, *self._audio_output_args(target_format), str(output_path)])
            return self._file_result(output_path, f"{Path(files[0]['filename']).stem}_{suffix}.{target_format}", target_format)

    def _transcribe_audio(self, files: List[MediaInputFile], options: Dict[str, Any]) -> Dict[str, Any]:
        language = str(options.get("language") or "zh").strip() or "zh"
        model_size = str(options.get("model") or os.getenv("TOOLBOX_WHISPER_MODEL") or "base")
        with self._single_input(files[0]) as (tmp, input_path):
            wav_path = Path(tmp) / "speech.wav"
            self._run_ffmpeg(["-i", str(input_path), "-ac", "1", "-ar", "16000", str(wav_path)])
            try:
                from faster_whisper import WhisperModel
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                segments, info = model.transcribe(str(wav_path), language=None if language == "auto" else language)
                text = "".join(segment.text for segment in segments).strip()
                return {"code": 200, "msg": "success", "data": {"text": text, "language": getattr(info, "language", language), "duration": getattr(info, "duration", None)}}
            except Exception:
                pass
            try:
                import whisper
                model = whisper.load_model(model_size)
                result = model.transcribe(str(wav_path), language=None if language == "auto" else language, fp16=False)
                return {"code": 200, "msg": "success", "data": {"text": str(result.get("text") or "").strip(), "language": result.get("language", language), "duration": None}}
            except Exception:
                pass
            if self.whisper_cli and Path(self.whisper_cli).exists():
                output_dir = Path(tmp) / "whisper"
                output_dir.mkdir(exist_ok=True)
                cmd = [self.whisper_cli, str(wav_path), "--model", model_size, "--output_format", "txt", "--output_dir", str(output_dir), "--fp16", "False"]
                if language != "auto":
                    cmd.extend(["--language", language])
                try:
                    subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=180)
                    txt_files = list(output_dir.glob("*.txt"))
                    text = txt_files[0].read_text(encoding="utf-8").strip() if txt_files else ""
                    return {"code": 200, "msg": "success", "data": {"text": text, "language": language, "duration": None}}
                except Exception as exc:
                    return {"code": 400, "msg": f"声音转文字失败：{exc}"}
            return {"code": 400, "msg": "声音转文字需要 Whisper 模型/命令，当前后端环境不可用"}

    def _single_input(self, file: MediaInputFile):
        class _Ctx:
            def __enter__(_self):
                _self.tmp = tempfile.TemporaryDirectory()
                suffix = self._suffix(file.get("filename", "input"))
                _self.input_path = Path(_self.tmp.name) / f"input{suffix}"
                _self.input_path.write_bytes(file.get("content", b""))
                return _self.tmp.name, _self.input_path

            def __exit__(_self, exc_type, exc, tb):
                _self.tmp.cleanup()
        return _Ctx()

    def _write_inputs(self, files: List[MediaInputFile], tmp: str) -> List[Path]:
        paths = []
        for idx, file in enumerate(files):
            path = Path(tmp) / f"input_{idx}{self._suffix(file.get('filename', 'input'))}"
            path.write_bytes(file.get("content", b""))
            paths.append(path)
        return paths

    def _run_ffmpeg(self, args: List[str]) -> None:
        cmd = [self.ffmpeg, "-hide_banner", "-loglevel", "error", "-y", *args]
        subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    @staticmethod
    def _suffix(filename: str) -> str:
        suffix = Path(str(filename or "input")).suffix.lower()
        return suffix if suffix else ".bin"

    @staticmethod
    def _normalize_audio_format(fmt: Any) -> str:
        fmt = str(fmt or "mp3").lower().strip().lstrip(".")
        return fmt if fmt in AUDIO_MIME_TYPES else "mp3"

    @staticmethod
    def _audio_output_args(fmt: str) -> List[str]:
        if fmt == "wav":
            return ["-ac", "2", "-ar", "44100"]
        if fmt == "m4a":
            return ["-vn", "-c:a", "aac", "-b:a", "192k"]
        if fmt == "aac":
            return ["-vn", "-c:a", "aac", "-b:a", "192k"]
        return ["-vn", "-c:a", "libmp3lame", "-b:a", "192k"]

    @staticmethod
    def _file_result(path: Path, filename: str, fmt: str) -> Dict[str, Any]:
        return {
            "code": 200,
            "msg": "success",
            "filename": filename,
            "media_type": AUDIO_MIME_TYPES.get(fmt, "audio/mpeg"),
            "content": path.read_bytes(),
        }

    @staticmethod
    def _to_float(value: Any, default: float) -> float:
        try:
            if value in (None, ""):
                return default
            number = float(value)
            return number if math.isfinite(number) else default
        except Exception:
            return default

    @staticmethod
    def _guess_suffix_from_url_or_type(url: str, content_type: str) -> str:
        suffix = Path(urlparse(url).path).suffix.lower()
        if suffix:
            return suffix
        if "webm" in content_type:
            return ".webm"
        if "quicktime" in content_type:
            return ".mov"
        if "audio" in content_type:
            return ".mp3"
        return ".mp4"


_media_converter_service = MediaConverterService()


def get_media_converter_service() -> MediaConverterService:
    return _media_converter_service
