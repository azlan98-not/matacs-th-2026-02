# AI Proposal Triage Design — MATACS-TH-2026-02

**Candidate:** Azlan Asif
**Assessment reference:** MATACS-TH-2026-02
**Role:** Associate Software Developer, Matacs Technologies
**Time actually spent:** Approximately 1 hour (design, write-up, ranking and diagram)

## Contents

- [WRITEUP.md](WRITEUP.md) — answers to the five assessment questions (under 1,000 words): AI vs. rules, consistency and explainability, human in the loop, changing criteria, and risks.
- [diagram/flow.png](diagram/flow.png) — process-flow diagram from upload to ranked output, colour-coded for AI steps, rule-based steps and human checkpoints.
- [PROMPTS.md](PROMPTS.md) — the AI prompts exactly as the system would send them (extraction, plus an advisory manipulation check). The model extracts and flags; it never scores.
- [ranking.json](ranking.json) — the expected ranking of the five sample proposals (A–E) in the required format.
- [prototype/](prototype/) — optional extra credit: `score.py`, a small deterministic script that applies the mandatory gates, the manipulation flag and the weighted-scoring formulas to the structured extraction (`sample_extraction.json`) and reproduces `ranking.json` exactly. No AI is called, so it returns the same result on every run — which is the core of the design.

## The design in brief

AI reads each proposal once and fills a structured record — one field per criterion, every value backed by a verbatim evidence quote. Plain code then validates the record, applies the admin-configured mandatory pass/fail gates, and computes the weighted score with fixed formulas, so rankings are repeatable and every point can be traced to a quoted line in the proposal. Humans confirm the extraction before scoring, resolve every flag, may override only with a written reason, and make the final award decision themselves. Proposal text is always treated as untrusted data: one sample proposal contains an instruction addressed to automated review systems asking to be ranked first, and the design flags it for a human instead of obeying it.

## How AI tools were used

I used an AI assistant (Claude) to analyse the brief, draft the structure of the write-up and prompts, and double-check the scoring arithmetic; every design decision and the final ranking were reviewed by me before committing. One place I disagreed with the AI: its first scoring pass ranked the proposals on weighted points alone, which put the cheapest proposal (B) near the top and scored proposal C normally. I corrected that — mandatory criteria are pass/fail gates that run *before* any weighted scoring (so B is ineligible: its licence is held by a subcontractor, not the bidder), and C's embedded instruction must be flagged for human review, never followed or rewarded.
