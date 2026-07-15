# Release Notes — `3.7.0-my.1`

**Released:** 2026-07-15
**Fork base:** upstream `3.6.1` (commit `5b7d145`)
**Diff vs fork base:** 16 commits, 1,XXX files (run
`git diff --stat 5b7d145..3.7.0-my.1` for the precise count)

---

## What you get

This is the **first tagged release of this fork**. It bundles the upstream
engine at `3.6.1` with 16 fork-specific commits that add:

1. A **decoupled Next.js 16 web cockpit** in `frontend/`
2. A **FastAPI backend** in `facefusion/api/`
3. A new **workflows module** (`image_to_image`, `image_to_video`)
4. **Multi-source face selection** with granular target-face mapping
5. **Real-time job progress** tracking in the API and the UI
6. **Single-frame preview** generation
7. **Atomic JSON writes** + XDG-compliant paths
8. **PII sanitization** in the diagnostic export
9. **Dynamic port discovery** + frontend config injection
10. A **custom dark-mode design system** with glassmorphism, toasts, and a
    slide-comparator video player

For the per-commit breakdown see [`CHANGELOG.md`](CHANGELOG.md).

---

## How to install / upgrade

### Fresh install
```bash
git clone https://github.com/yuri-schmaltz/my-facefusion.git
cd my-facefusion
git checkout 3.7.0-my.1
python install.py
cd frontend && npm install && npm run build && cd ..
python run_api.py
```

### Upgrading from a previous fork snapshot
```bash
git fetch --tags
git checkout 3.7.0-my.1
python install.py               # picks up any new Python deps
cd frontend && npm install && npm run build && cd ..
```

> If you were running the legacy CLI only, no frontend rebuild is required —
> `python facefusion.py …` still works exactly as before.

---

## Known limitations

- **Behind upstream.** Upstream `3.7.0` and `3.7.1` have not been merged.
  See [`docs/UPSTREAM_MERGE.md`](docs/UPSTREAM_MERGE.md) for the planned
  merge procedure.
- **Linux/macOS focus.** Windows is supported by upstream but is not the
  primary development platform for this fork. Issues specific to Windows
  paths in the API layer may surface — please report them.
- **No multi-user / no auth.** The API binds to `127.0.0.1` only and has
  no authentication. Do not expose it to the network without a reverse
  proxy that adds auth.

---

## Credits

- Upstream engine: [facefusion/facefusion](https://github.com/facefusion/facefusion)
- Fork maintainer: [@yuri-schmaltz](https://github.com/yuri-schmaltz)
