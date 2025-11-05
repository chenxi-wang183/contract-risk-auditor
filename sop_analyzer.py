# sop_analyzer.py
# ------------------------------
# Executable SOP (V7) for NDA review.
# No AI "creativity". Pure rule-engine, deterministic.
# ------------------------------

from typing import List, Dict, Tuple
import re

# ---------- Utilities ----------

SUBJECTIVE_TERMS = [
    "reasonable", "reasonably", "promptly", "best efforts", "commercially reasonable",
    "material", "materially", "substantially", "as soon as practicable"
]

EXCLUSION_MARKERS = [
    "public domain", "publicly available", "already in the public domain",
    "independently developed", "independently obtained", "independent development",
    "lawfully obtained", "rightfully obtained", "third party", "prior knowledge",
    "already known", "known by the receiving party", "known to the receiving party"
]

TERM_MARKERS = [
    "term", "duration", "survive", "survival", "period", "years", "year", "expire", "expiration"
]

TRADE_SECRET_MARKERS = ["trade secret", "trade secrets"]

DEFINITION_MARKERS = [
    "confidential information means", "definition of confidential information",
    "for purposes of this agreement, “confidential information”", "as used in this agreement, confidential information"
]

OBLIGATION_MARKERS = [
    "use", "protect", "maintain", "keep confidential", "not disclose", "disclose only", "restrict"
]

RECITAL_MARKERS = ["whereas", "recital", "鉴于"]


def _lower(s: str) -> str:
    return (s or "").lower()


def _has_any(s: str, needles: List[str]) -> bool:
    text = _lower(s)
    return any(n in text for n in needles)


def _extract_year_like_numbers(text: str) -> List[int]:
    # Find small integers likely used as durations (1..20)
    nums = [int(x) for x in re.findall(r"\b([1-9]|1[0-9]|20)\b", text)]
    return nums


def _looks_like_definition(title: str, body: str) -> bool:
    t = _lower(title + " " + body)
    return ("confidential information" in t and ("means" in t or "shall mean" in t)) or _has_any(t, DEFINITION_MARKERS)


def _looks_like_term(title: str, body: str) -> bool:
    t = _lower(title + " " + body)
    return _has_any(t, TERM_MARKERS)


def _looks_like_obligation(title: str, body: str) -> bool:
    t = _lower(title + " " + body)
    # Must mention protecting/using/keeping and CI
    return ("confidential information" in t) and _has_any(t, OBLIGATION_MARKERS)


def _looks_like_recital(title: str, body: str) -> bool:
    t = _lower(title + " " + body)
    return _has_any(t, RECITAL_MARKERS) or title.strip().lower().startswith("preamble") or title.strip().lower().startswith("recital")


def _requires_marking_only(body: str) -> bool:
    b = _lower(body)
    # If it insists on "must be marked as confidential" and does not allow unmarked/oral with later confirmation.
    needs_mark = ("marked as confidential" in b or "must be marked" in b)
    allows_oral_flow = ("oral" in b and ("confirm" in b or "confirmation" in b or "written within" in b))
    return needs_mark and not allows_oral_flow


def _oral_without_timing(body: str) -> bool:
    b = _lower(body)
    if "oral" in b:
        # if mentions oral but does not include a timing word like "days" / "business days" / "within X days"
        has_timing = bool(re.search(r"(within\s+\d+\s+(business\s+)?days?|no\s+later\s+than\s+\d+)", b))
        return not has_timing
    return False


def _has_exclusions(body: str) -> bool:
    return _has_any(body, EXCLUSION_MARKERS)


def _mentions_all_information(body: str) -> bool:
    return "all information" in _lower(body)


def _contains_subjective_terms(body: str) -> List[str]:
    b = _lower(body)
    hits = [t for t in SUBJECTIVE_TERMS if t in b]
    return hits


def _mentions_trade_secret(body: str) -> bool:
    return _has_any(body, TRADE_SECRET_MARKERS)


def _mentions_fixed_years(body: str) -> Tuple[bool, List[int]]:
    nums = _extract_year_like_numbers(body)
    if not nums:
        return False, []
    # We treat as "fixed years present" if typical phrasing like "for X years", "X years"
    return True, nums


# ---------- Stage 1 (global structure scan) ----------

def global_structure_scan(clauses: List[Dict[str, str]]) -> Dict[str, List[int]]:
    """
    Return a simple structural map:
      - where we found definition-like
      - where we found term/duration-like
      - where we found obligation-like
    """
    definition_ix = []
    term_ix = []
    obligation_ix = []
    for i, c in enumerate(clauses):
        title = c.get("title", "")
        text = c.get("text", "")
        if _looks_like_definition(title, text):
            definition_ix.append(i)
        if _looks_like_term(title, text):
            term_ix.append(i)
        if _looks_like_obligation(title, text):
            obligation_ix.append(i)
    return {"definition_ix": definition_ix, "term_ix": term_ix, "obligation_ix": obligation_ix}


# ---------- Stage 2 (per-clause SOP rules) ----------

def _structural_conflict_flags(i: int, role_bucket: Dict[str, List[int]], role_name: str, title: str, body: str) -> Tuple[bool, str]:
    """
    If a clause looks like one role but is placed in another role zone, flag conflict.
    For a simple deterministic rule: if multiple indices for the same role exist and this clause body
    contains content from other roles, we encourage consolidation.
    """
    looks_def = _looks_like_definition(title, body)
    looks_term = _looks_like_term(title, body)
    looks_obl = _looks_like_obligation(title, body)

    msg_parts = []
    conflict = False

    # definition mixed with term content
    if looks_def and looks_term:
        conflict = True
        msg_parts.append("Definition and Term/logical content appear in the same clause.")

    # obligation clause containing term wording
    if looks_obl and looks_term:
        conflict = True
        msg_parts.append("Obligations clause also defines duration (Term) — split content.")

    # recital trying to define substance
    if _looks_like_recital(title, body) and (looks_def or looks_term or looks_obl):
        conflict = True
        msg_parts.append("Recital contains substantive definitions/terms — move to operative clauses.")

    return conflict, " ".join(msg_parts)


def analyze_clause(title: str, body: str, global_map: Dict[str, List[int]]) -> Dict[str, str]:
    """
    Returns:
      {
        "level": "RED/YELLOW/GREEN",
        "risk": "...",
        "suggestion": "...",
        "original_excerpt": "..."
      }
    Deterministic, SOP V7 compliant.
    """
    # Trim a short excerpt for readability (avoid wall of text)
    excerpt = body.strip()
    if len(excerpt) > 900:
        excerpt = excerpt[:900].rstrip() + " …"

    # 0) Structural conflicts first (never fabricate; only when real mixed content)
    conflict, conflict_msg = _structural_conflict_flags(
        i=-1, role_bucket=global_map, role_name="", title=title, body=body
    )
    if conflict:
        return {
            "level": "RED",
            "risk": f"Structural conflict: {conflict_msg}",
            "suggestion": "Consolidate by function: keep definitions only in 'Definitions'; keep durations only in 'Term'; move substantive obligations into 'Obligations'.",
            "original_excerpt": excerpt,
        }

    # 1) Definition Clause SOP
    if _looks_like_definition(title, body):
        # (a) “all information” → too broad
        if _mentions_all_information(body):
            return {
                "level": "YELLOW",
                "risk": "Overbroad definition ('all information') risks unenforceability due to lack of objective scope.",
                "suggestion": "Scope the definition and include standard exclusions (public domain, prior knowledge, third-party lawful disclosure, independent development).",
                "original_excerpt": excerpt,
            }

        # (b) requires marking only w/o oral confirmation path
        if _requires_marking_only(body):
            return {
                "level": "YELLOW",
                "risk": "Marking-only definition imposes heavy admin burden and risks unprotected unmarked disclosures.",
                "suggestion": "Allow oral/unmarked disclosures if confirmed in writing within a short window (e.g., 5 business days); retain standard exclusions.",
                "original_excerpt": excerpt,
            }

        # (c) oral mentioned but no timing
        if _oral_without_timing(body):
            return {
                "level": "YELLOW",
                "risk": "Oral disclosures referenced without a written confirmation window, impairing enforceability.",
                "suggestion": "Add a confirmation window (e.g., oral disclosures must be confirmed in writing within 5 business days).",
                "original_excerpt": excerpt,
            }

        # (d) no exclusions at all
        if not _has_exclusions(body):
            return {
                "level": "YELLOW",
                "risk": "Standard exclusions (public domain, prior knowledge, independent development, lawful third-party disclosure) missing.",
                "suggestion": "Add the standard exclusions to avoid overreach and improve enforceability.",
                "original_excerpt": excerpt,
            }

        # otherwise OK
        return {
            "level": "GREEN",
            "risk": "Definition appears industry-standard with adequate scope and exclusions.",
            "suggestion": "No revision required.",
            "original_excerpt": excerpt,
        }

    # 2) Term/Duration Clause SOP (HARD RULE)
    if _looks_like_term(title, body):
        has_trade_secret = _mentions_trade_secret(body)
        has_fixed, nums = _mentions_fixed_years(body)

        if has_trade_secret and has_fixed:
            # Fatal if *Trade Secrets* are placed under a fixed number (any)
            return {
                "level": "RED",
                "risk": "Fatal risk: Trade Secrets appear tied to a fixed duration. Trade Secrets require indefinite protection.",
                "suggestion": "Adopt dual-track: (a) Confidential Information: fixed term (e.g., 3–5 years); (b) Trade Secrets: indefinite ('until no longer a trade secret').",
                "original_excerpt": excerpt,
            }

        if has_trade_secret and not has_fixed:
            # Probably OK if it says indefinite / until no longer a trade secret
            return {
                "level": "GREEN",
                "risk": "Trade Secrets not tied to a fixed duration.",
                "suggestion": "No revision required.",
                "original_excerpt": excerpt,
            }

        if (not has_trade_secret) and has_fixed:
            # Standard NDA: fixed term for general CI only is fine
            return {
                "level": "GREEN",
                "risk": "Fixed duration for general Confidential Information is standard.",
                "suggestion": "No revision required.",
                "original_excerpt": excerpt,
            }

        # If term clause exists but neither fixed nor TS mentioned (rare)
        return {
            "level": "YELLOW",
            "risk": "Term is underspecified (no fixed duration, no trade secret carve-out).",
            "suggestion": "State dual-track model explicitly: CI = fixed term; Trade Secrets = indefinite.",
            "original_excerpt": excerpt,
        }

    # 3) Obligations Clause SOP
    if _looks_like_obligation(title, body):
        subs = _contains_subjective_terms(body)
        if subs:
            return {
                "level": "YELLOW",
                "risk": f"Subjective standard detected ({', '.join(sorted(set(subs)))}), which is harder to enforce.",
                "suggestion": "Replace with an objective baseline: 'at least the degree of care used to protect its own comparable confidential information, and no less than reasonable care.'",
                "original_excerpt": excerpt,
            }
        return {
            "level": "GREEN",
            "risk": "Obligations appear measurable and enforceable.",
            "suggestion": "No revision required.",
            "original_excerpt": excerpt,
        }

    # 4) Standard boilerplate (Severability / Entire Agreement / Notice / Governing Law)
    #    — unless subjective terms or obvious misplacements appear.
    subs = _contains_subjective_terms(body)
    if subs:
        return {
            "level": "YELLOW",
            "risk": f"Subjective phrasing detected in a boilerplate context ({', '.join(sorted(set(subs)))}).",
            "suggestion": "Replace with specific, objective timing (e.g., 'within 10 business days') or measurable criteria.",
            "original_excerpt": excerpt,
        }

    return {
        "level": "GREEN",
        "risk": "Standard boilerplate; no material legal risk detected.",
        "suggestion": "No revision required.",
        "original_excerpt": excerpt,
    }


def analyze_all(clauses: List[Dict[str, str]]) -> Tuple[List[Dict[str, str]], Dict[str, int]]:
    """
    Input: [{title, text}, ...]
    Output:
      results: per-clause dicts with ('title','level','risk','suggestion','original_excerpt')
      counters: {'RED': x, 'YELLOW': y, 'GREEN': z}
    """
    gmap = global_structure_scan(clauses)
    results = []
    counts = {"RED": 0, "YELLOW": 0, "GREEN": 0}
    for c in clauses:
        r = analyze_clause(c.get("title", ""), c.get("text", ""), gmap)
        results.append({
            "title": c.get("title", "Clause"),
            "level": r["level"],
            "risk": r["risk"],
            "suggestion": r["suggestion"],
            "original_excerpt": r["original_excerpt"],
        })
        counts[r["level"]] += 1
    return results, counts