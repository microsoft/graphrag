# Migration Gotchas — verified fixes for this repo

Load this when a dependency bump breaks tests or `pyright`/`ruff` with a library API change.
Each entry is a pattern that was actually hit and fixed in this codebase. Apply the minimal
fix and keep it consistent with sibling code.

## pandas 3.0

### `DataFrame.swapaxes` removed → `np.array_split(df, n)` returns ndarrays

`np.array_split` internally calls `np.swapaxes`, which used to delegate to
`DataFrame.swapaxes` and return DataFrames with column names intact. In pandas 3.0
`swapaxes` was removed (deprecated in 2.1), so `np.array_split(df, n)` now yields plain
numpy arrays. Rebuilding with `pd.DataFrame(fold)` produces integer `RangeIndex` columns,
so later `df["some_column"]` raises `KeyError`.

Symptom: `KeyError: '<column>'` with a traceback ending in
`pandas/core/indexes/range.py ... get_loc`.

Fix — split positional indices instead of the frame, then select rows with `iloc`:

```python
# Broken under pandas 3.0
return [pd.DataFrame(fold) for fold in np.array_split(reports, n)]

# Fixed — preserves columns, dtypes, and even fold sizes
return [reports.iloc[indices] for indices in np.array_split(np.arange(len(reports)), n)]
```

### `copy=` keyword removed from `merge`/`concat`/`join`/`set_axis` etc.

pandas 3.0 makes Copy-on-Write the default and drops the `copy=` parameter. Calls like
`df.merge(other, copy=False)` or `pd.concat([...], copy=False)` raise `TypeError`.
Fix: delete the `copy=` argument — CoW already avoids the unnecessary copy.

### Chained-assignment / `inplace` under Copy-on-Write

With CoW, mutating a slice (`df[mask]["col"] = x`) no longer writes back and may warn/error.
Assign through `.loc`: `df.loc[mask, "col"] = x`. Reassign results of `inplace=True`-style
operations rather than relying on in-place mutation of a view.

## numpy 2.x

- Removed aliases (`np.float_`, `np.int0`, `np.bool8`, `np.object0`, etc.) — use the builtin
  or the explicit sized dtype (`np.float64`, `np.bool_`).
- `np.array_split` on a DataFrame no longer preserves the frame (see the pandas entry above).
- Some functions moved out of the top-level namespace; import from the documented submodule.

## ruff (preview mode active in this repo)

- **RUF069 (float-equality-comparison):** `x == 0.0` / `!= 0.0` is flagged. Prefer a
  non-equality guard when semantically valid (`x <= 0.0` for a non-positive divide guard) or
  `math.isclose(...)` for tolerance checks. Avoid a blanket `# noqa` when a real fix exists.
- **ASYNC119 (yield in context manager in async generator):** do not `yield` while holding a
  `with`/`async with` in an async generator. Materialize inside the block, then yield after
  it closes — matching the sibling providers:

  ```python
  with Path.open(path, "r", encoding=enc) as f:
      rows = list(csv.DictReader(f))
  for row in rows:
      yield transform(row)
  ```

## pyright

- Type stubs travel with majors: the `dev` group pins `pandas-stubs~=3.0`. When bumping
  pandas, bump the matching stubs so `pyright` reflects the new API.
- After dependency changes, `pyright` may surface new optional/overload errors from updated
  stubs; fix at the call site rather than suppressing, unless the stub is demonstrably wrong.

## General approach

1. Read the actual traceback/diagnostic to the leaf frame — the failing library call and the
   changed symbol are usually right there.
2. Check how a sibling module in the same package already handles the pattern and match it.
3. Prefer a real, minimal fix over suppression; re-run `uv run poe check` and
   `uv run poe test_unit` after each fix to confirm.
