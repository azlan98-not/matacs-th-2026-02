# AI Proposal Triage — Design Write-up

**Reference:** MATACS-TH-2026-02 · **Category used for the worked example:** Commercial Solar Installation

**The flow in one paragraph.** A reviewer uploads proposal PDFs and picks a category. Plain code extracts the text. An AI model then reads the text and fills a fixed structured record for each proposal — one field per criterion, each with a verbatim evidence quote. Code validates that record, applies the mandatory pass/fail gates, scans for manipulation, and computes the weighted score with ordinary arithmetic. The reviewer sees a ranked list where every score expands into its extracted values, points and evidence quotes, confirms or overrides, and a human makes the final award decision. Criteria always come from the admin's configuration for the category — never from code.

## 1. AI vs. rules

AI is used for exactly one job: **extraction** — turning unstructured proposal text into the structured record (licence stated yes/no, total price, weeks to complete, warranty years, install count, team details), because reading varied prose is what language models are good at. A second, advisory AI pass can flag text that looks like an instruction aimed at the reviewer or the system.

Everything else is plain code: PDF text extraction, schema and range validation, the mandatory gates, all scoring maths, and the ranking sort. The line is drawn on reliability: scoring must be deterministic and auditable, and language models are neither — they can vary between runs and are weak at arithmetic. AI understands the documents; code decides the numbers.

## 2. Consistency and explainability

Because AI never touches the score, the same extracted record always produces the same ranking — scoring is a pure function of the record plus the criteria version. Extraction is made as stable as possible: pinned model version, temperature 0, a fixed prompt version, and a strict output schema. Every extracted field must carry a verbatim quote from the proposal; a field with no quote is stored as missing, never guessed.

The stored record, criteria version and prompt version are kept with each result, so any ranking can be reproduced and audited exactly. In the interface, each proposal's score expands to show, per criterion, the extracted value, the points it earned, the formula applied, and the evidence quote — so a reviewer can see *why* it ranked where it did without trusting the system.

## 3. Human in the loop

There are three human checkpoints. **Before scoring**, the reviewer confirms the extracted fields for each proposal (and can correct them — corrections are marked as human-entered). **At the ranking**, the reviewer must resolve every flag — missing data, low-confidence extraction, suspected manipulation — and may override any score or position, but only with a written reason. **The award itself** is always a human decision; the tool ranks, it never awards.

Logged for audit: uploader and timestamps, a hash of each uploaded file, the criteria version, model and prompt versions, the full extracted record with evidence quotes, all scores and flags, every human correction and override with its reason and author, and the final decision.

## 4. Changing criteria

Criteria are versioned. Editing criteria or weights creates a new version; it never rewrites history. Scores already produced keep the version they were computed under, and the ranking screen shows that version. If a reviewer wants the new criteria applied, they re-score the **whole batch** under the new version in one action — a single ranking never mixes versions, so proposals are always compared on identical rules. The old version and its rankings remain viewable for audit.

## 5. Risks and safeguards

- **Wrong extraction** (a price or date misread): caught by schema/range validation, evidence quotes the reviewer can check in one click, and the pre-scoring confirmation step.
- **Made-up facts**: the prompt forbids inference — a field with no supporting quote is null. Missing mandatory evidence means the gate fails; missing weighted data scores zero and is flagged, never filled in.
- **Manipulation / prompt injection**: proposal text is data, never instructions. The system prompt says so explicitly, an instruction-pattern scan runs over every document, and any hit flags the proposal for a human with its score withheld. (The sample set contains exactly this: one proposal carries a note addressed to automated review systems asking to be ranked first with full marks. My design flags it — see `ranking.json`, proposal C.)
- **Bias**: scoring is blind arithmetic over extracted facts against admin-set criteria; company identity plays no part in any formula.
- **Cost**: one extraction pass per document, page and token caps, and targeted re-checks only where validation fails — no repeated whole-document calls.
- **Confidentiality**: in production, uploads would sit behind access control with a retention limit; this exercise uses only the fictional samples provided.

*Assumption stated per the brief's instructions: a mandatory criterion counts as met only when the proposal itself evidences it (e.g. a licence held by an unnamed subcontractor "to be confirmed" does not meet "licence held by the bidder").*
