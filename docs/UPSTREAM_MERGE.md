# Upstream Merge Playbook

This document is the operational runbook for bringing new upstream
[facefusion/facefusion](https://github.com/facefusion/facefusion) releases
into this fork without losing the fork-specific work in `facefusion/api/`,
`facefusion/workflows/`, `frontend/`, and the docs in `docs/goal/`.

> **TL;DR:** Use a dedicated branch per upstream release, merge the upstream
> tag, resolve conflicts, run the test suite, then tag a new
> `-my.X` release.

---

## 1. Add / refresh the upstream remote

```bash
git remote -v                         # check current remotes
git remote add upstream https://github.com/facefusion/facefusion.git 2>/dev/null \
  || git remote set-url upstream https://github.com/facefusion/facefusion.git
git fetch --tags upstream
```

---

## 2. Cut a merge branch from current `master`

```bash
git checkout master
git pull --ff-only
git checkout -b merge/upstream-3.7.0
```

---

## 3. Merge the upstream tag

```bash
git merge --no-ff upstream/3.7.0 -m "merge upstream 3.7.0"
```

If there are conflicts, work through them in this order (most → least
likely to conflict):

1. `facefusion/uis/` — the legacy Gradio UI; we did not touch it but the
   upstream usually does.
2. `facefusion/jobs/` (we split this out of `facefusion/jobs.py`) — both
   sides refactored this area in `3.6.x` and `3.7.x`.
3. `facefusion/choices.py` — we added the processor pre-check; upstream
   occasionally adds new processor choices too.
4. `facefusion/processors/frame_enhancer.py` and the rest of the
   `processors/` package — usually conflict-free, but check.
5. `requirements.txt` — accept the upstream version, then re-add any
   fork-only dependency (`uvicorn`, `fastapi`, `sqlalchemy`, etc.) that
   the API layer needs.

---

## 4. Smoke tests

```bash
# Python engine CLI (legacy path)
python facefusion.py --help
python facefusion.py job-list

# API + frontend boot
cd frontend && npm install && npm run build && cd ..
python run_api.py &
# Hit the API root and confirm 200
curl -fsSL http://127.0.0.1:8000/api/hardware/providers | jq .

# Test suite
pytest -q tests/
```

If any smoke step fails, **do not** tag a release — fix on the merge branch
and re-run.

---

## 5. Tag the new fork release

```bash
# Bump the version in facefusion/__init__.py
#   version = "3.7.0-my.2"
git add facefusion/__init__.py
git commit -m "chore: bump fork version to 3.7.0-my.2"

# Tag & push
git tag -a 3.7.0-my.2 -m "FaceFusion fork 3.7.0-my.2 — merged upstream 3.7.0"
git push origin merge/upstream-3.7.0
git push origin 3.7.0-my.2
```

---

## 6. Update `CHANGELOG.md`

Add a new top-level section summarising:

- The upstream version merged in.
- The fork-specific commits that landed since the previous `-my.X` tag.
- Any merge-conflict decisions worth recording (e.g. *"kept fork X over
  upstream Y because Z"*).

---

## 7. Open a PR from `merge/upstream-3.7.0` → `master`

Use the generated `CHANGELOG.md` diff as the PR description body. This makes
the diff between fork releases auditable in one place.

---

## Appendix: release matrix

| Fork tag      | Upstream base | Date         |
|---------------|---------------|--------------|
| `3.7.0-my.1`  | `3.6.1`       | 2026-07-15   |
| `3.7.0-my.2`  | `3.7.0`       | _planned_    |
| `3.7.1-my.1`  | `3.7.1`       | _planned_    |
