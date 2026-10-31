# dsh-pet-chubby_blue_whale

> **Fork Notice** | Based on [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop) (MIT License, Copyright (c) 2026 Merzlin) — personal self-use re-development. Original copyright notice ([`LICENSE`](LICENSE)) and third-party notices ([`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md)) are preserved.

A **desktop pet frontend for DSH (DeepSeek Harness)**, connecting to DSH via the `dsh-web-service` plugin's session API.

[中文文档](README_ZH.md)

## Features

- **Chat**: Continuous conversation via DSH Web Service session API (`/sessions/:id/prompt-stream`), shown as a single session on the DSH side
- **Character → Workspace mapping**: Each pet character binds to an independent DSH workspace (`~/.dsh-pet-workspace/<char_id>`); memories are shared within the workspace
- **Memory**: Powered by the `@dsh-pet/memory` DSH plugin (forked from fish-memory, 14-day half-life), shared per workspace; the pet frontend is pure UI; toggle per character, enabled by default
- **Screen capture / screenshot Q&A**: Upload screenshot to DSH session (`POST /sessions/:id/files`) → ask → bubble shows reply
- **Balance query**: Query DeepSeek balance via the `dsh-balance-panel` plugin
- **IP city detection**: Detect city on first launch, prompt to set default weather city
- **Auto self-talk**: Daily auto-generated self-talk candidates (trending topics, news, quips) via DSH API in the pet's identity; replaces rather than accumulates
- **No releases, no CI/CD** — personal self-use packaging only
- Dependency management via uv + `pyproject.toml` (Python 3.14+)
- Upstream sync: `git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream`

> **Platform**: Currently verified **only on Windows 11**. Linux/macOS not yet tested.

## DSH Plugin Dependencies

| Plugin | Purpose | Source | Install |
|---|---|---|---|
| `dsh-web-service` | REST API (sessions/workspaces/upload/SSE streaming) | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) | `dsh plugin --profile web add @toddpan/dsh-webapi` |
| `@dsh-pet/memory` | Per-workspace long-term memory (forked from fish-memory, 14-day half-life) | Bundled in `integrations/dsh-pet-memory/` | Auto-detected on startup with install prompt |
| `@wycto/dsh-balance-panel` | Balance query endpoint `GET /dsh-balance-panel` | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) | `dsh plugin --profile web add @wycto/dsh-balance-panel` |

> **Note**: `@dsh-pet/memory` and the original `dsh-fish-memory` both register the `remember` tool — **do not install both in the same DSH profile**. If fish-memory is already installed, remove it first: `dsh plugin --profile <profile> remove dsh-fish-memory`.

## Recommended Plugins (not bundled)

| Plugin | Purpose | Source |
|---|---|---|
| `dsh-persona-dafeiyu` | Persona library: built-in characters, import custom personas, per-workspace scoping, hot-swap without restart. Injects via `ctx.systemPrompt.section()` (prompt-caching friendly). | [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) |

## Acknowledged Plugins & References

### Bundled (modified)

| Plugin | Based on | Modifications | Source |
|---|---|---|---|
| `@dsh-pet/memory` | [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) | Per-workspace memory sharing; `<system-reminder>` query filter; queryGate small-lib guard (0.8→0.5, skip when <10 memories); settings UI session→workspace; packed-dir encoding fix | [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) |

### Dependencies (unmodified)

| Plugin | Purpose | Source |
|---|---|---|
| `dsh-web-service` | REST/SSE API server | [toddpan/dsh-webapi](https://github.com/toddpan/dsh-webapi) |
| `@wycto/dsh-balance-panel` | DeepSeek balance query | [wycto/dsh-balance-panel](https://github.com/wycto/dsh-balance-panel) |

### Recommended (not installed)

| Plugin | Purpose | Source |
|---|---|---|
| `dsh-persona-dafeiyu` | Persona/system-prompt management (per-workspace, hot-swap) | [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) |
| `dsh-whale-musume-persona` | Whale-girl (大肥鱼) persona | [Kaalia0912/dsh-whale-musume-persona](https://github.com/Kaalia0912/dsh-whale-musume-persona) |
| `dsh-prompt-persona` | Edit deployment persona from settings page | [Xilin3/dsh-prompt-persona](https://github.com/Xilin3/dsh-prompt-persona) |

---

## Table of Contents

- [Quick Start](#quick-start)
- [Packaging](#packaging)
- [Asset Packs](#asset-packs)
- [Data Directory](#data-directory)
- [Changelog](#changelog)
- [License & Acknowledgements](#license--acknowledgements)

---

## Quick Start

Requires Python 3.14+. Uses uv for dependency management:

```powershell
uv sync                    # Install dependencies from pyproject.toml into .venv
uv run python -m pet       # Launch the pet
```

## Packaging

### Full Installer (exe)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_installer.ps1
```

Output: `dist-onedir\dsh-pet-chubby_blue_whale-setup.exe` (~500MB, includes all assets, no admin required)

### Incremental Update (exe, no assets)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_update.ps1
```

Output: `dist-onedir\dsh-pet-chubby_blue_whale-update-setup.exe` (~100MB, code-only, preserves existing assets)

### Portable (zip)

```powershell
powershell -ExecutionPolicy Bypass -File scripts\build_portable.ps1
```

Output: `dist-onedir\dsh-pet-chubby_blue_whale-portable.zip` (~500MB, extract and run)

| Script | Assets | ISCC | Portable zip | Size |
|---|---|---|---|---|
| `build_installer.ps1` | ✅ | ✅ | ❌ | ~500MB |
| `build_update.ps1` | ❌ | ✅ | ❌ | ~100MB |
| `build_portable.ps1` | ✅ | ❌ | ✅ | ~500MB |

**Prerequisites**: [uv](https://docs.astral.sh/uv/) installed; Inno Setup 7 for installer/update builds (default path: `D:\Tool\Inno Setup 7\ISCC.exe`).

## Asset Packs

The repo includes **106 WebM animations** (`assets/characters/shenshen/videos/`). Frame sequences (WebP) are generated at build time via `convert_frameseq_progress.py`.

`packs-index.json` lists pre-built asset packs (core + extra1-6, ~1.45GB total) — WebP frame sequences corresponding 1:1 to the 106 WebM files. These are for **installer users** who don't have the repo.

| Directory | Source | Format | Use case |
|---|---|---|---|
| `videos/` | Repo | WebM | Source material (dev) |
| `anim/` | Asset pack | WebP frames | Installer users |
| `frameseq/` | Generated | WebP frames | Repo users (auto-converted from WebM) |

Runtime auto-selects: uses `anim/` if available, otherwise generates `frameseq/` from `videos/` on first run.

## Data Directory

Settings and DSH sessions persist across reinstalls:

| OS | Path |
|---|---|
| Windows | `%APPDATA%/dsh-pet-chubby_blue_whale/` |
| macOS | `~/Library/Application Support/dsh-pet-chubby_blue_whale/` |
| Linux | `~/.config/dsh-pet-chubby_blue_whale/` |

```text
config.json                # Global settings
config-slot-0.json         # Per-pet settings (main pet)
dsh_session.json           # Character→workspace/session mapping
dsh_workspaces.json        # Workspace bindings + memory toggle
sessions/<character_id>/   # Session history
pet.log
```

## Changelog

> Tracks all modifications from upstream for merge conflict reference.
>
> **Merge strategy**: `git remote add upstream https://github.com/MerZlin/dsh-pet-indesktop.git && git fetch upstream && git merge upstream/main`

### Added Files

| File | Purpose |
|---|---|
| `pet/dsh_api.py` | DSH Web Service REST API client (workspaces/sessions/upload/SSE) |
| `pet/chat/dsh_provider.py` | `DshWebApiProvider` + `ProviderRouter` |
| `pet/dsh_workspace.py` | Per-character workspace binding + memory toggle |
| `pet/memory_plugin_link.py` | `@dsh-pet/memory` install check & one-click install |
| `integrations/dsh-pet-memory/` | DSH memory plugin (forked from fish-memory, per-workspace, 14-day half-life) |
| `pet/dsh_self_talk.py` | Daily auto self-talk generation via DSH API |
| `pet/weather/ip_city.py` | IP city detection (Gaode API → free fallback) |
| `tools/convert_frameseq_progress.py` | Frame sequence converter with progress/ETA |
| `scripts/build_installer.ps1` | Full installer build script |
| `scripts/build_update.ps1` | Incremental update build script |
| `scripts/build_portable.ps1` | Portable zip build script |
| `scripts/run_all_tests.ps1` | Run all tests with timeout |
| `packaging/dsh-pet-chubby_blue_whale.iss` | Inno Setup script |

### Modified Files

| File | Changes |
|---|---|
| `pet/chat/service.py` | Inject `ProviderRouter`; remove memory extraction hook |
| `pet/chat/prompt.py` | Add `MEMORY_GUIDE` segment to `build_messages` |
| `pet/chat/ai_settings_page.py` | Add DSH memory plugin settings + install button |
| `pet/chat/widgets.py` / `pet/legacy_widgets.py` | Remove memory UI & logic |
| `pet/quick_chat.py` / `pet/modern_settings_dialog.py` | Remove memory references |
| `pet/config.py` | Default provider → `dsh-webapi`; clean deprecated memory keys |
| `pet/vision.py` | Screenshot Q&A: DSH branch (upload → ask → reply) |
| `pet/window.py` | Screen capture: DSH branch |
| `pet/overlay_shell.py` | Screen capture overlay DSH branch; merge self-talk candidates |
| `pet/app.py` | Startup checks: workspace binding, memory plugin, city detection, self-talk |
| `pet/settings_features.py` | Trigger city detection on weather activation |
| `pet/window_alerts.py` | `merge_dsh_texts`: read self-talk from `dsh_self_talk_texts.json` |
| `pet/pack_download.py` | Asset pack URL order (proxy first, GitHub last) |
| `scripts/build_onedir.ps1` | Unify name; add `-SkipAssets` flag |
| `pyproject.toml` | Python 3.14 + uv dependency management |
| `.gitignore` | Add CodeArts, uv, tmp/ |
| `integrations/dsh-pet-memory/lib/index.js` | ① Filter `<system-reminder>` in query cleaner ② queryGate 0.8→0.5 + small-lib guard (<10 memories skip) ③ Workspace dedup in `buildMemoryList` ④ Packed-dir U+FFFD encoding fix |
| `integrations/dsh-pet-memory/lib/client.js` | Settings UI: "session"→"workspace" wording |
| `README.md` | English translation + plugin references |
| `THIRD_PARTY_NOTICES.md` | Remove Android, add self-use components |

### Deleted Files

| File/Dir | Reason |
|---|---|
| `.github/` | No CI/CD needed |
| `android/` | No Android client |
| `update.json` | No auto-update |
| `requirements.txt` | Migrated to pyproject.toml |
| `pet/chat/memory.py` | Pet-side memory (1104 lines) → moved to `@dsh-pet/memory` plugin |
| `pet/chat/memory_recall.py` | Memory recall (531 lines) |
| `pet/chat/memory_extract.py` | Memory extraction (306 lines) |
| `tests/test_chat_memory*.py` | Chat memory tests |

### Configuration

DSH Web API provider config (`config.json`):

```json
{
  "chat": {
    "active_provider": "dsh-webapi",
    "providers": {
      "dsh-webapi": {
        "name": "DSH Web API",
        "base_url": "http://127.0.0.1:3080/api/v1",
        "chat_path": "/chat/completions",
        "api_key": "<DSH API Key>",
        "model": ""
      }
    }
  }
}
```

## License & Acknowledgements

**MIT License** (see [`LICENSE`](LICENSE)). Third-party assets: [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

**Credits:**

- [MerZlin/dsh-pet-indesktop](https://github.com/MerZlin/dsh-pet-indesktop) (MIT, Copyright (c) 2026 Merzlin) — upstream project
- [PC2005-cloud/dsh-pet](https://github.com/PC2005-cloud/dsh-pet) — animation asset basis
- [MeteorNOX/DeepSeek-Balance-Whale-Widget](https://github.com/MeteorNOX/DeepSeek-Balance-Whale-Widget) — balance bubble inspiration
- [Yuuyuko-uu/dsh-fish-memory](https://github.com/Yuuyuko-uu/dsh-fish-memory) — memory plugin basis for `@dsh-pet/memory`
- [huaizhuanghub/dsh-persona-dafeiyu](https://github.com/huaizhuanghub/dsh-persona-dafeiyu) — recommended persona plugin
