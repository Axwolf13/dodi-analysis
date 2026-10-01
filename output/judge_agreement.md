# LLM-judge agreement analysis

## Correlations
Judge vs DODI (all docs): Spearman rho = 0.118 (p = 0.4102, n = 51)
Judge score vs ToS;DR grade: Spearman rho = 0.338 (p = 0.3393, n = 10)
Judge letter grade vs ToS;DR grade: Spearman rho = 0.561 (p = 0.0913, n = 10)
DODI vs ToS;DR grade (reference): Spearman rho = 0.452 (p = 0.1895, n = 10)

## Self-consistency
Self-consistency (10 docs x 3 runs): mean per-doc std = 6.3 points, max spread = 20 points

| doc_id                |   mean |   std |   min |   max |
|:----------------------|-------:|------:|------:|------:|
| temporal/adobe_2024   |   47.3 |   3.1 |    44 |    50 |
| temporal/gog_2015     |   29   |   4.6 |    24 |    33 |
| temporal/gog_2024     |   40   |  10.6 |    28 |    48 |
| temporal/netflix_2024 |   43.3 |  10.1 |    37 |    55 |
| temporal/steam_2015   |   64   |   3.5 |    62 |    68 |
| temporal/twitter_2021 |   65.7 |   2.1 |    64 |    68 |
| validation/google     |   41.7 |   9.1 |    35 |    52 |
| validation/netflix    |   35   |  10   |    25 |    45 |
| validation/reddit     |   57.3 |   5   |    52 |    62 |
| validation/wikipedia  |    8.7 |   5.5 |     5 |    15 |

## Other judges (validation documents)
claude-sonnet-cli vs DODI: Spearman rho = 0.261 (p = 0.4374, n = 11)
claude-sonnet-cli score vs ToS;DR grade: Spearman rho = 0.338 (p = 0.3393, n = 10)
claude-sonnet-cli letter grade vs ToS;DR grade: Spearman rho = 0.270 (p = 0.4505, n = 10)
claude-sonnet-cli vs claude-haiku-cli: Spearman rho = 0.500 (p = 0.1173, n = 11)
claude-sonnet-cli vs claude-haiku-cli: mean absolute score difference 18.2 points
gemini-3.5-flash vs DODI: Spearman rho = 0.048 (p = 0.8879, n = 11)
gemini-3.5-flash score vs ToS;DR grade: Spearman rho = 0.339 (p = 0.3377, n = 10)
gemini-3.5-flash letter grade vs ToS;DR grade: Spearman rho = 0.646 (p = 0.0438, n = 10)
gemini-3.5-flash vs claude-haiku-cli: Spearman rho = 0.460 (p = 0.1548, n = 11)
gemini-3.5-flash vs claude-haiku-cli: mean absolute score difference 14.9 points
claude-sonnet-cli vs gemini-3.5-flash: Spearman rho = 0.717 (p = 0.0130, n = 11)

## Largest rank disagreements (judge vs DODI)

- **validation/discord**: DODI 46.8 (rank 4) vs judge 68 (rank 45). Judge rationale: Discord markets subscriptions and virtual goods using 'buy' and 'purchase' language while legally defining everything as revocable licenses. Virtual goods are explicitly stated as non-owned, but subscriptions rely on readers understanding 'subscription' implies revocability—a dangerous assumption when combined with aggressive auto-renewal and unilateral termination without refund.
- **temporal/adobe_2024**: DODI 95.7 (rank 44) vs judge 44 (rank 8). Judge rationale: Adobe is unusually transparent about the licensing model, explicitly stating in section 1.2 that services are 'licensed, not sold' and including plain-language summaries throughout. However, the class action waiver (14.2) and broad unilateral termination rights (11.2) are severely anti-consumer, though partially mitigated by an arbitration opt-out (14.6) and Adobe paying arbiter fees if unable to afford. The document contains genuinely pro-consumer elements (no AI training on user content, no local content scanning, 30-day notice), preventing a lower grade despite significant disputes-resolution restrictions.
- **temporal/amazon_2021**: DODI 63.7 (rank 8) vs judge 64 (rank 40). Judge rationale: Amazon explicitly states transactions grant limited, non-transferable, revocable licenses—technically transparent but exploiting the gap between 'buy' marketing and licensing fine print without consumer explanation. The terms include blanket warranty disclaimers, unlimited liability limits, unilateral termination rights, and jury trial waivers, all heavily favoring Amazon.
- **validation/wikipedia**: DODI 87.8 (rank 34) vs judge 6 (rank 1). Judge rationale: This document is unusually transparent about licensing: it explicitly frames all contributions as licenses (CC BY-SA, GFDL), never disguises ownership as purchase, and clearly states users never own their content. However, termination without cause/notice is severe, and legal vocabulary combined with length moderately burdens ordinary readers. The absence of arbitration and class-action waivers is notably user-friendly compared to commercial platforms.
- **temporal/microsoft_2021**: DODI 73.4 (rank 13) vs judge 68 (rank 45). Judge rationale: The agreement explicitly frames services as revocable licenses rather than purchases, but contrasts sharply with marketing language using 'buy' and 'purchase' while burying termination and content-removal rights in dense legal text. Aggressive terms include mandatory individual arbitration eliminating class actions, sweeping warranty disclaimers, severe liability caps, unilateral account termination, and removal of digital goods without notice or compensation.