# -*- coding: utf-8 -*-
import argparse
import base64
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

PNG_1X1 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Wl5H7kAAAAASUVORK5CYII="


def _load_module():
    import importlib
    return importlib.import_module("image_plugin_webai_nano_banana.main")


def request_suite():
    mod = _load_module()
    calls = {}

    class Resp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": f"![generated](data:image/png;base64,{PNG_1X1})"}}]}

    def fake_post(url, json=None, headers=None, timeout=None, stream=None):
        calls["url"] = url
        calls["json"] = json
        calls["headers"] = headers
        calls["stream"] = stream
        return Resp()

    with patch("image_plugin_webai_nano_banana.main.requests.post", side_effect=fake_post):
        images, _ = mod.send_webai_image_request(
            api_key="sk-test",
            endpoint="http://localhost:8316",
            model="gemini-3-pro-image-preview",
            prompt="generate a cat",
            reference_images={},
            request_timeout=30,
            stream=False,
        )

    assert calls["url"].endswith("/v1/chat/completions")
    assert calls["headers"]["Authorization"].startswith("Bearer ")
    assert calls["json"]["model"] == "gemini-3-pro-image-preview"
    assert "messages" in calls["json"]
    assert calls["json"]["stream"] is False
    assert len(images) >= 1
    print("PASS request_suite")


def parse_suite():
    mod = _load_module()

    class RespOk:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": f"a ![x](data:image/png;base64,{PNG_1X1}) b"}}]}

    class RespBad:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": "no image"}}]}

    with patch("image_plugin_webai_nano_banana.main.requests.post", return_value=RespOk()):
        images, _ = mod.send_webai_image_request("k", "http://localhost:8316", "gemini-3-pro-image-preview", "p", {}, 30, False)
        assert len(images) == 1

    with patch("image_plugin_webai_nano_banana.main.requests.post", return_value=RespBad()):
        try:
            mod.send_webai_image_request("k", "http://localhost:8316", "gemini-3-pro-image-preview", "p", {}, 30, False)
            raise AssertionError("expected parse failure")
        except Exception as e:
            assert "NO_RETRY:::" in str(e)

    print("PASS parse_suite")


def stream_suite():
    mod = _load_module()

    class RespStream:
        status_code = 200
        text = ""
        def iter_lines(self, decode_unicode=True):
            yield 'data: {"choices":[{"delta":{"content":"![g](data:image/png;base64,' + PNG_1X1[:20] + '"}}]}'
            yield 'data: {"choices":[{"delta":{"content":"' + PNG_1X1[20:] + ')"}}]}'
            yield 'data: [DONE]'

    with patch("image_plugin_webai_nano_banana.main.requests.post", return_value=RespStream()):
        images, _ = mod.send_webai_image_request("k", "http://localhost:8316", "gemini-3-pro-image-preview", "p", {}, 30, True)
        assert len(images) == 1

    print("PASS stream_suite")


def output_suite():
    mod = _load_module()

    class Resp:
        status_code = 200
        def json(self):
            return {"choices": [{"message": {"content": f"![generated](data:image/png;base64,{PNG_1X1})"}}]}

    with tempfile.TemporaryDirectory() as td:
        with patch("image_plugin_webai_nano_banana.main.requests.post", return_value=Resp()):
            out = mod.generate(
                {
                    "prompt": "generate",
                    "reference_images": {},
                    "output_dir": td,
                    "plugin_params": {
                        "api_key": "sk-test",
                        "base_url": "http://localhost:8316",
                        "model": "gemini-3-pro-image-preview",
                        "request_timeout": 300,
                        "stream": False,
                    },
                    "viewer_index": 1,
                }
            )
        assert len(out) >= 1
        assert all(Path(p).exists() for p in out)

    print("PASS output_suite")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", required=True, choices=["request", "parse", "stream", "output"])
    args = parser.parse_args()

    if args.suite == "request":
        request_suite()
    elif args.suite == "parse":
        parse_suite()
    elif args.suite == "stream":
        stream_suite()
    elif args.suite == "output":
        output_suite()


if __name__ == "__main__":
    main()
