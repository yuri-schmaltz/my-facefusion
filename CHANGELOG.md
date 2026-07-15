# Changelog

All notable changes to this fork are documented in this file.

The format is loosely based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/) for the
fork-specific portion of the version (`-my.X`).

> **Upstream:** This is a fork of [`facefusion/facefusion`](https://github.com/facefusion/facefusion).
> Upstream releases and their notes live at <https://github.com/facefusion/facefusion/releases>.
> Only **fork-specific** changes appear here; for upstream changes, consult the
> corresponding upstream release notes (see the "Upstream divergence" section in `README.md`).

---

## [3.7.0-my.1] — 2026-07-15

**Fork base:** upstream `3.6.1` (commit `5b7d145`).
**Status:** First tagged release of this fork. Brings the codebase in line with
upstream `3.6.1` plus 16 fork-specific commits. **Behind** upstream `3.7.0` / `3.7.1`
(those upstream releases have **not** been merged into this fork yet — see
"Upstream divergence" below).

### ✨ Highlights

- **New: Decoupled Web UI (Cockpit).** A Next.js 16 frontend replaces the Gradio
  monolithic UI. The frontend is statically exported and served by FastAPI,
  communicating with the backend exclusively through a documented REST API
  (`/api/...`).
- **New: FastAPI backend layer.** Added `facefusion/api/` (database, routes,
  worker, main) and a `run_api.py` entrypoint that auto-discovers a free TCP
  port and publishes the URL to the frontend.
- **New: Workflows module.** Added `facefusion/workflows/` with dedicated
  pipelines for `image_to_image` and `image_to_video`, including a modernized
  type system and standardized translation handling.
- **New: Multi-source face selection + granular face mapping.** Submit multiple
  source images and choose exactly which detected face in the target receives
  which source face.
- **New: Real-time job progress tracking.** Jobs now expose a `progress` field
  (0–100) that updates while the worker is running, and the frontend polls it
  every 2 s.
- **New: Single-frame preview (auto + manual).** Generate a quick preview of
  the swap on a single frame before committing to a full render.
- **New: Diagnostic export endpoint with PII sanitization.** Downloads a ZIP
  bundle of logs, configs and system info, with all local user paths
  (`/home/<user>`, `C:\Users\<user>`) masked to `/home/user` / `C:\Users\user`.
- **New: Atomic JSON writes + XDG-compliant path management** to prevent
  half-written config files and to respect platform conventions.
- **New: Backend logger + custom frontend design system** (dark mode, glass
  surfaces, semantic status colors, toast notifications, slide-comparator
  video player).
- **New: Explicit application context** (`cli` vs `ui`) wired through
  `facefusion.app_context` so code paths that must differ between modes are
  deterministic.

### 🛠 Changed

- **API endpoint refactor** (`1c1f741`) — frontend layout optimized for
  responsive display.
- **FFmpeg process robustness** (`18a4a3a`) — better job path resolution and
  file-download tracking.
- **Environment initialization** (`368e13f`) — added GPU memory limit and
  refreshed the frontend video comparator.
- **Frontend static export mount** (`f740f0b`) — Next.js build is now served
  directly by FastAPI; build binaries are git-ignored.
- **Default thread count** is now set in core (`dd90887`).
- **Processor pre-check validation** added before kickoff (`dd90887`) — early
  fail with a clear error message instead of a mid-run crash.

### 🐛 Fixed

- **FFmpeg test invocations** now pass `-y` so existing outputs can be
  overwritten (`1ff545f`).
- **Test fixtures** hardened with null checks and explicit boolean
  type-casting (`6d86b16`).

### 🧹 Housekeeping

- `.new_jobs_path_test/` removed from the working tree and added to
  `.gitignore` to prevent re-leaking test scaffolding.
- `.gitignore` extended to cover `frontend/.next/`, `frontend/out/`,
  `frontend/node_modules/`, `out/`, `tmp/`, local `*.ini` overrides, and
  common OS/editor noise.
- `facefusion/__init__.py` previously empty; now declares
  `version = "3.7.0-my.1"` and metadata so the Python package is
  introspectable.

### ⬆️ Upstream divergence

| Upstream tag | Merged into this fork? |
|---|---|
| `3.6.0` | ✅ (commit `57fcb86`) |
| `3.6.1` | ✅ (commit `5b7d145`) — **fork base** |
| `3.7.0` | ❌ pending |
| `3.7.1` | ❌ pending |

A merge of upstream `3.7.0` + `3.7.1` is the next planned item. See
[README.md § Upstream divergence](README.md#upstream-divergence) for the
strategy and reproduction commands.

---

## Pre-fork history

Inherited from upstream `facefusion/facefusion`. See upstream
[`CHANGELOG.md`](https://github.com/facefusion/facefusion/blob/master/CHANGELOG.md)
for everything before `3.6.1`.
