#!/usr/bin/env python3
"""
Deterministic scoring prototype for the AI Proposal Triage design
(MATACS-TH-2026-02). Extra credit only — the assessment is a design exercise.

This script is the "plain code" half of the design: it consumes the structured
record that the extraction prompt (see ../PROMPTS.md) would produce and applies

  1. mandatory pass/fail gates,
  2. a manipulation flag (an embedded instruction withholds the score),
  3. weighted scoring with fixed formulas,

and prints the same ranking that is committed in ../ranking.json. No AI is
called here, so running it twice always gives the same result — that is the
point of the design.

Criteria below stand in for the admin-configured criteria for the category;
in the real system they are loaded from the admin's configuration, never
hard-coded per category in scoring logic.
"""

import json
import math
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# --- Admin-configured criteria (stand-in for the category configuration) ---
CRITERIA = {
    "budget_ceiling_cad": 260000,
    "timeline_ceiling_weeks": 16,
    "weights": {
        "experience": 30,
        "price": 25,
        "timeline": 15,
        "warranty": 15,
        "team": 15,
    },
}


def round_half_up(x):
    return int(math.floor(x + 0.5))


def score_proposal(rec, pool):
    """Weighted score for one eligible, unflagged proposal.

    pool holds the comparison anchors computed across eligible proposals:
    max installs, lowest price, fastest timeline, longest workmanship
    warranty. Missing weighted data scores zero — it is never invented.
    """
    w = CRITERIA["weights"]

    experience = w["experience"] * rec["qualifying_installs"] / pool["max_installs"]

    price = w["price"] * pool["min_price"] / rec["total_price_cad"]

    if rec["completion_weeks"] is None:
        timeline = 0.0  # no schedule stated -> zero, and flagged in the UI
    else:
        ceiling = CRITERIA["timeline_ceiling_weeks"]
        timeline = (
            w["timeline"]
            * (ceiling - rec["completion_weeks"])
            / (ceiling - pool["min_weeks"])
        )

    # Panel warranty is identical across the sample set, so the workmanship
    # term decides this criterion; in general both terms would be combined.
    warranty = (
        w["warranty"]
        * rec["workmanship_warranty_years"]
        / pool["max_workmanship"]
    )

    team = (
        (5 if rec["named_project_lead"] else 0)
        + (4 if rec["crew_described"] else 0)
        + (3 if rec["safety_plan"] else 0)
        + (3 if rec["monitoring_plan"] else 0)
    )

    return round_half_up(experience + price + timeline + warranty + team)


def main():
    with open(os.path.join(HERE, "sample_extraction.json")) as f:
        proposals = json.load(f)

    results = {}

    # Step 1: mandatory gates (pass/fail, evaluated before any scoring).
    eligible = {}
    for letter, rec in proposals.items():
        if not rec["bidder_licence_held"]:
            results[letter] = {
                "status": "ineligible",
                "reason": "Licence is not held by the bidder.",
            }
        elif not rec["wsib_and_insurance_confirmed"]:
            results[letter] = {
                "status": "ineligible",
                "reason": "WSIB clearance / liability insurance not confirmed.",
            }
        else:
            eligible[letter] = rec

    # Step 2: manipulation flag — score withheld, routed to a human.
    scorable = {}
    for letter, rec in eligible.items():
        if rec["embedded_instruction_detected"]:
            results[letter] = {
                "status": "flagged",
                "reason": "Embedded instruction aimed at the review system "
                "detected in the proposal text; human review required.",
            }
        else:
            scorable[letter] = rec

    # Step 3: comparison anchors across the scorable pool, then scoring.
    pool = {
        "max_installs": max(r["qualifying_installs"] for r in scorable.values()),
        "min_price": min(r["total_price_cad"] for r in scorable.values()),
        "min_weeks": min(
            r["completion_weeks"]
            for r in scorable.values()
            if r["completion_weeks"] is not None
        ),
        "max_workmanship": max(
            r["workmanship_warranty_years"] for r in scorable.values()
        ),
    }
    scored = {
        letter: score_proposal(rec, pool) for letter, rec in scorable.items()
    }

    # Step 4: rank by score, highest first.
    for rank, letter in enumerate(
        sorted(scored, key=lambda l: -scored[l]), start=1
    ):
        results[letter] = {
            "status": "ranked",
            "rank": rank,
            "score": scored[letter],
        }

    for letter in sorted(results):
        print(letter, json.dumps(results[letter], sort_keys=True))


if __name__ == "__main__":
    main()
