#!/usr/bin/env bash
# Simple sequential evaluator for 16 local-search experimental conditions.
# Requirements: bash, python3, pyyaml, md5sum
# Usage:
#   OUTPUT_DIR=/path/to/output \
#   ROOT=/path/to/project \
#   LOG_BASE=./eval_logs \
#   QUERY_FILE=./queries.txt \
#   QUERY_EXEC_TEMPLATE='graphrag query "__QUERY__" --method local --root "__ROOT__" --data "__OUTPUT__" --streaming --verbose' \
#   bash scripts/eval_local_experiment_simple.sh

set -euo pipefail

OUTPUT_DIR="${OUTPUT_DIR:-/path/to/output}"
ROOT="${ROOT:-/path/to/project}"
LOG_BASE="${LOG_BASE:-./eval_logs}"
QUERY_FILE="${QUERY_FILE:-./queries.txt}"

# Replace placeholders:
#  - __QUERY__  -> actual query string
#  - __ROOT__   -> ROOT path
#  - __OUTPUT__ -> OUTPUT_DIR path
QUERY_EXEC_TEMPLATE="${QUERY_EXEC_TEMPLATE:-graphrag query \"__QUERY__\" --method local --root \"__ROOT__\" --data \"__OUTPUT__\" --streaming --verbose}"

if [[ ! -f "$ROOT/settings.yaml" ]]; then
  echo "[ERROR] Missing settings.yaml at ROOT: $ROOT" >&2
  exit 1
fi

if [[ ! -f "$QUERY_FILE" ]]; then
  echo "[ERROR] Missing QUERY_FILE: $QUERY_FILE" >&2
  exit 1
fi

if [[ -z "$QUERY_EXEC_TEMPLATE" ]]; then
  cat >&2 <<'EOF'
[ERROR] QUERY_EXEC_TEMPLATE is required.
Example:
QUERY_EXEC_TEMPLATE='graphrag query "__QUERY__" --method local --root "__ROOT__" --data "__OUTPUT__" --streaming --verbose'
EOF
  exit 1
fi

policies=("leaf_only" "leaf_then_parent_mix" "pyramid" "flat_ranked")
histories=(0 1)
covs=(0 1)

mkdir -p "$LOG_BASE"

cp "$ROOT/settings.yaml" "$ROOT/settings.yaml.bak"
trap 'mv -f "$ROOT/settings.yaml.bak" "$ROOT/settings.yaml"' EXIT

set_local_search_flags() {
  local policy="$1"
  local history_enabled="$2"
  local covariate_enabled="$3"
  python - "$ROOT/settings.yaml" "$policy" "$history_enabled" "$covariate_enabled" <<'PY'
import sys, yaml
path, policy, history, cov = sys.argv[1:]
with open(path, "r", encoding="utf-8") as f:
    data = yaml.safe_load(f) or {}
local = data.setdefault("local_search", {})
local["experiment_enabled"] = True
local["community_selection_policy"] = policy
local["experiment_history_enabled"] = history == "1"
local["experiment_covariate_enabled"] = cov == "1"
local["experiment_history_max_turns"] = 3
local["prompt_logging_enabled"] = True
with open(path, "w", encoding="utf-8") as f:
    yaml.safe_dump(data, f, sort_keys=False, allow_unicode=True)
PY
}

while IFS= read -r q; do
  [[ -z "$q" ]] && continue
  qid=$(echo "$q" | md5sum | awk '{print $1}')

  for p in "${policies[@]}"; do
    for h in "${histories[@]}"; do
      for c in "${covs[@]}"; do
        cond="${p}:h${h}:c${c}"
        run_log_dir="${LOG_BASE}/${qid}/${cond}"
        mkdir -p "$run_log_dir"

        set_local_search_flags "$p" "$h" "$c"

        cmd="${QUERY_EXEC_TEMPLATE//__QUERY__/$q}"
        cmd="${cmd//__ROOT__/$ROOT}"
        cmd="${cmd//__OUTPUT__/$OUTPUT_DIR}"

        bash -lc "$cmd" > "${run_log_dir}/stdout.txt" 2> "${run_log_dir}/stderr.txt" || true

        if [[ -f "$ROOT/logs/query.log" ]]; then
          cp "$ROOT/logs/query.log" "${run_log_dir}/query.log"
        fi
      done
    done
  done
done < "$QUERY_FILE"
