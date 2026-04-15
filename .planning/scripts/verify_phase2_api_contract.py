#!/usr/bin/env python3
"""Phase 2 API contract verifier for zlhub provider path.

Suites:
- request: validate endpoint, auth header, payload keys/defaults and image field shape
- parse: validate data[].url extraction and NO_RETRY failure branch
"""

from __future__ import annotations

import argparse
import sys
import types
from pathlib import Path
from typing import Any
from unittest.mock import mock_open, patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if "plugin_utils" not in sys.modules:
    plugin_utils_stub = types.ModuleType("plugin_utils")
    plugin_utils_stub.load_plugin_config = lambda *args, **kwargs: {}
    sys.modules["plugin_utils"] = plugin_utils_stub

from image_plugin_zlhub_nano_banana import main as plugin_main


class _MockResponse:
    def __init__(self, status_code: int = 200, payload: dict[str, Any] | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self) -> dict[str, Any]:
        return self._payload


class ContractAssertionError(AssertionError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise ContractAssertionError(message)


def _assert_request_suite() -> None:
    call_log: list[dict[str, Any]] = []

    def _fake_post(url: str, json: dict[str, Any], headers: dict[str, str], timeout: int | None = None):
        call_log.append({"url": url, "json": json, "headers": headers, "timeout": timeout})
        return _MockResponse(payload={"data": [{"url": "https://img.example/a.png"}]})

    # Test 1: 文生图请求字段与默认值
    with patch.object(plugin_main.requests, "post", side_effect=_fake_post):
        plugin_main.send_doubao_request(
            api_key="token-123",
            endpoint="https://zlhub.xiaowaiyou.cn",
            model="doubao-seedream-5.0-lite",
            prompt="test prompt",
            reference_images={},
            aspect_ratio="16:9",
            request_timeout=77,
            download_timeout=88,
        )

    _assert(len(call_log) == 1, "request suite: text2img should issue exactly one HTTP call")
    call = call_log[-1]
    payload = call["json"]

    _assert(
        call["url"] == "https://zlhub.xiaowaiyou.cn/zhonglian/api/v1/proxy/chat/completions",
        f"request suite: endpoint mismatch: {call['url']}",
    )
    _assert(call["headers"].get("Authorization") == "Bearer token-123", "request suite: Bearer token header mismatch")
    _assert(call["headers"].get("Content-Type") == "application/json", "request suite: content type mismatch")
    _assert(call["timeout"] == 77, f"request suite: request timeout not forwarded, got {call['timeout']}")

    expected_keys = {
        "model",
        "prompt",
        "response_format",
        "size",
        "stream",
        "watermark",
        "sequential_image_generation",
        "image",
    }
    _assert(set(payload.keys()) == expected_keys, f"request suite: payload keys mismatch: {set(payload.keys())}")
    _assert(payload["model"] == "doubao-seedream-5.0-lite", "request suite: model mismatch")
    _assert(payload["prompt"] == "test prompt", "request suite: prompt mismatch")
    _assert(payload["response_format"] == "url", "request suite: response_format default mismatch")
    _assert(payload["size"] == "2K", f"request suite: size mapping mismatch: {payload['size']}")
    _assert(payload["stream"] is False, "request suite: stream default must be False")
    _assert(payload["watermark"] is True, "request suite: watermark default must be True")
    _assert(
        payload["sequential_image_generation"] == "disabled",
        "request suite: sequential_image_generation default must be 'disabled'",
    )
    _assert(payload["image"] == "", "request suite: text2img image field must be empty string")

    # Test 2: 图生图 image 字段必须为数组
    call_log.clear()
    with (
        patch.object(plugin_main.requests, "post", side_effect=_fake_post),
        patch.object(plugin_main.os.path, "exists", return_value=True),
        patch.object(plugin_main.os.path, "getsize", return_value=3),
        patch.object(plugin_main, "upload_image_to_host", return_value="https://img.host/ref.png"),
        patch("builtins.open", mock_open(read_data=b"abc")),
    ):
        plugin_main.send_doubao_request(
            api_key="token-456",
            endpoint="https://zlhub.xiaowaiyou.cn",
            model="doubao-seedream-5.0-lite",
            prompt="img2img prompt",
            reference_images={"ref1": "/tmp/ref1.png"},
            aspect_ratio="1:1",
            request_timeout=31,
            download_timeout=66,
        )

    _assert(len(call_log) == 1, "request suite: img2img should issue exactly one HTTP call")
    payload2 = call_log[-1]["json"]
    _assert(isinstance(payload2["image"], list), "request suite: img2img image field must be array")


def _assert_parse_suite() -> None:
    # Test 3A: 多个 data[].url -> 返回 URL 列表
    with patch.object(
        plugin_main.requests,
        "post",
        return_value=_MockResponse(
            payload={
                "data": [
                    {"url": "https://img.example/1.png"},
                    {"url": "https://img.example/2.png"},
                    {"url": ""},
                ]
            }
        ),
    ):
        image_b64, image_urls = plugin_main.send_doubao_request(
            api_key="token-parse",
            endpoint="https://zlhub.xiaowaiyou.cn",
            model="doubao-seedream-5.0-lite",
            prompt="parse prompt",
            reference_images={},
            request_timeout=20,
        )

    _assert(image_b64 is None, "parse suite: expected None for b64 result on URL response")
    _assert(isinstance(image_urls, list), "parse suite: multiple URLs should return list")
    _assert(image_urls == ["https://img.example/1.png", "https://img.example/2.png"], "parse suite: URL list mismatch")

    # Test 3B: 无可用 data[].url -> NO_RETRY
    with patch.object(
        plugin_main.requests,
        "post",
        return_value=_MockResponse(payload={"data": [{"size": "2K"}, {"url": ""}]}, text="ok"),
    ):
        try:
            plugin_main.send_doubao_request(
                api_key="token-parse",
                endpoint="https://zlhub.xiaowaiyou.cn",
                model="doubao-seedream-5.0-lite",
                prompt="parse fail prompt",
                reference_images={},
                request_timeout=20,
                )
        except Exception as exc:  # contract uses generic Exception
            _assert(str(exc).startswith("NO_RETRY:::"), f"parse suite: expected NO_RETRY prefix, got: {exc}")
        else:
            raise ContractAssertionError("parse suite: expected exception when data[].url missing")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify phase 2 zlhub API contract")
    parser.add_argument("--suite", choices=["request", "parse", "all"], required=True)
    args = parser.parse_args()

    try:
        if args.suite in {"request", "all"}:
            _assert_request_suite()
            print("PASS request_suite")

        if args.suite in {"parse", "all"}:
            _assert_parse_suite()
            print("PASS parse_suite")

        return 0
    except Exception as exc:
        print(f"FAIL {args.suite}_suite: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
