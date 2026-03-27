# Local Search 실험 모드 가이드 (KO)

## 1) 개요

이 문서는 이번에 추가된 **Local Search 실험용 summary-only 모드**의 사용법과 분석 방법을 설명합니다.

실험 모드는 opt-in이며, `experiment_enabled=false`일 때는 기존 local query 동작을 유지합니다.

추가된 핵심 기능:

- 실험 모드 토글 (`experiment_enabled`)
- 커뮤니티 선택 정책:
  - `leaf_only`
  - `leaf_then_parent_mix`
  - `pyramid`
  - `flat_ranked`
- 실험용 대화 히스토리 포함 옵션 (`experiment_history_enabled`)
- 실험용 코바리에이트 포함 옵션 (`experiment_covariate_enabled`)
- 재현 가능한 조건 ID 포맷
- 최종 프롬프트 페이로드 로깅 (`prompt_logging_enabled`)

---

## 2) 설정

`settings.yaml`의 `local_search`에 아래 값을 설정합니다.

```yaml
local_search:
  experiment_enabled: true
  community_selection_policy: leaf_only
  experiment_history_enabled: false
  experiment_covariate_enabled: false
  experiment_history_max_turns: 3
  prompt_logging_enabled: true
```

### 필드 설명

- `experiment_enabled`: `false`면 기존 local-search 경로 사용
- `community_selection_policy`: 4개 정책 중 하나
- `experiment_history_enabled`: 실험 경로에서 히스토리 컨텍스트 포함 여부
- `experiment_covariate_enabled`: 실험 경로에서 코바리에이트 포함 여부
- `experiment_history_max_turns`: 실험 히스토리 포함 턴 수 제한
- `prompt_logging_enabled`: LLM 호출 직전 구조화 payload 로그 출력

---

## 3) 기존 local search 대비 동작 차이

`experiment_enabled=true`일 때:

- Entity retrieval은 기존과 동일하게 수행됨
- 컨텍스트는 **summary-only** 경로로 생성됨
  - 정책 기반 community summary
  - 옵션 기반 history
  - 옵션 기반 covariates
- entity/relationship/text_unit 테이블 컨텍스트는 생성하지 않음
- `context_records`에 `experiment_meta`를 넣어 후속 분석에 활용 가능

`experiment_enabled=false`일 때:

- 기존 local-search 흐름 유지

---

## 4) Condition ID 규칙 (총 16개)

Condition ID 포맷:

```text
<policy>:h<history_enabled>:c<covariate_enabled>
```

예시:

- `leaf_only:h0:c0`
- `leaf_only:h1:c0`
- `pyramid:h1:c1`

총 16개 조건:

- 4개 정책 × history 2개 상태 × covariate 2개 상태

---

## 5) 정책별 의도 요약

### `leaf_only`

- leaf 커뮤니티 우선 선택
- 토큰 여유 시 fallback 우선순위로 추가

### `leaf_then_parent_mix`

- leaf + parent 중심 구성으로 시작
- 부족 시 ranked fallback으로 보강
- 최종 선택 커뮤니티가 1개면 warning 기록

### `pyramid`

- leaf/parent/grandparent 계층 다양성 반영
- 상위 leaf를 우선 포함 후 상위 계층을 순차 반영

### `flat_ranked`

- 계층 무시
- ranked 우선순위대로 선택

---

## 6) 최종 프롬프트 로깅 payload

`prompt_logging_enabled=true`이고 `experiment_meta`가 있으면, LLM 호출 직전에 구조화 payload가 로그로 남습니다.

대표 필드:

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

## 7) 권장 평가 워크플로우

### A) 고정 인덱스 output 준비

모든 조건 비교는 동일한 인덱스 output 디렉터리에서 실행해야 공정합니다.

### B) 조건 매트릭스 반복 실행

16개 조건 각각에 대해:

1. 조건별 설정 반영
2. local query 실행
3. 결과/로그 저장

### C) 결과 집계 분석

수집 항목:

- 모델 응답 텍스트
- 선택된 community ids/titles
- warning 여부
- 토큰 통계
- 최종 prompt payload

---

## 8) query 입력 포맷 요구사항 (중요)

`QUERY_FILE` 기반 토탈 스크립트를 사용할 때 기본 포맷은 다음과 같습니다.

- UTF-8 텍스트 파일
- 한 줄에 질의 1개
- 빈 줄은 템플릿 스크립트에서 무시
- 각 줄은 일반 자연어 질의 문자열로 작성 (JSON 래핑 불필요)

예시 `queries.txt`:

```text
What are the key changes in policy X over time?
Summarize the relationship between Entity A and Entity B.
List unresolved risks mentioned in recent reports.
```

### 메타데이터 포함 포맷 (고급)

질의별 메타데이터가 필요하면 TSV/CSV를 사용하고, 스크립트에서 컬럼 파싱 로직을 직접 넣어야 합니다.

예시:

```text
query_id\tquery_text\tlang
q001\tWhat are top 3 strategic risks?\ten
q002\tSummarize timeline changes for Project K.\ten
```

이 경우 단일 줄 질의 읽기 대신 컬럼 파싱 방식으로 루프를 변경하세요.

### query 명령 입력 형태

query 실행 시 질의는 단일 문자열 인자로 전달합니다.

예시 형태:

```bash
graphrag query \"What are the top risks this quarter?\" --method local ...
```

질의 문자열에 따옴표, 파이프(`|`), `$`, 백틱 등이 포함되면 shell escaping/quoting을 신경 써야 합니다.

---

## 9) 토탈 평가 스크립트 템플릿 (심플 버전, bash)

```bash
#!/usr/bin/env bash
set -euo pipefail

OUTPUT_DIR="/path/to/output"
ROOT="/path/to/project"
LOG_BASE="./eval_logs"
QUERY_FILE="./queries.txt"

policies=("leaf_only" "leaf_then_parent_mix" "pyramid" "flat_ranked")
histories=(0 1)
covs=(0 1)

mkdir -p "$LOG_BASE"

# settings 백업 1회
cp "${ROOT}/settings.yaml" "${ROOT}/settings.yaml.bak"
trap 'mv -f "${ROOT}/settings.yaml.bak" "${ROOT}/settings.yaml"' EXIT

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

        # settings를 제자리에서 간단히 변경
        set_local_search_flags "$p" "$h" "$c"

        # 환경에 맞는 실제 실행 명령으로 교체
        # graphrag query "$q" --method local --root "$ROOT" --data "$OUTPUT_DIR" --streaming --verbose \
        #   > "${run_log_dir}/stdout.txt" 2> "${run_log_dir}/stderr.txt" || true

        if [[ -f "${ROOT}/logs/query.log" ]]; then
          cp "${ROOT}/logs/query.log" "${run_log_dir}/query.log"
        fi
      done
    done
  done
done < "$QUERY_FILE"
```

레포에 포함된 실행 스크립트를 바로 사용해도 됩니다:

```bash
bash scripts/eval_local_experiment_simple.sh
```

주의:

- 이 스크립트는 의도적으로 단순/순차 실행용입니다.
- 같은 `ROOT`를 대상으로 병렬 실행하면 안 됩니다 (`settings.yaml` 하나를 공유해 수정하기 때문).
- 이 버전은 Python + PyYAML 기반이며 `yq`가 필요 없습니다.

---

## 10) 5가지 상호보완 평가 방법

1. **Summary-only 안전성 검사**
   - 실험 컨텍스트에 full content가 포함되지 않는지 검증
2. **History 토글 충실도 검사**
   - history on일 때만 history 컨텍스트 존재하는지 검증
3. **Covariate 토글 충실도 검사**
   - covariate on일 때만 covariate 테이블 존재하는지 검증
4. **정책 결과 무결성/다양성 검사**
   - 정책 의도와 선택 결과의 일치성, 중복 ID, warning 패턴 점검
5. **토큰 영향도 분석**
   - 정책/히스토리/코바리에이트 조합별 토큰 분포 비교

---

## 11) 검증된 10회 반복 평가 (스모크 검증)

실험 컨텍스트 경로에 대해 정책/히스토리/코바리에이트/토큰 예산을 섞은 10개 케이스 반복 평가를 수행했고, 모든 케이스에서 아래 점검 항목을 통과했습니다.

- summary-only 강제 (full content 누수 없음)
- history 토글 정확성
- covariate 토글 정확성
- selected community id dedup 보장
- 실험 모드에서 local entity/relationship/text-unit 테이블 미생성

관측 결과:

- `total_cases = 10`
- `passed_cases = 10`
- `failed_cases = []`

권장 재실행 명령 형태:

```bash
PYTHONPATH=packages/graphrag python your_10_case_eval_script.py
```

---

## 12) 토탈 스크립트 결과 분석 방법

### 권장 로그 구조

- `stdout.txt`: 모델 응답
- `stderr.txt`: 경고/에러
- `query.log`: 구조화 payload 포함 로그

### 집계 추천 컬럼

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

### 실무 점검 포인트

- 16개 조건 모두 실행되었는가?
- payload 누락 케이스는 없는가?
- selected community id 중복이 있는가?
- 토큰 이상치(outlier)가 특정 조건에 몰리는가?
- 정책별 답변 품질/일관성 차이가 있는가?

---

## 13) 로그 확인 방법 (빠른 명령)

```bash
# payload 로그 검색
grep -n "local_search_prompt_payload" eval_logs/**/query.log

# condition id별 건수
jq -r '.experiment_condition_id' eval_logs/**/payload.jsonl | sort | uniq -c

# warning 발생 건수
jq -r 'select(.warning==true) | .experiment_condition_id' eval_logs/**/payload.jsonl | wc -l
```

로그가 prefix 문자열과 함께 저장되면 prefix 제거 후 `jq`를 사용하세요.

---

## 14) 트러블슈팅

- payload가 안 찍힘:
  - `prompt_logging_enabled=true` 확인
  - `experiment_enabled=true` 확인
- 조건별 결과 차이가 없음:
  - 실행마다 settings가 실제로 바뀌었는지 확인
  - 조건별 root 경로로 실행했는지 확인
- 정책 결과가 기대와 다름:
  - payload의 selected ids/titles, warnings 확인
  - 토큰 예산 및 fallback 동작 여부 확인

---

## 15) 재현성 체크리스트

- 고정된 인덱스 output 사용
- 고정된 query 세트 사용
- condition id 규칙 일관 적용
- 전체 로그/페이로드 보관
- 코드 브랜치/커밋 해시 고정
