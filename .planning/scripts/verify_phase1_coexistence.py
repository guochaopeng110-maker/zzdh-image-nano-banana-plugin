# -*- coding: utf-8 -*-
"""Phase 1 coexistence verification for GeekNow and zlhub plugins."""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path


def _ensure_plugin_utils_stub() -> None:
    """Provide a minimal plugin_utils module if runtime dependency is absent."""
    if "plugin_utils" in sys.modules:
        return
    stub = types.ModuleType("plugin_utils")

    def load_plugin_config(_plugin_file):
        return {}

    stub.load_plugin_config = load_plugin_config
    sys.modules["plugin_utils"] = stub


def _load_module(module_name: str, file_path: Path):
    spec = importlib.util.spec_from_file_location(module_name, str(file_path))
    assert spec is not None, f"failed to build spec for {file_path}"
    assert spec.loader is not None, f"failed to build loader for {file_path}"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    worktree_root = Path(__file__).resolve().parents[2]
    repo_root = worktree_root.parents[2]

    new_root = worktree_root / "image_plugin_zlhub_nano_banana"
    old_root = worktree_root / "nano_banana_plugin_geeknow"
    if not old_root.exists():
        old_root = repo_root / "nano_banana_plugin_geeknow"

    new_main = new_root / "main.py"
    new_info = new_root / "info.json"
    new_ui = new_root / "ui" / "index.html"

    old_main = old_root / "main.py"
    old_info = old_root / "info.json"

    for required in [new_main, new_info, new_ui, old_main, old_info]:
        assert required.exists(), f"required file missing: {required}"

    _ensure_plugin_utils_stub()

    old_module = _load_module("phase1_old_plugin", old_main)
    new_module = _load_module("phase1_new_plugin", new_main)

    for name in ["get_info", "generate", "handle_action"]:
        assert hasattr(old_module, name), f"old plugin missing entry: {name}"
        assert hasattr(new_module, name), f"new plugin missing entry: {name}"
        assert callable(getattr(old_module, name)), f"old plugin entry not callable: {name}"
        assert callable(getattr(new_module, name)), f"new plugin entry not callable: {name}"

    old_runtime_info = old_module.get_info()
    new_runtime_info = new_module.get_info()

    assert old_runtime_info.get("name") != new_runtime_info.get("name"), "runtime names must differ"
    assert "GeekNow" in str(old_runtime_info.get("name", "")), "old runtime name must include GeekNow"
    assert "zlhub" in str(new_runtime_info.get("name", "")), "new runtime name must include zlhub"

    old_static_info = _read_json(old_info)
    new_static_info = _read_json(new_info)
    assert old_static_info.get("name") != new_static_info.get("name"), "info.json names must differ"

    print("coexistence verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
