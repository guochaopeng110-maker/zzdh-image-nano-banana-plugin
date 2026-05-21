---
status: investigating
trigger: "image_plugin_webai_nano_banana generate works but no in-app generating hint, no live logs, no task logs"
created: "2026-05-21"
updated: "2026-05-21"
---

# Debug Session

## Symptoms
- expected_behavior: "Click generate should show generating status in 字字软件 and provide realtime logs + task logs, similar to nano_banana_plugin_geeknow."
- actual_behavior: "Image generation succeeds, but no generating hint, no realtime logs, no task logs."
- errors: "No explicit error shown in UI."
- timeline: "Observed after copying image_plugin_webai_nano_banana into 字字 plugin directory and running with non-stream mode."
- reproduction: "Install plugin -> set api_key -> choose non-stream -> click generate image."

## Current Focus
- hypothesis: "Plugin currently lacks status/log persistence and UI action plumbing present in reference plugin, so host cannot display progress/log views."
- test: "Compare main.py and UI pages between webai plugin and nano_banana_plugin_geeknow around generate(), handle_action(), and log/task DB pathways."
- expecting: "Missing lifecycle logging and task log endpoints in webai plugin."
- next_action: "gather initial evidence"
