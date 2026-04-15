#!/usr/bin/env python3
"""Phase 2 output-path verifier for zlhub generate() download/save flow.

Suites:
- single: single URL response -> one absolute local file path
- multi: multi URL response -> partial success retained + all-failed raises error
"""

from __future__ import annotations

import argparse
import base64
import sys
import tempfile
import types
from pathlib import Path
from typing import Any
from unittest.mock import patch

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

if "plugin_utils" not in sys.modules:
    plugin_utils_stub = types.ModuleType("plugin_utils")
    plugin_utils_stub.load_plugin_config = lambda *args, **kwargs: {}
    sys.modules["plugin_utils"] = plugin_utils_stub

from image_plugin_zlhub_nano_banana import main as plugin_main


class OutputPathAssertionError(AssertionError):
    pass


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise OutputPathAssertionError(message)


# 1x1 PNG
_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVQIHWP4"
    "////fwAJ+wP9KobjigAAAABJRU5ErkJggg=="
)


def _build_context(output_dir: str) -> dict[str, Any]:
    return {
        "prompt": "phase2 output test",
        "reference_images": {},
        "output_dir": output_dir,
        "viewer_index": 12,
        "plugin_params": {
            "api_key": "token-abc",
            "base_url": "https://zlhub.xiaowaiyou.cn",
            "model": "doubao-seedream-5.0-lite",
            "aspect_ratio": "16:9",
            "image_size": "2K",
            "request_timeout": 20,
            "download_timeout": 20,
        },
    }


def _assert_single_url_suite() -> None:
    task_statuses: list[str] = []

    def _fake_log_task_result(task_context, status, **kwargs):
        task_statuses.append(status)
        if status == "running":
            return 1001
        return kwargs.get("log_id")

    with tempfile.TemporaryDirectory(prefix="phase2-single-") as tmpdir:
        context = _build_context(tmpdir)

        with (
            patch.object(plugin_main, "send_doubao_request", return_value=(None, "https://img.example/single.png")),
            patch.object(plugin_main, "_download_image_from_url", return_value=_PNG_BASE64),
            patch.object(plugin_main, "_log_task_result", side_effect=_fake_log_task_result),
        ):
            paths = plugin_main.generate(context)

        _assert(isinstance(paths, list), "single suite: generate() must return list")
        _assert(len(paths) == 1, f"single suite: expected 1 output path, got {len(paths)}")

        p = Path(paths[0])
        _assert(p.is_absolute(), f"single suite: path must be absolute, got {paths[0]}")
        _assert(p.exists(), f"single suite: output file not found: {paths[0]}")
        _assert(str(p).startswith(str(Path(tmpdir))), "single suite: output path must be under output_dir")

        _assert("success" in task_statuses, f"single suite: missing success status, got {task_statuses}")


def _assert_multi_url_suite() -> None:
    png_bytes = base64.b64decode(_PNG_BASE64)

    # Test 1: partial failure should keep successful files
    task_statuses_partial: list[str] = []

    def _fake_log_task_result_partial(task_context, status, **kwargs):
        task_statuses_partial.append(status)
        if status == "running":
            return 2001
        return kwargs.get("log_id")

    def _download_side_effect_partial(url: str, download_timeout: int = 300) -> str:
        if url.endswith("3.png"):
            raise plugin_main.ImageDownloadError("mock download failure", url)
        return base64.b64encode(png_bytes).decode("utf-8")

    with tempfile.TemporaryDirectory(prefix="phase2-multi-partial-") as tmpdir:
        context = _build_context(tmpdir)

        with (
            patch.object(
                plugin_main,
                "send_doubao_request",
                return_value=(None, [
                    "https://img.example/1.png",
                    "https://img.example/2.png",
                    "https://img.example/3.png",
                ]),
            ),
            patch.object(plugin_main, "_download_image_from_url", side_effect=_download_side_effect_partial),
            patch.object(plugin_main, "_log_task_result", side_effect=_fake_log_task_result_partial),
        ):
            paths = plugin_main.generate(context)

        _assert(len(paths) == 2, f"multi suite(partial): expected 2 successful files, got {len(paths)}")
        for idx, output_path in enumerate(paths, start=1):
            p = Path(output_path)
            _assert(p.is_absolute(), f"multi suite(partial): non-absolute path: {output_path}")
            _assert(p.exists(), f"multi suite(partial): missing output file: {output_path}")
            _assert(f"_n{idx}" in p.name, f"multi suite(partial): missing suffix _n{idx} in filename: {p.name}")

        _assert(
            task_statuses_partial.count("success") == 2,
            f"multi suite(partial): expected 2 success logs, got {task_statuses_partial}",
        )
        _assert(
            task_statuses_partial.count("download_failed") == 1,
            f"multi suite(partial): expected 1 download_failed log, got {task_statuses_partial}",
        )

    # Test 2: all URL downloads failed -> PLUGIN_ERROR and failed status
    task_statuses_all_failed: list[str] = []

    def _fake_log_task_result_all_failed(task_context, status, **kwargs):
        task_statuses_all_failed.append(status)
        if status == "running":
            return 3001
        return kwargs.get("log_id")

    def _download_side_effect_all_failed(url: str, download_timeout: int = 300) -> str:
        raise plugin_main.ImageDownloadError("mock all fail", url)

    with tempfile.TemporaryDirectory(prefix="phase2-multi-allfail-") as tmpdir:
        context = _build_context(tmpdir)

        with (
            patch.object(
                plugin_main,
                "send_doubao_request",
                return_value=(None, ["https://img.example/a.png", "https://img.example/b.png"]),
            ),
            patch.object(plugin_main, "_download_image_from_url", side_effect=_download_side_effect_all_failed),
            patch.object(plugin_main, "_log_task_result", side_effect=_fake_log_task_result_all_failed),
        ):
            try:
                plugin_main.generate(context)
            except Exception as exc:
                _assert(
                    str(exc).startswith("PLUGIN_ERROR:::"),
                    f"multi suite(all-failed): expected PLUGIN_ERROR prefix, got {exc}",
                )
            else:
                raise OutputPathAssertionError("multi suite(all-failed): expected exception when all downloads fail")

        _assert(
            "failed" in task_statuses_all_failed,
            f"multi suite(all-failed): expected failed task status, got {task_statuses_all_failed}",
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify phase 2 output paths contract")
    parser.add_argument("--suite", choices=["single", "multi", "all"], required=True)
    args = parser.parse_args()

    try:
        if args.suite in {"single", "all"}:
            _assert_single_url_suite()
            print("PASS single_url_suite")

        if args.suite in {"multi", "all"}:
            _assert_multi_url_suite()
            print("PASS multi_url_suite")

        return 0
    except Exception as exc:
        print(f"FAIL {args.suite}_url_suite: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
