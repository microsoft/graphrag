# Release Process

This document describes the end-to-end process for releasing GraphRAG packages.

**Note**: The CI publish workflow (python-publish.yml) is currently non-functional.
Packages must be published manually as described below.

## Prerequisites

- Write access to the `microsoft/graphrag` repository.
- Maintainer or owner role on **all** GraphRAG packages on PyPI.
- A project-scoped PyPI API token (see [PyPI token setup](#generate-pypi-tokens)).
- `uv` installed locally.
- Dependencies synced: `uv sync --all-packages`.

## 1. Prepare the release

Pull the latest changes on `main` and run the release task:

```sh
git checkout main
git pull
uv run poe release
```

This runs the following steps automatically:

1. `semversioner release` -- consumes all pending change files and bumps the
   version.
2. Regenerates `CHANGELOG.md`.
3. Updates `project.version` in every package's `pyproject.toml`.
4. Updates cross-package dependency version pins (e.g. `graphrag-common==X.Y.Z`
   in all packages that depend on it).
5. Runs `uv sync --all-packages` to update the lockfile.

### Cutting a release on Windows

`uv run poe release` does not work on Windows unless you are using WSL. Poe
defaults to `cmd.exe` and there is no straightforward way to force it to use
PowerShell. Run each step manually in PowerShell instead:

```powershell
uv run semversioner release
uv run semversioner changelog > CHANGELOG.md

$version = uv run semversioner current-version
if (-not $version) { Write-Error "Failed to get version"; exit 1 }

uv run update-toml update --file packages/graphrag/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-common/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-chunking/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-input/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-storage/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-cache/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-vectors/pyproject.toml --path project.version --value $version
uv run update-toml update --file packages/graphrag-llm/pyproject.toml --path project.version --value $version

uv run python -m scripts.update_workspace_dependency_versions
uv sync --all-packages
```

## 2. Open and merge the release PR

Check `CHANGELOG.md` or any package's `pyproject.toml` to find the new version,
then move the changes to a release branch:

```sh
git switch -c release/vVERSION
git add .
git commit -m "Release vVERSION"
git tag -a vVERSION -m "Release vVERSION"
git push origin release/vVERSION -u
```

Open a PR targeting `main`. CI checks (semver, linting, tests) will run
automatically. Once approved, merge to `main`.

## 3. Publish to PyPI

Once the PR is merged, switch back to `main`, build, and publish.

You will need a PyPI API token set as the `UV_PUBLISH_TOKEN` environment
variable. See the
[uv docs on publishing](https://docs.astral.sh/uv/guides/package/#building-and-publishing-a-package)
for details.

### Generate PyPI tokens

For each package, go to <https://pypi.org/manage/account/> and create a
project-scoped API token under **API tokens > Add API token**. Select the
specific project as the scope. Copy the token (starts with `pypi-...`) -- it is
only shown once.

If you want to publish all packages with one token and a single `uv publish`
call, create an **account-scoped** token instead of a project-scoped one.

### Build the packages

```sh
git checkout main
git pull
uv sync --all-packages
uv run poe build
```

All wheels and source distributions will be placed in the `dist/` directory.

### Publish all packages at once

This requires an **account-scoped** PyPI token:

```sh
export UV_PUBLISH_TOKEN="pypi-..."
uv publish
```

### Publishing packages individually

If you need to publish packages one at a time (e.g. with separate per-package
tokens), publish them in dependency order. The `graphrag` meta-package depends on
all others, so it goes last.

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

# 8. graphrag (depends on ALL of the above -- publish last)
export UV_PUBLISH_TOKEN="pypi-<token-for-graphrag>"
uv publish dist/graphrag-<version>*
```

### Verify

After publishing, confirm the new versions are live:

```sh
pip index versions graphrag
```

Or visit <https://pypi.org/project/graphrag/> and check each sub-package page.

## 4. Create a GitHub release

1. Go to <https://github.com/microsoft/graphrag/releases/new>.
2. Select the tag you pushed earlier (e.g. `v3.1.0`). Target: `main`.
3. Title: the version number (e.g. `v3.1.0`).
4. Use a previous release as a template for the release notes, or click
   "Generate release notes".
5. Publish the release.

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