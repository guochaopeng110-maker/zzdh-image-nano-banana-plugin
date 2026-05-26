# -*- coding: utf-8 -*-
import argparse
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PNG_1X1 = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc``\x00\x00\x00\x03\x00\x01+\tM\x84\x00\x00\x00\x00IEND\xaeB`\x82"


def _load_module():
    import importlib
    return importlib.import_module("image_plugin_huimeng_nano_banana.main")


def request_suite():
    mod = _load_module()
    calls = {}

    class Resp:
        status_code = 200
        text = ""
        def json(self):
            return {"task_id": "task-123", "status": "pending"}

    def fake_post(url, json=None, headers=None, timeout=None):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["timeout"] = timeout
        return Resp()

    with patch("image_plugin_huimeng_nano_banana.main.requests.post", side_effect=fake_post):
        task_id = mod.submit_huimeng_task(
            api_key="hm-test",
            endpoint="https://api.huimengi.com",
            model="seedream-4.5",
            prompt="a cat",
            request_timeout_s=30,
        )

    assert task_id == "task-123"
    assert calls["url"].endswith("/api/v1/tasks")
    assert calls["headers"]["Authorization"].startswith("Bearer ")
    assert calls["json"]["model"] == "seedream-4.5"
    assert calls["json"]["params"]["prompt"] == "a cat"
    print("PASS request_suite")


def poll_suite():
    mod = _load_module()

    class RespPending:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "pending"}

    class RespProcessing:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "processing"}

    class RespDone:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "completed", "result": {"image_urls": ["https://example.com/a.png"]}}

    with patch("image_plugin_huimeng_nano_banana.main.requests.get", side_effect=[RespPending(), RespProcessing(), RespDone()]):
        with patch("image_plugin_huimeng_nano_banana.main.time.sleep", return_value=None):
            urls = mod.poll_huimeng_result("k", "https://api.huimengi.com", "task-1", 30, 1, 10000)
            assert urls == ["https://example.com/a.png"]

    class RespFailed:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "failed", "error_message": "bad key"}

    with patch("image_plugin_huimeng_nano_banana.main.requests.get", return_value=RespFailed()):
        try:
            mod.poll_huimeng_result("k", "https://api.huimengi.com", "task-1", 30, 1, 10000)
            raise AssertionError("expected failed task")
        except Exception as e:
            assert "NO_RETRY:::" in str(e)

    print("PASS poll_suite")


def parse_suite():
    mod = _load_module()

    class RespUrls:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "completed", "result": {"image_urls": ["u1", "u2"]}}

    class RespUrl:
        status_code = 200
        text = ""
        def json(self):
            return {"status": "completed", "result": {"image_url": "u1"}}

    with patch("image_plugin_huimeng_nano_banana.main.requests.get", return_value=RespUrls()):
        urls = mod.poll_huimeng_result("k", "https://api.huimengi.com", "task-1", 30, 1, 10000)
        assert urls == ["u1", "u2"]

    with patch("image_plugin_huimeng_nano_banana.main.requests.get", return_value=RespUrl()):
        urls = mod.poll_huimeng_result("k", "https://api.huimengi.com", "task-1", 30, 1, 10000)
        assert urls == ["u1"]

    print("PASS parse_suite")


def output_suite():
    mod = _load_module()

    with tempfile.TemporaryDirectory() as td:
        with patch("image_plugin_huimeng_nano_banana.main.submit_huimeng_task", return_value="task-1"):
            with patch("image_plugin_huimeng_nano_banana.main.poll_huimeng_result", return_value=["https://x/a.png", "https://x/b.png"]):
                with patch("image_plugin_huimeng_nano_banana.main._download_image_from_url", return_value=PNG_1X1):
                    out = mod.generate(
                        {
                            "prompt": "generate",
                            "reference_images": {},
                            "output_dir": td,
                            "plugin_params": {
                                "api_key": "hm-test",
                                "base_url": "https://api.huimengi.com",
                                "model": "seedream-4.5",
                                "request_timeout": 30000,
                                "download_timeout": 30000,
                                "poll_interval_ms": 100,
                                "poll_timeout_ms": 5000,
                            },
                            "viewer_index": 1,
                        }
                    )

        assert len(out) == 2
        assert all(Path(p).is_absolute() for p in out)
        assert all(Path(p).exists() for p in out)

    print("PASS output_suite")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, choices=["request", "poll", "parse", "output"])
    args = parser.parse_args()

    if args.suite == "request":
        request_suite()
    elif args.suite == "poll":
        poll_suite()
    elif args.suite == "parse":
        parse_suite()
    elif args.suite == "output":
        output_suite()


if __name__ == "__main__":
    main()
