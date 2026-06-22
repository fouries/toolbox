import asyncio
import base64
import functools
import http.server
import socketserver
import subprocess
import threading
from pathlib import Path
from typing import cast

from api.media_converter import MediaConverterService, MediaInputFile


def _run_ffmpeg(args):
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", *args], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)


def _make_sine(path: Path, frequency: int = 440, duration: float = 0.8):
    _run_ffmpeg(["-f", "lavfi", "-i", f"sine=frequency={frequency}:duration={duration}", "-c:a", "pcm_s16le", str(path)])
    return path.read_bytes()


def _make_video(path: Path, duration: float = 0.8):
    _run_ffmpeg([
        "-f", "lavfi", "-i", f"testsrc=size=160x120:rate=10:duration={duration}",
        "-f", "lavfi", "-i", f"sine=frequency=600:duration={duration}",
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac", "-shortest", str(path)
    ])
    return path.read_bytes()


def _probe_duration(path: Path) -> float:
    result = subprocess.run([
        "ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=nk=1:nw=1", str(path)
    ], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    return float(result.stdout.strip())


def _write_result(tmp_path: Path, result: dict) -> Path:
    assert result["code"] == 200, result
    data = result.get("content") or base64.b64decode(result["data"]["base64"])
    out = tmp_path / result.get("filename", "out.mp3")
    out.write_bytes(data)
    assert out.stat().st_size > 100
    return out


def test_media_converter_trim_concat_merge_volume_and_video_to_audio(tmp_path):
    service = MediaConverterService()
    one: MediaInputFile = {"filename": "one.wav", "content": _make_sine(tmp_path / "one.wav", 440, 1.0)}
    two: MediaInputFile = {"filename": "two.wav", "content": _make_sine(tmp_path / "two.wav", 660, 1.0)}

    trimmed = _write_result(tmp_path, service.process("trim", [one], {"start": 0.1, "end": 0.5, "target_format": "mp3"}))
    assert trimmed.suffix == ".mp3"
    assert _probe_duration(trimmed) < 1.0

    concat = _write_result(tmp_path, service.process("concat", [one, two], {"target_format": "mp3"}))
    assert _probe_duration(concat) > 1.5

    merged = _write_result(tmp_path, service.process("merge", [one, two], {"target_format": "mp3"}))
    assert _probe_duration(merged) > 0.7

    volume = _write_result(tmp_path, service.process("volume", [one], {"volume": 1.5, "target_format": "mp3"}))
    assert _probe_duration(volume) > 0.7

    instrumental = _write_result(tmp_path, service.process("vocal_remove", [one], {"vocal_mode": "instrumental", "target_format": "mp3"}))
    assert instrumental.name.endswith("_instrumental.mp3")

    video: MediaInputFile = {"filename": "clip.mp4", "content": _make_video(tmp_path / "clip.mp4", 1.0)}
    extracted = _write_result(tmp_path, service.process("video_to_audio", [video], {"target_format": "mp3"}))
    assert extracted.name.endswith("_audio.mp3")


def test_media_converter_rejects_missing_files_and_unknown_operation():
    service = MediaConverterService()
    assert service.process("trim", [], {})["code"] == 400
    assert service.process("unknown", [cast(MediaInputFile, {"filename": "a.wav", "content": b"x"})], {})["code"] == 400


def test_media_converter_extracts_audio_from_direct_video_url(tmp_path):
    service = MediaConverterService()
    _make_video(tmp_path / "direct.mp4", 0.8)

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(tmp_path))
    with socketserver.TCPServer(("127.0.0.1", 0), handler) as httpd:
        thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        thread.start()
        try:
            url = f"http://127.0.0.1:{httpd.server_address[1]}/direct.mp4"
            result = asyncio.run(service.extract_audio_from_url(url, "mp3"))
            out = _write_result(tmp_path, result)
            assert _probe_duration(out) > 0.5
        finally:
            httpd.shutdown()


def test_media_transcribe_returns_text_payload_or_clear_error(tmp_path):
    service = MediaConverterService()
    audio: MediaInputFile = {"filename": "silence.wav", "content": _make_sine(tmp_path / "speech.wav", 440, 0.2)}
    result = service.process("transcribe", [audio], {"language": "zh", "model": "base"})
    if result["code"] == 200:
        assert "text" in result["data"]
    else:
        assert "声音转文字" in result["msg"] or "Whisper" in result["msg"]


def test_media_async_task_endpoints_create_poll_and_download(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main

    monkeypatch.setattr(main, "MEDIA_TASK_DIR", tmp_path / "media_tasks")
    main.MEDIA_TASKS.clear()
    client = TestClient(main.app)
    audio_bytes = _make_sine(tmp_path / "task.wav", 440, 0.5)

    create = client.post(
        "/api/media/tasks",
        data={"operation": "trim", "options": '{"target_format":"mp3","start":0,"end":0.3}'},
        files=[("files", ("task.wav", audio_bytes, "audio/wav"))],
    )
    assert create.status_code == 200, create.text
    task_id = create.json()["data"]["task_id"]

    status = {}
    for _ in range(40):
        status_res = client.get(f"/api/media/tasks/{task_id}")
        assert status_res.status_code == 200, status_res.text
        status = status_res.json()["data"]
        if status["status"] in {"completed", "failed"}:
            break
        import time
        time.sleep(0.2)

    assert status["status"] == "completed", status
    assert status["download_url"].endswith(f"/api/media/tasks/{task_id}/download")
    downloaded = client.get(status["download_url"])
    assert downloaded.status_code == 200
    assert downloaded.headers["content-type"].startswith("audio/")
    assert len(downloaded.content) > 100


def test_media_url_task_endpoint_rejects_non_http():
    from fastapi.testclient import TestClient
    import main

    client = TestClient(main.app)
    response = client.post("/api/media/url-tasks", json={"url": "ftp://example.com/a.mp4", "target_format": "mp3"})
    assert response.status_code == 400


def test_media_task_init_upload_start_flow(tmp_path, monkeypatch):
    from fastapi.testclient import TestClient
    import main

    monkeypatch.setattr(main, "MEDIA_TASK_DIR", tmp_path / "media_tasks_init")
    main.MEDIA_TASKS.clear()
    client = TestClient(main.app)
    audio_bytes = _make_sine(tmp_path / "init.wav", 440, 0.5)

    init = client.post("/api/media/tasks/init", json={"operation": "trim", "options": {"target_format": "mp3", "start": 0, "end": 0.3}})
    assert init.status_code == 200, init.text
    task_id = init.json()["data"]["task_id"]
    uploaded = client.post(f"/api/media/tasks/{task_id}/files", files={"file": ("init.wav", audio_bytes, "audio/wav")})
    assert uploaded.status_code == 200, uploaded.text
    started = client.post(f"/api/media/tasks/{task_id}/start")
    assert started.status_code == 200, started.text

    status = {}
    for _ in range(40):
        status = client.get(f"/api/media/tasks/{task_id}").json()["data"]
        if status["status"] in {"completed", "failed"}:
            break
        import time
        time.sleep(0.2)
    assert status["status"] == "completed", status
