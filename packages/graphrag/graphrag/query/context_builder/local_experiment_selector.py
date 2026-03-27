# Copyright (c) 2024 Microsoft Corporation.
# Licensed under the MIT License

"""Community selection policies for local-search experimental summary context."""

from dataclasses import dataclass

from graphrag_llm.tokenizer import Tokenizer

from graphrag.data_model.community import Community
from graphrag.data_model.community_report import CommunityReport


@dataclass
class SelectionResult:
    """Selection result envelope for experimental policy path."""

    selected_reports: list[CommunityReport]
    warnings: list[str]
    debug: dict[str, object]


def is_leaf(community: Community) -> bool:
    """Return true when community has no children."""
    return not community.children


def _is_leaf_id(community_by_id: dict[str, Community], community_id: str) -> bool:
    community = community_by_id.get(community_id)
    return bool(community and is_leaf(community))


def sort_reports_by_priority(
    reports: list[CommunityReport],
    community_matches: dict[str, int],
) -> list[CommunityReport]:
    """Re-use mixed-context priority ordering (matches, rank desc)."""
    return sorted(
        reports,
        key=lambda report: (
            community_matches.get(report.community_id, 0),
            report.rank or 0,
        ),
        reverse=True,
    )


def get_parent_chain(
    community_id: str,
    community_by_id: dict[str, Community],
) -> list[Community]:
    """Return ancestors from parent to root."""
    chain: list[Community] = []
    current = community_by_id.get(community_id)
    visited: set[str] = set()

    while current and current.parent and current.parent not in visited:
        visited.add(current.parent)
        parent = community_by_id.get(current.parent)
        if not parent:
            break
        chain.append(parent)
        current = parent

    return chain


def can_fit_community_summary(
    tokenizer: Tokenizer,
    report: CommunityReport,
    token_budget: int,
) -> bool:
    """Approximate per-community token fit from summary payload."""
    content = f"{report.title}|{report.summary}\n"
    return tokenizer.num_tokens(content) <= token_budget


def _fill_with_fallback(
    selected_ids: set[str],
    selected: list[CommunityReport],
    ranked_reports: list[CommunityReport],
    tokenizer: Tokenizer,
    token_budget: int,
) -> bool:
    used_fallback = False
    remaining = token_budget - sum(
        tokenizer.num_tokens(f"{report.title}|{report.summary}\n") for report in selected
    )
    for report in ranked_reports:
        if report.community_id in selected_ids:
            continue
        if can_fit_community_summary(tokenizer, report, remaining):
            selected_ids.add(report.community_id)
            selected.append(report)
            remaining -= tokenizer.num_tokens(f"{report.title}|{report.summary}\n")
            used_fallback = True
    return used_fallback


def _collect_fit(
    candidates: list[CommunityReport],
    tokenizer: Tokenizer,
    token_budget: int,
) -> list[CommunityReport]:
    selected: list[CommunityReport] = []
    seen_ids: set[str] = set()
    remaining = token_budget
    for report in candidates:
        if report.community_id in seen_ids:
            continue
        if can_fit_community_summary(tokenizer, report, remaining):
            selected.append(report)
            seen_ids.add(report.community_id)
            remaining -= tokenizer.num_tokens(f"{report.title}|{report.summary}\n")
    return selected


def select_leaf_only(
    ranked_reports: list[CommunityReport],
    community_by_id: dict[str, Community],
    tokenizer: Tokenizer,
    token_budget: int,
) -> SelectionResult:
    leaves = [
        report
        for report in ranked_reports
        if _is_leaf_id(community_by_id, report.community_id)
    ]
    selected = _collect_fit(leaves, tokenizer, token_budget)
    selected_ids = {report.community_id for report in selected}
    used_fallback = _fill_with_fallback(
        selected_ids, selected, ranked_reports, tokenizer, token_budget
    )
    return SelectionResult(
        selected_reports=selected,
        warnings=[],
        debug={
            "policy": "leaf_only",
            "candidate_count": len(ranked_reports),
            "leaf_candidate_count": len(leaves),
            "fallback_used": used_fallback,
        },
    )


def select_leaf_then_parent_mix(
    ranked_reports: list[CommunityReport],
    community_by_id: dict[str, Community],
    tokenizer: Tokenizer,
    token_budget: int,
) -> SelectionResult:
    warnings: list[str] = []
    by_id = {report.community_id: report for report in ranked_reports}
    leaf_ranked = [
        report
        for report in ranked_reports
        if _is_leaf_id(community_by_id, report.community_id)
    ]

    parent_candidates: list[CommunityReport] = []
    for report in leaf_ranked:
        for parent in get_parent_chain(report.community_id, community_by_id)[:1]:
            parent_report = by_id.get(parent.id)
            if parent_report and parent_report not in parent_candidates:
                parent_candidates.append(parent_report)

    phase1 = []
    for report in leaf_ranked:
        phase1.append(report)
        leaf_parent_id = (
            community_by_id[report.community_id].parent
            if report.community_id in community_by_id
            else ""
        )
        for parent in parent_candidates:
            if parent.community_id == leaf_parent_id:
                phase1.append(parent)
                break

    selected = _collect_fit(phase1, tokenizer, token_budget)
    selected_ids = {report.community_id for report in selected}

    if selected and len(selected) == len(leaf_ranked) and len(parent_candidates) > 0:
        replacement_parent = next(
            (report for report in parent_candidates if report.community_id not in selected_ids),
            None,
        )
        if replacement_parent and len(selected) > 1:
            selected.pop()
            selected.append(replacement_parent)
            selected_ids = {report.community_id for report in selected}

    used_fallback = _fill_with_fallback(
        selected_ids, selected, ranked_reports, tokenizer, token_budget
    )

    if len(selected) == 1:
        warnings.append("Only one community selected for leaf_then_parent_mix.")

    return SelectionResult(
        selected_reports=selected,
        warnings=warnings,
        debug={
            "policy": "leaf_then_parent_mix",
            "candidate_count": len(ranked_reports),
            "leaf_candidate_count": len(leaf_ranked),
            "parent_candidate_count": len(parent_candidates),
            "fallback_used": used_fallback,
        },
    )


def select_pyramid(
    ranked_reports: list[CommunityReport],
    community_by_id: dict[str, Community],
    tokenizer: Tokenizer,
    token_budget: int,
) -> SelectionResult:
    by_id = {report.community_id: report for report in ranked_reports}
    leaf_ranked = [
        report
        for report in ranked_reports
        if _is_leaf_id(community_by_id, report.community_id)
    ]

    ordered: list[CommunityReport] = []
    if leaf_ranked:
        ordered.append(leaf_ranked[0])

    for leaf in leaf_ranked:
        chain = get_parent_chain(leaf.community_id, community_by_id)
        parent = chain[0] if len(chain) > 0 else None
        grandparent = chain[1] if len(chain) > 1 else None

        if parent and parent.id in by_id and by_id[parent.id] not in ordered:
            ordered.append(by_id[parent.id])
        if grandparent and grandparent.id in by_id and by_id[grandparent.id] not in ordered:
            if parent and by_id[parent.id] in ordered:
                ordered.append(by_id[grandparent.id])
        if leaf not in ordered:
            ordered.append(leaf)

    selected = _collect_fit(ordered, tokenizer, token_budget)
    selected_ids = {report.community_id for report in selected}
    used_fallback = _fill_with_fallback(
        selected_ids, selected, ranked_reports, tokenizer, token_budget
    )

    return SelectionResult(
        selected_reports=selected,
        warnings=[],
        debug={
            "policy": "pyramid",
            "candidate_count": len(ranked_reports),
            "leaf_candidate_count": len(leaf_ranked),
            "fallback_used": used_fallback,
        },
    )


def select_flat_ranked(
    ranked_reports: list[CommunityReport],
    tokenizer: Tokenizer,
    token_budget: int,
) -> SelectionResult:
    selected = _collect_fit(ranked_reports, tokenizer, token_budget)
    return SelectionResult(
        selected_reports=selected,
        warnings=[],
        debug={
            "policy": "flat_ranked",
            "candidate_count": len(ranked_reports),
            "fallback_used": False,
        },
    )
