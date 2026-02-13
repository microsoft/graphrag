# Release Process

This document describes the end-to-end process for releasing GraphRAG packages.

**Note**: The CI publish workflow (python-publish.yml) is currently non-functional. Packages must be published manually as described below.

## Prerequisites

- Write access to the `microsoft/graphrag` repository.
- Maintainer or owner role on **all** GraphRAG packages on PyPI. 
- `uv` installed locally.
- Dependencies synced: `uv sync --all-packages`.

## 1. Prepare the release

From `main` (or a clean branch off `main`), run the release task:

```sh
uv run poe release
```

This does the following automatically:

1. Runs `semversioner release` — consumes all pending change files and bumps the
   version.
2. Regenerates `CHANGELOG.md`.
3. Updates `project.version` in every package's `pyproject.toml`.
4. Updates cross-package dependency version pins (e.g. `graphrag-common==X.Y.Z`
   in all packages that depend on it).
5. Runs `uv sync --all-packages` to update the lockfile.

## 2. Open and merge the release PR

1. Commit all changes and push to a branch named `release/<version>` (e.g.
   `release/3.1.0`).
2. Open a PR targeting `main`.
3. CI checks (semver, linting, tests) will run automatically.
4. Once approved, merge to `main`.

## 3. Create a GitHub release

1. Go to https://github.com/microsoft/graphrag/releases/new.
2. Create a new tag matching the version (e.g. `v3.1.0`).
3. Target: `main`.
4. Title: the version number (e.g. `v3.1.0`).
5. Use the changelog entry for the release notes, or click "Generate release
   notes".
6. Publish the release.

## 4. Build the packages

Pull the latest `main` to get a clean state, then build:

```sh
git checkout main && git pull
uv sync --all-packages
uv run poe build
```

All wheels and sdists will be in the `dist/` directory.

## 5. Publish to PyPI

Packages must be published in dependency order. The `graphrag` package depends on
all others, so it goes last.

### Generate PyPI tokens

For each package, go to https://pypi.org/manage/account/ and create a
project-scoped API token under **API tokens > Add API token**. Select the
specific project as the scope. Copy the token (starts with `pypi-...`) — it is
only shown once.

### Publish each package

For each package, export its token and publish. Replace `<version>` with the
actual version (e.g. `3.1.0`).

```sh
# 1. graphrag-common (no internal dependencies)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-common>"
uv publish dist/graphrag_common-<version>*

# 2. graphrag-storage (depends on common)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-storage>"
uv publish dist/graphrag_storage-<version>*

# 3. graphrag-chunking (depends on common)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-chunking>"
uv publish dist/graphrag_chunking-<version>*

# 4. graphrag-vectors (depends on common)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-vectors>"
uv publish dist/graphrag_vectors-<version>*

# 5. graphrag-input (depends on common, storage)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-input>"
uv publish dist/graphrag_input-<version>*

# 6. graphrag-cache (depends on common, storage)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-cache>"
uv publish dist/graphrag_cache-<version>*

# 7. graphrag-llm (depends on cache, common)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag-llm>"
uv publish dist/graphrag_llm-<version>*

# 8. graphrag (depends on ALL of the above — publish last)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag>"
uv publish dist/graphrag-<version>*
```

### Verify

After publishing, confirm the new versions are live:

```sh
pip index versions graphrag
```

Or visit https://pypi.org/project/graphrag/ and check each sub-package page.

## Package dependency graph (for reference)

```
graphrag-common          (no internal deps)
├── graphrag-storage     (common)
├── graphrag-chunking    (common)
├── graphrag-vectors     (common)
├── graphrag-input       (common, storage)
├── graphrag-cache       (common, storage)
├── graphrag-llm         (cache, common)
└── graphrag             (all of the above)
```
