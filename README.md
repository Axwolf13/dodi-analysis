# DODI: Digital Ownership Deception Index

**When you click "Buy now" on a digital storefront, you almost never buy anything.** The fine print grants you a revocable licence. DODI measures how hard a platform's Terms of Service work to keep you from noticing. It also tracks how that language has evolved over a decade.

Built solo for the Data and Society seminar at Saarland University, grounded in Perzanowski & Hoofnagle's 2017 finding that 83% of consumers misread "Buy now" as actual ownership.

**Score any ToS yourself at [dodi-web.onrender.com](https://dodi-web.onrender.com/)**, the deployed version of this scorer ([code](https://github.com/Axwolf13/dodi-web)), or call it from an AI agent through the [MCP server](#use-dodi-from-an-ai-agent-mcp-server).

> **This is DODI v1.1 (September 2026).** An audit of the July release found five problems, two of which changed published numbers. Every figure below comes from the corrected version. [Corrections](#corrections-september-2026) lists what was wrong and how to reproduce the old numbers.

## Key findings

<img src="output/temporal_analysis.png" width="100%">

**1. Ownership language got worse, not better.** Across 10 major platforms and four ToS snapshots each (2015, 2018, 2021, 2024, pulled from the Wayback Machine), the mean DODI score rose from 77.5 to 81.7. Seven of ten platforms drifted toward more licence-heavy, less readable, more aggressive terms.

**2. The index passes its face-validity test.** GOG, the DRM-free store whose whole brand is "you actually own your games", scores lowest of all ten platforms in every year (27.4 in 2015). GOG's own terms still drifted upward, to 47.7 in 2024. Twitter scores 95 or more in every year; Spotify hits the 100 ceiling in 2015 and 2018.

**3. Netflix 2024 is the poster child.** Its ToS uses an ownership word once and licence words 98 times, a licence-to-ownership ratio of 98, the highest in the corpus.

**4. Agreement with human experts is weak and not significant.** Against ten reviewed ToS;DR grades, DODI correlates at Spearman ρ = 0.45 (p = 0.19); Pearson r = 0.20. Including Salesforce, whose ToS;DR grade is unreviewed, gives ρ = 0.53 (n = 11). Part of the gap is construct validity: ToS;DR rates general fairness, DODI rates ownership transparency. Wikipedia shows the difference and it also shows DODI's main flaw. It earns a good ToS;DR grade (B) but a high DODI score (87.8), because its copyleft licensing (CC BY-SA) fills the text with licence terms. Honest licensing reads as deception to a word counter.

<img src="validation_analysis.png" width="100%">

## Cross-checking with LLM judges

I built a second, independent grader to check DODI: an LLM reads each document against a rubric and scores it 0-100 for ownership deception (`scripts/llm_judge.py`, `scripts/analyze_judge_agreement.py`). It runs on the local Claude subscription through the CLI with no API billing. Every response is cached, so the analysis reruns without a model.

I expected the judges to agree with DODI. They don't.

| Grader | vs DODI | vs reviewed ToS;DR grades (n = 10) |
|---|---|---|
| DODI v1.1 (counts words) | | ρ = 0.45 |
| Claude Haiku (reads) | ρ = 0.12 (n = 51) | ρ = 0.34 |
| Claude Sonnet (reads) | ρ = 0.26 (n = 11) | ρ = 0.34 |
| Sonnet vs Haiku | ρ = 0.50 (n = 11) | |

What this says, in order of how much I trust it:

1. **The judges barely agree with DODI.** Haiku lands at 0.12 across 51 documents, Sonnet at 0.26 across 11. They agree with each other (0.50) more than either agrees with DODI. The two models even score differently: Haiku high and narrow (lots of 68s), Sonnet lower and wider (most mainstream terms at "moderate"). Neither reads the documents the way DODI counts them.
2. **Nobody wins against the humans.** DODI (0.45) edges both judges' scores (0.34), but Haiku's letter grade reaches 0.56. At n = 10 none of these differences can be told apart and none is significant.
3. **The judges are consistent.** Ten documents judged three times each vary by 6.3 points on average, so the disagreement isn't noise.

The clearest single case is **Adobe 2024**. DODI scores it 95.7, the 7th most deceptive of 40 documents. Haiku scores it 44 and Sonnet 32. Both judges cite the same sentence: Adobe states plainly that its software is "licensed, not sold". It never dangles a "Buy" button. DODI can't tell honest licensing from deceptive licensing, because it counts licence words. That's the same false positive as Wikipedia above. The fix is to measure the gap between what the storefront promises and what the contract grants, which is the natural DODI v2.

The honest read: three reasonable methods for "ownership deception" barely converge. It isn't one well-defined number, which is a caution against trusting any single automated ToS score, including this one.

Model notes: the Haiku judgments (`--model haiku`) and the Sonnet validation judgments (`--model sonnet`) ran in August 2026. The Sonnet judgment of Adobe 2024 ran in September 2026 and resolved to `claude-sonnet-5-5`. Temperature can't be set through the CLI. A cross-vendor judge (Gemini 3.5 Flash, `scripts/llm_judge.py`) has scored 6 of the 11 validation documents so far; the free tier's daily quota ran out. It isn't reported until it's complete.

## Corrections (September 2026)

A September audit found these problems in the July release. I'm keeping them visible because the whole point of this project is honest measurement.

1. **Terms were counted as substrings.** `text.count("own")` also counted "download", "known" and "takedown"; `"rent"` matched "different", "parent" and "current". Across the corpus, 349 of 837 "own" hits and 352 of 374 "rent" hits were other words. The British spelling "licence" was never counted, which understated GOG and Spotify. v1.1 counts whole words and their genuine forms. `scripts/matching_audit.py` compares both versions on every result: GOG stays lowest in every year and the upward trend holds (details in [`output/matching_audit.md`](output/matching_audit.md)).
2. **The validation used different weights from the index.** The published ρ = 0.54 came from a run with 10/50/40 weights left over from a tuning experiment. Every other result, the website and the MCP server use the documented 25/50/25.
3. **The validation set had mislabeled and duplicated documents.** The ToS;DR record numbers in `tosdr_working_api.py` were wrong for six services. Each text was fetched by record number, so texts matched their grades, but the names didn't. "WhatsApp" was Wikipedia (fixed in August), "Apple" was Salesforce with an unreviewed grade, "Amazon" was a byte-identical second copy of Reddit. The corrected set has ten reviewed services, plus Salesforce as a sensitivity check.
4. **Two claims about Adobe were wrong.** The August write-up called Adobe 2024 DODI's most deceptive document. It ranked 6th under v1.0 and ranks 7th under v1.1. It also reported a Sonnet score of 20 for Adobe, but Sonnet had never judged Adobe: 20 was its score for the Salesforce document. Sonnet has now judged Adobe 2024 and gives it 32.
5. **"DODI tracks human experts best" no longer holds.** With the corrected set and scorer, DODI, Haiku and Sonnet are indistinguishable against the human grades.

The July v1.0 numbers remain reproducible: `DODIAnalyzer(matching="substring")` scores the old way. `data/validation_2026-07/` keeps the original grade files, the published validation results and the duplicate Amazon file.

## How the score works

```
DODI = 0.25 × readability penalty + 0.50 × licence ratio score + 0.25 × red-flag score
```

- **Licence ratio (50%):** count of licence terms ("license", "subscription", "access", "grant"...) over ownership terms ("buy", "own", "purchase"...). The core deception mechanism per Perzanowski & Hoofnagle, hence the dominant weight. A ratio of 10 or more scores the maximum.
- **Readability (25%):** Flesch-Kincaid grade level via `textstat`. Grade 8 or below scores 0, grade 16+ scores 100. Complexity enables deception but isn't deception itself.
- **Red flags (25%):** counts of aggressive clauses across three families: unilateral termination ("sole discretion", "without notice"), rights waivers ("class action", "arbitration", "indemnify") and data exploitation ("third parties", "sell your", "track"). Fifty or more hits score the maximum.

Terms are counted as whole words, including their genuine forms ("purchased", "licences", "terminated"). Scores run 0-100; higher means more deceptive about ownership. The scorer is fully deterministic: same document in, same score out, no API calls, no models. That's what makes the 2015-2024 comparison clean.

## Repository structure

```
scripts/
  dodi_analyzer_clean.py        the scorer (the core of the project)
  analyze_temporal_data.py      scores data/temporal, writes output/temporal_results.csv
  visualize_temporal_trends.py  builds the 4-panel figure above
  run_validation_analysis.py    DODI vs ToS;DR grades, writes validation_results.csv + plot
  matching_audit.py             v1.0 substring vs v1.1 word counting, on every result
  llm_judge.py                  LLM-as-judge runs (Claude CLI, Gemini), cached
  analyze_judge_agreement.py    judge vs DODI vs ToS;DR, writes output/judge_agreement.md
  judge_sonnet_validation.py    resumable Sonnet robustness run on the validation set
  batch_analyzer_clean.py       score any folder of .txt ToS documents
  test_weights_face_validity.py compares the candidate weightings
  tosdr_working_api.py          July 2026 grade collection (record numbers were wrong)
  download_tos_documents.py     July 2026 text collection (the API route no longer exists)
mcp_server.py                   DODI as an MCP server (stdio or Streamable HTTP)
tests/test_mcp_server.py        end-to-end protocol test over both transports
data/
  temporal/                     40 ToS snapshots: 10 platforms × {2015, 2018, 2021, 2024}
  validation/                   11 ToS texts matched to ToS;DR grades (tosdr_grades.csv)
  validation_2026-07/           the original July validation files, kept for reproducibility
output/                         results, figures, judge cache and audit reports
```

## Run it

```sh
pip install -r requirements.txt

# rescore the temporal corpus and redraw the figure
python scripts/analyze_temporal_data.py
python scripts/visualize_temporal_trends.py

# reproduce the validation study against ToS;DR
python scripts/run_validation_analysis.py

# compare v1.0 and v1.1 counting on every result
python scripts/matching_audit.py

# judge agreement, from the cached judge responses (no model needed)
python scripts/analyze_judge_agreement.py

# score your own documents: drop .txt files in a folder and point the batch analyzer at it
python scripts/batch_analyzer_clean.py
```

Run everything from the repo root; scripts resolve `data/` and `output/` relative to it.

## Use DODI from an AI agent (MCP server)

DODI is also an [MCP](https://modelcontextprotocol.io/) server, so an AI agent can score documents mid-conversation. Paste a ToS, ask "how deceptive is this?" and the agent calls the same deterministic scorer this repo ships.

Three tools: `score_tos` (the 0-100 index), `explain_score` (the evidence behind the number: which terms and red-flag clauses matched, how often) and `get_platform_rankings` (the 2015-2024 study results).

**Locally** with Claude Code, over stdio:

```sh
claude mcp add dodi -- python mcp_server.py
```

**Remotely**, over Streamable HTTP. A public instance runs on Render at `https://dodi-mcp.onrender.com/mcp`. I've tested it as a tool inside a Microsoft Copilot Studio agent. To run your own:

```sh
python mcp_server.py --http          # serves http://0.0.0.0:8000/mcp, plus /health
```

HTTP mode also switches on when a `PORT` variable is set, which is how Render passes its port, so the deploy needs no extra flag (build with `requirements-mcp.txt`). `tests/test_mcp_server.py` runs the same checks over both transports and confirms that `explain_score`'s evidence adds up to `score_tos`'s counts.

## Honest limitations

- **n = 10 for validation** is far too small for significance. ρ = 0.45 at p = 0.19 is a weak signal, not evidence.
- **"Service" dominates the licence count.** It accounts for about two thirds of all licence-term hits, because every Terms of Service says "Services" constantly. The ratio partly measures how often a document names its own services.
- **Both capped components saturate.** 24 of 51 documents hit the licence-ratio ceiling and 23 of 51 the red-flag ceiling, so the index can't separate documents at the deceptive end.
- **ToS;DR grades drift.** Between the July collection and September 2026, Reddit moved from E to D and Discord from D to E. The validation pairs each text with the grade fetched alongside it.
- **Keyword counting has no sense of negation.** "You do not own this content" counts an ownership word.
- **Wayback snapshots have coarse timing**, so a "2015" document is the nearest capture to that year, not January 1st.
- **The score is gameable.** A platform could pad its ToS with ownership words without changing its terms. DODI measures language, not legal substance.

## Future work

The marketing-vs-contract gap (deception is largest where the storefront says "buy" and the contract says "licence"), which would fix the Adobe and Wikipedia false positives. A revised term list that doesn't count "service" as licence language, with continuous scaling instead of hard caps. A larger validation set: ToS;DR has reviewed grades for Amazon (D), Apple Services (C), Steam (D), TikTok (E) and WhatsApp (E), but it no longer serves document text, so this needs a new text source. Negation-aware clause parsing with spaCy dependency trees.

## References

- Perzanowski, A. & Hoofnagle, C. J. (2017). *What We Buy When We Buy Now*. University of Pennsylvania Law Review.
- [ToS;DR](https://tosdr.org/), Terms of Service; Didn't Read, the human-curated grades used for validation.

---

Akshay Ashok · [axwolf13.github.io](https://axwolf13.github.io/) · akshay57ax@gmail.com
