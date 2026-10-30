# AI Proposal Triage — Design Write-up

**Reference:** MATACS-TH-2026-02 · **Worked example:** Commercial Solar Installation

**The flow in one paragraph.** An admin defines each category's criteria on admin screens — criteria are configuration, never code. A reviewer uploads proposal PDFs and picks a category. Plain code extracts the text; an AI model reads it and fills a fixed structured record, one field per criterion, each value backed by a verbatim evidence quote. Code validates the record, the reviewer confirms it, then code applies the mandatory pass/fail gates and a manipulation scan. Survivors are scored by fixed formulas (missing weighted data scores zero, with a visible warning) and ranked. A human reviews the ranking, resolves every flag and warning, and makes the final award decision.

## 1. AI vs. rules

AI does exactly one job: **extraction** — turning unstructured proposal text into the structured record (licence held yes/no, total price, weeks to complete, warranty years, install count, team details), because reading varied prose is what language models are good at. A second, advisory AI pass can flag text that looks like an instruction aimed at the reviewer or system; it can only raise a flag, never change a result.

Everything else is plain code: text extraction, validation, mandatory gates, all scoring maths and the sort. The line is drawn on reliability — scoring must be deterministic and auditable, and language models are neither: they vary between runs and are weak at arithmetic. AI understands the documents; code decides the numbers. Mandatory gates run *before* scoring: eligibility is pass/fail, not a preference a low price can offset.

## 2. Consistency, explainability and the scoring method

Because AI never touches the score, the same extracted record always produces the same ranking: scoring is a pure function of the record plus the criteria version. Extraction is kept stable with a pinned model version, temperature 0, a fixed prompt version and a strict output schema. Every field must carry a verbatim quote; a field with no quote is stored as missing, never guessed.

The weights (30/25/15/15/15) come from the brief's category configuration. The formulas are my design assumptions, applied by code: **experience** scales against the highest qualifying install count in the scored pool; **price** scales against the lowest price in the pool, and a price above the $260,000 ceiling scores zero price points with a warning (the ceiling is a scoring rule, not a third mandatory criterion); **timeline** scales between the 16-week limit and the fastest confirmed bid, and a missing or over-limit timeline scores zero with a warning; **warranty** averages the panel and workmanship terms, each scaled to the pool's longest; **team** follows a fixed checklist (named lead 5, crew 4, safety plan 3, monitoring plan 3). Each criterion is rounded to whole points and summed, so totals run to 100. Every score expands to show the extracted value, points, formula and evidence quote per criterion — a reviewer can see *why* each proposal ranked where it did.

## 3. Human in the loop

Three checkpoints. **Before scoring**, the reviewer confirms the extracted fields and can correct them (corrections are marked human-entered). **At the ranking**, the reviewer must resolve every flag (manipulation) and warning (missing data — an unstated schedule must be clarified before any award), and may override any score or position only with a written reason. **The award** is always human; the tool ranks, it never awards.

Logged for audit: uploader and timestamps, a hash of each file, the criteria version, model and prompt versions, the full extracted record with quotes, scores, flags and warnings, every correction and override with reason and author, and the final decision.

## 4. Changing criteria

Criteria are versioned. Editing criteria or weights creates a new version and never rewrites history; existing scores keep the version they were computed under, and the screen shows it. To apply new criteria, the reviewer re-scores the **whole batch** under the new version in one action — a single ranking never mixes versions, so proposals are always compared on identical rules. Old versions stay viewable for audit.

## 5. Risks and safeguards

- **Wrong extraction**: schema/range validation, evidence quotes checkable in one click, and the pre-scoring confirmation step.
- **Made-up facts**: the prompt forbids inference — no quote means null. Missing evidence for a mandatory criterion fails the gate. Missing *weighted* data follows one rule: zero for that criterion, plus a reviewer warning on the ranking — never invented, never silently treated as confirmed. Proposal D is the worked example: it passes both mandatory gates and is ranked, but states no completion schedule, so its timeline scores 0/15 and its entry warns that 16-week compliance is unverified and clarification is required before award. D is *ranked with a warning*, which is deliberately different from *flagged*: flagged is reserved for manipulation, where no score is produced at all.
- **Manipulation / prompt injection**: proposal text is data, never instructions. The system prompt says so, an instruction-pattern scan runs over every document, and any hit flags the proposal with its score withheld. The sample set contains exactly this — one proposal carries a note addressed to automated review systems asking to be ranked first with full marks (proposal C). My design flags it; its legitimate contents stay on file for the human, and it is not declared ineligible, because the brief's mandatory criteria do not cover conduct.
- **Bias**: scoring is blind arithmetic over extracted facts against admin-set criteria; company identity plays no part.
- **Cost**: one extraction pass per document, page and token caps, targeted re-checks only where validation fails.
- **Confidentiality**: production uploads would sit behind access control with a retention limit; this exercise uses only the fictional samples.

*Assumption, stated as the brief allows: a mandatory criterion is met only when the proposal itself evidences it — a licence held by a subcontractor "to be confirmed" does not meet "licence held by the bidder", so proposal B is ineligible and its low price never enters scoring.*
