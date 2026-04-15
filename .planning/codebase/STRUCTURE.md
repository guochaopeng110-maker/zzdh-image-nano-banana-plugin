# Codebase Structure

**Analysis Date:** 2026-04-15

## Directory Layout

```
zz-image-plugins/
├── nano_banana_plugin_geeknow/         # Active image plugin runtime and UI
│   ├── main.py                          # Core plugin logic and host entry points
│   ├── info.json                        # Plugin metadata descriptor
│   ├── image_task_logs.db               # Local SQLite task history
│   ├── manual_downloads/                # Manual image re-download output
│   ├── ui/                              # Static plugin UI pages
│   │   ├── index.html                   # Main configuration panel
│   │   ├── task_log.html                # Task log and manual download panel
│   │   └── live_log.html                # Live log viewer panel
│   └── __pycache__/                     # Python bytecode artifacts
├── docs/                                # Project documentation
│   └── require/
│       └── zlhub-chat-image-api.md      # API integration reference notes
├── .planning/                           # Generated planning artifacts (current run)
│   └── codebase/                        # Codebase map documents
├── .claude/                             # Claude/GSD command and workflow toolchain
├── .agent/                              # Mirrored toolchain resources
├── .codex/                              # Mirrored toolchain resources
└── .gemini/                             # Mirrored toolchain resources
```

## Directory Purposes

**`nano_banana_plugin_geeknow/`:**
- Purpose: Primary product code for the GeekNow image plugin.
- Contains: Python runtime logic, UI pages, metadata, local DB, download outputs.
- Key files: `nano_banana_plugin_geeknow/main.py`, `nano_banana_plugin_geeknow/ui/index.html`, `nano_banana_plugin_geeknow/info.json`.
- Subdirectories:
  - `ui/`: user-facing plugin pages.
  - `manual_downloads/`: downloaded image files from task log actions.
  - `__pycache__/`: generated runtime cache.

**`docs/`:**
- Purpose: Supporting documentation and external API references.
- Contains: requirement/notes markdown docs.
- Key files: `docs/require/zlhub-chat-image-api.md`.

**`.planning/`:**
- Purpose: Generated planning and analysis artifacts used by GSD workflows.
- Contains: codebase mapping documents produced in this run.
- Key files: `.planning/codebase/*.md`.

**Tooling directories (`.claude/`, `.agent/`, `.codex/`, `.gemini/`):**
- Purpose: command/workflow libraries, templates, hooks, and scripts for automation workflows.
- Contains: workflow markdown, CLI scripts (`get-shit-done/bin/*`), command definitions.
- Key files: `.claude/get-shit-done/workflows/map-codebase.md` and sibling resources.

## Key File Locations

**Entry Points:**
- `nano_banana_plugin_geeknow/main.py` — plugin runtime entry points (`get_info`, `generate`, `handle_action`).
- `nano_banana_plugin_geeknow/ui/index.html` — main user config surface.

**Configuration:**
- `nano_banana_plugin_geeknow/info.json` — plugin name/description metadata.
- Runtime params persisted via host plugin config and read by `load_plugin_config(_PLUGIN_FILE)` in `nano_banana_plugin_geeknow/main.py`.

**Core Logic:**
- `nano_banana_plugin_geeknow/main.py` — provider requests, task logging, update flow, file handling.

**Persistence/Data:**
- `nano_banana_plugin_geeknow/image_task_logs.db` — task status ledger.
- `nano_banana_plugin_geeknow/manual_downloads/` — manual retrieval outputs.

**Documentation:**
- `docs/require/zlhub-chat-image-api.md` — external API examples/reference.

## Naming Conventions

**Files:**
- Python module is single lower_snake file: `main.py`.
- UI files are lowercase with underscores: `task_log.html`, `live_log.html`.
- Metadata/config docs use descriptive lowercase names (`info.json`, `zlhub-chat-image-api.md`).

**Directories:**
- Plugin folder uses snake_case plus suffix naming: `nano_banana_plugin_geeknow`.
- Supporting directories are short descriptive nouns (`ui`, `docs`, `manual_downloads`).

**Special Patterns:**
- Host contract file expected as `main.py` inside plugin directory.
- UI pages are sibling HTML files opened by action names (`open_task_logs` → `task_log.html`, `open_live_logs` → `live_log.html`).

## Where to Add New Code

**New provider integration logic:**
- Add adapter function(s) in `nano_banana_plugin_geeknow/main.py` near existing `send_*_request` functions.
- Route in `generate(context)` by model/prefix map.

**New UI setting/control:**
- Add control + `PluginSDK.saveParam` wiring in `nano_banana_plugin_geeknow/ui/index.html`.
- Read in `generate(context)` from `plugin_params` in `nano_banana_plugin_geeknow/main.py`.

**New popup panel/tool page:**
- Add HTML page under `nano_banana_plugin_geeknow/ui/`.
- Add action branch in `handle_action()` returning `open_page`.

**New task-log fields/state:**
- Extend SQLite schema migration logic in `_init_task_log_db()` and read/write helpers in `nano_banana_plugin_geeknow/main.py`.

## Special Directories

**`nano_banana_plugin_geeknow/__pycache__/`:**
- Purpose: Python bytecode cache.
- Source: auto-generated by Python runtime.
- Committed: currently present in workspace but usually should be ignored in VCS contexts.

**`nano_banana_plugin_geeknow/manual_downloads/`:**
- Purpose: stores user-triggered image downloads from historical tasks.
- Source: generated by `download_images_from_logs()`.
- Committed: runtime artifact, generally should remain local.

**`.planning/codebase/`:**
- Purpose: generated codebase analysis docs for planning workflows.
- Source: map-codebase workflow output.
- Committed: depends on workflow/project preference; currently generated for planning context.

---

*Structure analysis: 2026-04-15*
*Update when directory layout or plugin boundaries change*
