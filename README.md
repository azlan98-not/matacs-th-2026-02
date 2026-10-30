# AI Proposal Triage Design — MATACS-TH-2026-02

**Candidate:** Azlan Asif
**Assessment reference:** MATACS-TH-2026-02
**Role:** Associate Software Developer, Matacs Technologies
**Time actually spent:** Approximately 1 hour

## Contents

- [WRITEUP.md](WRITEUP.md) — answers to the five assessment questions (under 1,000 words): AI vs. rules, consistency and explainability, human in the loop, changing criteria, and risks.
- [diagram/flow.png](diagram/flow.png) — process-flow diagram from upload to ranked output, colour-coded for AI steps, rule-based steps and human checkpoints.
- [PROMPTS.md](PROMPTS.md) — the AI prompts exactly as the system would send them (extraction, plus an advisory manipulation check). The model extracts and flags; it never scores.
- [ranking.json](ranking.json) — the ranking of the five sample proposals (A–E) in the required format: A 1st (98), E 2nd (82), D 3rd (71) with a missing-timeline reviewer warning, C flagged (embedded instruction), B ineligible (mandatory licence not held by the bidder).
- [prototype/](prototype/) — optional extra credit: `score.py`, a small deterministic scorer. Run it with `python3 prototype/score.py`: it validates the structured extraction (`sample_extraction.json`), applies the mandatory gates and the manipulation flag, computes the weighted scores, and writes `ranking.json` at the repository root — the committed `ranking.json` is its exact output. No AI is called, so it returns the same result on every run, which is the core of the design.

## The design in brief

AI reads each proposal once and fills a structured record — one field per criterion, every value backed by a verbatim evidence quote. Plain code then validates the record, applies the admin-configured mandatory pass/fail gates and a manipulation scan, and computes the weighted score with fixed formulas; missing weighted data scores zero and is carried on the ranking as a reviewer warning. Rankings are therefore repeatable, and every point can be traced to a quoted line in the proposal. Humans confirm the extraction before scoring, resolve every flag and warning, may override only with a written reason, and make the final award decision themselves. Proposal text is always treated as untrusted data: one sample proposal contains an instruction addressed to automated review systems asking to be ranked first, and the design flags it for a human instead of obeying it.

## How AI tools were used

I used an AI assistant (Claude) to analyse the brief, draft the structure of the write-up and prompts, and double-check the scoring arithmetic; every design decision and the final ranking were reviewed by me before committing. One place I disagreed with the AI: its first scoring pass ranked the proposals on weighted points alone, which put the cheapest proposal (B) near the top and scored proposal C normally. I corrected that — mandatory criteria are pass/fail gates that run *before* any weighted scoring (so B is ineligible: its licence is held by a subcontractor, not the bidder), and C's embedded instruction must be flagged for human review, never followed or rewarded.
