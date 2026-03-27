# Local Search Experimental Mode Guide (EN)

## 1) Overview

This guide explains how to use and analyze the recently added **Local Search experimental summary-only mode**.

The mode is opt-in and preserves default local-query behavior unless enabled.

Core capabilities introduced:

- Experimental mode toggle (`experiment_enabled`)
- Community selection policies:
  - `leaf_only`
  - `leaf_then_parent_mix`
  - `pyramid`
  - `flat_ranked`
- Optional experimental conversation history (`experiment_history_enabled`)
- Optional experimental covariate context (`experiment_covariate_enabled`)
- Deterministic condition id format for reproducibility
- Final prompt payload logging (`prompt_logging_enabled`)

---

## 2) Configuration

Set values in `settings.yaml` under `local_search`:

```yaml
local_search:
  experiment_enabled: true
  community_selection_policy: leaf_only
  experiment_history_enabled: false
  experiment_covariate_enabled: false
  experiment_history_max_turns: 3
  prompt_logging_enabled: true
```

### Field descriptions

- `experiment_enabled`: if `false`, existing local-search path is used.
- `community_selection_policy`: one of the four policies listed above.
- `experiment_history_enabled`: include conversation history table in experimental mode.
- `experiment_covariate_enabled`: include covariate table(s) in experimental mode.
- `experiment_history_max_turns`: max QA turns included for history in experiment mode.
- `prompt_logging_enabled`: emit structured final-prompt payload log.

---

## 3) Behavior differences from default local search

When `experiment_enabled=true`:

- Entity retrieval still runs (same query-to-entity mapping / top-k mechanism).
- Context is built in **summary-only style**:
  - community summaries selected by policy
  - optional history
  - optional covariates
- Entity/relationship/text-unit context tables are not generated in this path.
- `context_records` contains `experiment_meta` for downstream logging/analysis.

When `experiment_enabled=false`:

- Existing local-search flow remains unchanged.

---

## 4) Condition ID convention (16 conditions)

Condition ID format:

```text
<policy>:h<history_enabled>:c<covariate_enabled>
```

Examples:

- `leaf_only:h0:c0`
- `leaf_only:h1:c0`
- `pyramid:h1:c1`

This yields 16 conditions total:

- 4 policies × 2 history states × 2 covariate states

---

## 5) Policy intent summary

### `leaf_only`

- Prioritize leaf communities first.
- If budget remains, fill using fallback priority ordering.

### `leaf_then_parent_mix`

- Start from leaf + parent-oriented composition.
- Fallback fills from ranked candidates.
- Warning is emitted if final selected community count is only one.

### `pyramid`

- Encourage hierarchical diversity (leaf/parent/grandparent).
- Ensure top leaf inclusion first, then higher levels as available.

### `flat_ranked`

- Ignore level hierarchy.
- Select by ranked priority order only.

---

## 6) Final prompt logging payload

When `prompt_logging_enabled=true` and experimental metadata exists, a structured payload is logged right before LLM invocation.

Typical fields:

- `experiment_condition_id`
- `selection_policy`
- `history_on`
- `covariate_on`
- `query`
- `selected_community_ids`
- `selected_community_titles`
- `warning`
- `warning_messages`
- `token_count_context`
- `final_system_prompt`

---

## 7) Recommended evaluation workflow

### Step A: Prepare a fixed index output directory

Use the same indexed output for all runs for fair comparison.

### Step B: Iterate condition matrix

For each of 16 conditions:

1. Set condition values in settings (or per-run settings copy)
2. Run local query
3. Save outputs and logs

### Step C: Aggregate results

Collect:

- model answer text
- selected community ids/titles
- warning flags
- token stats
- full prompt payload

---

## 8) Query input format requirements (important)

If you run the total script with `QUERY_FILE`, the expected format is:

- UTF-8 text file
- one query per line
- empty lines are ignored by the template script
- keep each line as a plain natural-language query (no JSON wrapper required)

Example `queries.txt`:

```text
What are the key changes in policy X over time?
Summarize the relationship between Entity A and Entity B.
List unresolved risks mentioned in recent reports.
```

### Optional metadata format (advanced)

If you need per-query metadata, use TSV/CSV and parse it in your script explicitly.
For example:

```text
query_id\tquery_text\tlang
q001\tWhat are top 3 strategic risks?\ten
q002\tSummarize timeline changes for Project K.\ten
```

Then update the loop to parse columns instead of reading a raw single-line query.

### Query command input shape

When calling your query command, pass the query as a single string argument.

Example shape:

```bash
graphrag query \"What are the top risks this quarter?\" --method local ...
```

If your query contains shell-sensitive characters (quotes, pipes, `$`, backticks), wrap carefully or escape.

---

## 9) Total evaluation script template (simple, bash)

Use the bundled script directly:

```bash
OUTPUT_DIR="/path/to/output"
ROOT="/path/to/project"
LOG_BASE="./eval_logs"
QUERY_FILE="./queries.txt"
QUERY_EXEC_TEMPLATE='graphrag query "__QUERY__" --method local --root "__ROOT__" --data "__OUTPUT__" --streaming --verbose'
bash scripts/eval_local_experiment_simple.sh
```

Note:

- This is intentionally simple and sequential.
- Do not run multiple copies of this script concurrently on the same `ROOT` (it edits one shared `settings.yaml`).
- The helper script uses Python + PyYAML and does not require `yq`.

---

## 10) Five complementary evaluation methods

Use all five for robust analysis:

1. **Summary-only safety check**
   - Ensure full content fields never appear in experimental context.
2. **History toggle fidelity**
   - `history_on` should only appear when enabled.
3. **Covariate toggle fidelity**
   - Covariate table should only appear when enabled.
4. **Policy outcome integrity/diversity**
   - Verify selected communities align with policy intent.
   - Check duplicate IDs and warning behavior.
5. **Token impact analysis**
   - Compare token count distributions by policy/history/covariate.

---

## 11) Verified 10-case repeat evaluation (smoke validation)

We ran a 10-case repeat evaluation against the experimental context path (policy/history/covariate/token-budget variations) and validated all checks below for every case:

- summary-only enforcement (no full content leakage)
- history toggle correctness
- covariate toggle correctness
- selected community id deduplication
- no local entity/relationship/text-unit tables in experiment mode

Observed result:

- `total_cases = 10`
- `passed_cases = 10`
- `failed_cases = []`

Recommended rerun command shape:

```bash
PYTHONPATH=packages/graphrag python your_10_case_eval_script.py
```

---

## 12) How to analyze total script outputs

### Suggested directory conventions

- `stdout.txt`: model answer stream
- `stderr.txt`: runtime warnings/errors
- `query.log`: structured logs including prompt payload

### Suggested aggregate columns

- `query_id`
- `condition_id`
- `policy`
- `history_on`
- `covariate_on`
- `selected_community_ids`
- `warning`
- `token_count_context`
- `answer_length`
- `latency`

### Practical checks

- 16 condition coverage complete?
- Any missing log payload rows?
- Any duplicate selected community ids?
- Token outliers by condition?
- Answer quality drift patterns by policy?

---

## 13) Log inspection quick commands

```bash
# Find payload entries
grep -n "local_search_prompt_payload" eval_logs/**/query.log

# Count by condition id
jq -r '.experiment_condition_id' eval_logs/**/payload.jsonl | sort | uniq -c

# Check warning rate
jq -r 'select(.warning==true) | .experiment_condition_id' eval_logs/**/payload.jsonl | wc -l
```

If logs are plain lines with prefix text, strip prefix before `jq`.

---

## 14) Troubleshooting

- Missing payload logs:
  - Check `prompt_logging_enabled=true`
  - Check `experiment_enabled=true`
- No behavior difference across conditions:
  - Verify settings were actually updated per run.
  - Confirm your run command points to each per-condition root.
- Unexpected policy output:
  - Inspect selected community IDs/titles and warnings from payload.
  - Compare token budgets and fallback activation patterns.

---

## 15) Reproducibility checklist

- Fixed indexed output directory
- Fixed query set
- Deterministic condition id usage
- Captured full logs + payloads
- Version-pinned code branch and commit hash
