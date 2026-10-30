#!/usr/bin/env python3
"""
Deterministic scoring prototype for the AI Proposal Triage design
(MATACS-TH-2026-02). Extra credit only — the assessment is a design exercise.

This script is the "plain code" half of the design. It consumes the structured
record that the extraction prompt (see ../PROMPTS.md) would produce and then,
in a fixed order:

  1. validates the input records,
  2. applies the mandatory pass/fail eligibility gates (before any scoring),
  3. flags proposals containing an embedded instruction (score withheld),
  4. scores the rest with fixed weighted formulas and ranks them,

and writes the result to ../ranking.json in exactly the required format.
No AI is called, so running it twice always gives the same result — that is
the point of the design.

Documented policies (see ../WRITEUP.md):
  * Missing or invalid weighted-criterion data scores zero for that
    criterion and adds a reviewer warning to the proposal's reason.
    Unknown information is never invented or treated as confirmed.
  * A price above the budget ceiling scores zero price points and adds a
    warning. The ceiling is a weighted-criterion rule, NOT one of the two
    mandatory eligibility criteria, so the proposal stays ranked.
  * Each criterion's points are rounded to a whole number; the total is
    their sum (maximum 100).

Criteria below stand in for the admin-configured criteria for the category;
in the real system they come from the admin's configuration.
"""

import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUTPUT_PATH = os.path.join(HERE, "..", "ranking.json")

CRITERIA = {
    "budget_ceiling_cad": 260000,   # project budget ceiling from the brief
    "timeline_ceiling_weeks": 16,   # hard completion limit from the brief
    "weights": {"experience": 30, "price": 25, "timeline": 15,
                "warranty": 15, "team": 15},
}

BOOL_FIELDS = (
    "bidder_licence_held", "wsib_and_insurance_confirmed",
    "embedded_instruction_detected", "named_project_lead",
    "crew_described", "safety_plan", "monitoring_plan",
)
NUMERIC_FIELDS = (
    "qualifying_installs", "total_price_cad", "completion_weeks",
    "panel_warranty_years", "workmanship_warranty_years",
)


def validate_structure(proposals):
    """Hard input errors: wrong shapes/types cannot be scored at all."""
    problems = []
    if not isinstance(proposals, dict) or not proposals:
        return ["input must be a non-empty object of proposal records"]
    for letter, rec in proposals.items():
        if not isinstance(rec, dict):
            problems.append(f"{letter}: record is not an object")
            continue
        for field in BOOL_FIELDS:
            if not isinstance(rec.get(field), bool):
                problems.append(f"{letter}: {field} must be true or false")
        for field in NUMERIC_FIELDS:
            value = rec.get(field)
            if value is not None and not isinstance(value, (int, float)):
                problems.append(f"{letter}: {field} must be a number or null")
    return problems


def clean_number(rec, field, warnings):
    """A stated value that cannot be real (zero/negative) is treated as
    missing — never as confirmed data — and earns a reviewer warning."""
    value = rec.get(field)
    if value is not None and value <= 0:
        warnings.append(f"{field} was not a usable value and was treated as not stated")
        return None
    return value


def round_half_up(x):
    return int(math.floor(x + 0.5))


def score_proposal(rec, pool, warnings):
    """Weighted points per criterion for one eligible, unflagged proposal."""
    w = CRITERIA["weights"]
    ceiling_weeks = CRITERIA["timeline_ceiling_weeks"]
    ceiling_price = CRITERIA["budget_ceiling_cad"]
    points = {}

    installs = clean_number(rec, "qualifying_installs", warnings)
    if installs is None:
        points["experience"] = 0
        warnings.append("no qualifying install count is stated, so experience scores 0")
    elif pool["max_installs"]:
        points["experience"] = round_half_up(w["experience"] * installs / pool["max_installs"])
    else:
        points["experience"] = 0

    price = clean_number(rec, "total_price_cad", warnings)
    if price is None:
        points["price"] = 0
        warnings.append("no total price is stated, so price scores 0")
    elif price > ceiling_price:
        points["price"] = 0
        warnings.append("the stated price exceeds the $260,000 budget ceiling, so price scores 0")
    else:
        points["price"] = round_half_up(w["price"] * pool["min_price"] / price)

    weeks = clean_number(rec, "completion_weeks", warnings)
    if weeks is None:
        points["timeline"] = 0
        warnings.append(
            "no confirmed completion timeline is stated, so timeline scores 0 "
            "and compliance with the 16-week limit is unverified — "
            "clarification is required before any award")
    elif weeks > ceiling_weeks:
        points["timeline"] = 0
        warnings.append("the stated timeline exceeds the 16-week limit, so timeline scores 0")
    else:
        span = ceiling_weeks - pool["min_weeks"]
        points["timeline"] = (
            round_half_up(w["timeline"] * (ceiling_weeks - weeks) / span)
            if span else w["timeline"]
        )

    panel = clean_number(rec, "panel_warranty_years", warnings)
    workmanship = clean_number(rec, "workmanship_warranty_years", warnings)
    if panel is None or workmanship is None:
        warnings.append("warranty information is incomplete, so the missing part scores 0")
    panel_part = 0.5 * panel / pool["max_panel"] if panel and pool["max_panel"] else 0.0
    work_part = 0.5 * workmanship / pool["max_workmanship"] if workmanship and pool["max_workmanship"] else 0.0
    points["warranty"] = round_half_up(w["warranty"] * (panel_part + work_part))

    points["team"] = (
        (5 if rec["named_project_lead"] else 0)
        + (4 if rec["crew_described"] else 0)
        + (3 if rec["safety_plan"] else 0)
        + (3 if rec["monitoring_plan"] else 0)
    )
    return points


def main():
    with open(os.path.join(HERE, "sample_extraction.json")) as f:
        proposals = json.load(f)

    problems = validate_structure(proposals)
    if problems:
        for problem in problems:
            print(f"input error: {problem}", file=sys.stderr)
        return 1

    outcomes = {}  # letter -> ranking.json row

    # Step 1: mandatory gates — always before any weighted scoring.
    eligible = {}
    for letter in sorted(proposals):
        rec = proposals[letter]
        if not rec["bidder_licence_held"]:
            outcomes[letter] = {
                "proposal": letter, "rank": None, "status": "ineligible",
                "score": None,
                "reason": "Ineligible: the mandatory licence criterion is not "
                          "met — the Ontario electrical contractor licence is "
                          "not held by the bidder, so the proposal is excluded "
                          "before weighted scoring.",
            }
        elif not rec["wsib_and_insurance_confirmed"]:
            outcomes[letter] = {
                "proposal": letter, "rank": None, "status": "ineligible",
                "score": None,
                "reason": "Ineligible: the mandatory criterion is not met — "
                          "WSIB clearance and $5M liability insurance are not "
                          "both confirmed in the proposal.",
            }
        else:
            eligible[letter] = rec

    # Step 2: manipulation flag — score withheld, routed to a human.
    scorable = {}
    for letter, rec in eligible.items():
        if rec["embedded_instruction_detected"]:
            outcomes[letter] = {
                "proposal": letter, "rank": None, "status": "flagged",
                "score": None,
                "reason": "Flagged for human review: the proposal text contains "
                          "an instruction addressed to automated review "
                          "systems. Proposal content is untrusted data, never "
                          "an instruction, so it is not scored until a human "
                          "reviews it.",
            }
        else:
            scorable[letter] = rec

    # Step 3: anchors from the scored pool, using usable values only.
    if scorable:
        usable = {
            field: [v for v in (clean_number(r, field, []) for r in scorable.values())
                    if v is not None]
            for field in NUMERIC_FIELDS
        }
        pool = {
            "max_installs": max(usable["qualifying_installs"], default=0),
            "min_price": min(usable["total_price_cad"], default=0),
            "min_weeks": min(usable["completion_weeks"], default=0),
            "max_panel": max(usable["panel_warranty_years"], default=0),
            "max_workmanship": max(usable["workmanship_warranty_years"], default=0),
        }

        scored = {}
        for letter, rec in scorable.items():
            warnings = []
            points = score_proposal(rec, pool, warnings)
            scored[letter] = (points, warnings)

        # Step 4: rank by total points (ties broken by letter, so the result
        # is deterministic), then build the final rows.
        totals = {l: sum(p.values()) for l, (p, _) in scored.items()}
        for rank, letter in enumerate(
            sorted(totals, key=lambda l: (-totals[l], l)), start=1
        ):
            points, warnings = scored[letter]
            reason = (
                f"Weighted score {totals[letter]} of 100: experience "
                f"{points['experience']}/30, price {points['price']}/25, "
                f"timeline {points['timeline']}/15, warranty "
                f"{points['warranty']}/15, team and approach {points['team']}/15."
            )
            # The generic "treated as not stated" notes are already implied
            # by the specific warnings; keep reasons to the specific ones.
            specific = [w for w in warnings if "scores 0" in w]
            if specific:
                reason += " Warning: " + "; ".join(specific) + "."
            outcomes[letter] = {
                "proposal": letter, "rank": rank, "status": "ranked",
                "score": totals[letter], "reason": reason,
            }
    else:
        print("note: no proposals could be scored in this run", file=sys.stderr)

    # Final array: ranked by rank, then flagged, then ineligible.
    order = {"ranked": 0, "flagged": 1, "ineligible": 2}
    rows = sorted(
        outcomes.values(),
        key=lambda r: (order[r["status"]], r["rank"] or 0, r["proposal"]),
    )
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(rows, f, indent=2, ensure_ascii=False)
        f.write("\n")

    for row in rows:
        print(row["proposal"], json.dumps(row, ensure_ascii=False))
    print(f"\nwrote {os.path.normpath(OUTPUT_PATH)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
