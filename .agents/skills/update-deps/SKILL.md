---
name: update-deps
description: >
  Update this GraphRAG uv-workspace monorepo's dependencies and repair the resulting
  breakages so every check and test passes again. Use when asked to update, upgrade, or
  bump dependencies/packages/versions, refresh or regenerate the lockfile, migrate to a new
  major of pandas/numpy/pydantic/pyarrow, resolve dependency-related test or lint failures,
  or run a "dependency sweep" — even if the user only names a single package. Covers editing
  pyproject.toml version specifiers across the root dev-deps and every packages/* member,
  re-locking with uv, and fixing code and tests for library API changes (e.g. pandas 3.0).
  USE FOR: update dependencies, upgrade packages, bump versions, dependency sweep, uv lock,
  uv sync, refresh lockfile, migrate pandas/numpy, "deps broke the tests", pyproject bump.
user-invocable: true
---

# Update Dependencies (GraphRAG monorepo)

## Goal

Raise dependency versions across this uv workspace, re-lock, and fix any code or test
fallout until `uv run poe check` and `uv run poe test_unit` are both green — without
touching the version machinery that the release process owns.

## Hard rules (non-negotiable)

1. **Only the Microsoft feed proxy.** All resolves and syncs MUST use
   `https://packagefeedproxy.microsoft.io/pypi/simple` (the `[[tool.uv.index]]` configured in
   the root `pyproject.toml`). Never resolve against public PyPI, never add
   `--index`/`--default-index`/`--index-url` overrides, and never set `UV_INDEX_URL` or
   `PIP_INDEX_URL` to pypi.org. Do not disable or reorder the configured index.
2. **Target versions must be at least 7 days old.** Only bump to a version that was released
   more than 7 days ago. The proxy does not serve versions published within the last week —
   syncing to a too-new version WILL fail. Before pinning a specific version, verify its
   release date and pick the newest release older than 7 days; otherwise let the specifier
   float and let `uv lock` choose (it can only see eligible versions on the proxy anyway).

## Layout facts

- This is a **uv workspace monorepo**. The root [`pyproject.toml`](../../../pyproject.toml)
  holds the `dev` group under `[dependency-groups]` and the `[tool.poe.tasks]` commands.
- Runtime dependencies live in each member's `packages/*/pyproject.toml` under
  `[project] dependencies`.
- Workspace members are wired via `[tool.uv.sources]` (`{ workspace = true }`) and pinned to
  each other with `graphrag-*==X.Y.Z` lines.
- Package resolution goes through a Microsoft-internal index (`[[tool.uv.index]]`); expect
  that feed to be used, not public PyPI directly.

## Do NOT edit these (release-owned)

1. **Cross-package pins** `graphrag-cache==...`, `graphrag-llm==...`, etc. in any package.
   These are rewritten automatically by
   [`scripts/update_workspace_dependency_versions.py`](../../../scripts/update_workspace_dependency_versions.py)
   from the semversioner version. Hand-editing them causes drift.
2. **`[project] version` fields** — managed by semversioner ("do not change the version
   here manually").
3. **`graspologic-native>=1.2,<1.3`** — held below 1.3 on purpose; 1.3.x changes Leiden
   clustering output and breaks golden regression data. Only bump with a deliberate
   golden-data refresh, and say so explicitly.

## Process

1. **Baseline first.** Confirm a clean working tree and that checks/tests already pass
   before changing anything, so later failures are attributable to the bump:
   - `uv run poe check`
   - `uv run poe test_unit`
     Prefer a dedicated branch (e.g. `dep-sweep`).

2. **Decide the scope.** Either a targeted set of packages the user named, or a full sweep.
   Edit the `~=`/`>=`/`<` specifiers in the relevant `[project] dependencies`
   (`packages/*/pyproject.toml`) and the root `dev` group. Leave the release-owned lines
   above untouched.

3. **Resolve and lock.** All of these use the configured Microsoft feed proxy — do not pass
   any index override (see Hard rules).
   - For a full "get latest allowed" pass: `uv lock --upgrade`.
   - For targeted bumps after editing specifiers: `uv lock`.
   - Then install: `uv sync --all-packages`.
     If resolution fails, read the conflict, relax/adjust the offending specifier, and re-lock.
     Do not delete `uv.lock` to force it.
   - If a sync fails to find a version you just pinned, it is almost certainly younger than 7
     days on the proxy — step down to the newest release older than one week.

4. **Static checks.** Run `uv run poe check` (this is `ruff format --check` + `ruff check` +
   `pyright`). Apply safe autofixes with `uv run poe fix`; format with `uv run poe format`.
   Fix remaining lint/type errors by hand — see Gotchas and the migration reference.

5. **Tests.** Run `uv run poe test_unit` (NOT `uv run poe test`, which runs the full coverage
   suite). Run `uv run poe test_verbs` and `uv run poe test_integration` when the change is
   broad or touches indexing/query. Investigate every new failure.

6. **Repair breakages.** For test/type failures caused by a library's API change, load
   [`references/migration-gotchas.md`](references/migration-gotchas.md) and apply the
   documented pattern. Keep fixes minimal and consistent with sibling code; prefer a real
   fix over a `# noqa`.

7. **Record the change.** Add a changelog entry:
   `uv run semversioner add-change -t patch -d "<short description>"` (use `minor`/`major`
   only if the user's intent warrants it).

8. **Final verification.** Re-run `uv run poe check` and `uv run poe test_unit`; both must be
   green (see the known-flake note below before calling a failure a regression).

## Gotchas (this repo)

- **`test_unit`, not `test`.** `poe test` runs coverage over everything and is slow; use
  `test_unit` for the fast feedback loop.
- **Ruff runs in preview mode** (`preview = true`, `target-version = "py310"`). Preview-only
  rules such as `RUF069` (float equality) and `ASYNC119` fire here even though they may not
  in other repos.
- **Known pre-existing flake:**
  `tests/unit/indexing/test_profiling.py::TestWorkflowProfiler::test_handles_exception_in_context`
  is timing-sensitive and can fail intermittently — it is not a dependency regression.
- **`uv sync --all-packages`** (not bare `uv sync`) to install every workspace member.
- **pandas is on the 3.0 line and numpy on 2.x.** Their major-version API changes are the
  usual source of post-bump breakage — see the reference file.
- Version-bump edits touch many `pyproject.toml` files; make sure you did not accidentally
  modify a `graphrag-*==` pin or a `version` field while editing nearby specifiers.

## Load-on-demand reference

When a bump breaks tests or type-checking with a library API change (especially pandas or
numpy), read [`references/migration-gotchas.md`](references/migration-gotchas.md) for
verified, repo-specific fix patterns before improvising.

## Completion checklist

- [ ] All resolves/syncs used the `packagefeedproxy.microsoft.io` index; no public-PyPI or
      index-override was introduced.
- [ ] No dependency was bumped to a version released within the last 7 days.
- [ ] Only intended specifiers changed; no `graphrag-*==` pin or `version` field edited.
- [ ] `uv.lock` regenerated via `uv lock`/`uv lock --upgrade` (not hand-edited or deleted).
- [ ] `uv run poe check` passes (ruff format, ruff lint, pyright).
- [ ] `uv run poe test_unit` passes (ignoring only the known profiling flake).
- [ ] Broader suites run if the change was broad (`test_verbs`/`test_integration`).
- [ ] A semversioner changelog entry was added.
- [ ] Any risky/held pin (e.g. `graspologic-native`) left in place unless explicitly bumped.
