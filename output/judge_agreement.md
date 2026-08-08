# LLM-judge agreement analysis

## Correlations
Judge vs DODI (all docs): Spearman rho = 0.109 (p = 0.4438, n = 52)
Judge score vs ToS;DR grade: Spearman rho = 0.302 (p = 0.3409, n = 12)
Judge letter grade vs ToS;DR grade: Spearman rho = 0.432 (p = 0.1606, n = 12)
DODI vs ToS;DR grade (reference): Spearman rho = 0.535 (p = 0.0733, n = 12)

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

## Largest rank disagreements (judge vs DODI)

- **validation/discord**: DODI 46.7 (rank 5) vs judge 68 (rank 46). Judge rationale: Discord markets subscriptions and virtual goods using 'buy' and 'purchase' language while legally defining everything as revocable licenses. Virtual goods are explicitly stated as non-owned, but subscriptions rely on readers understanding 'subscription' implies revocability—a dangerous assumption when combined with aggressive auto-renewal and unilateral termination without refund.
- **temporal/facebook_2018**: DODI 55.4 (rank 8) vs judge 68 (rank 46). Judge rationale: Facebook falsely claims users 'own' their content while granting itself an expansive, transferable, sub-licensable right to modify, create derivatives, and persist copies indefinitely—rendering ownership meaningless. Add unilateral account termination, severe liability caps, and mandatory California jurisdiction, and the deception becomes systematic.
- **temporal/adobe_2024**: DODI 95.7 (rank 46) vs judge 44 (rank 8). Judge rationale: Adobe is unusually transparent about the licensing model, explicitly stating in section 1.2 that services are 'licensed, not sold' and including plain-language summaries throughout. However, the class action waiver (14.2) and broad unilateral termination rights (11.2) are severely anti-consumer, though partially mitigated by an arbitration opt-out (14.6) and Adobe paying arbiter fees if unable to afford. The document contains genuinely pro-consumer elements (no AI training on user content, no local content scanning, 30-day notice), preventing a lower grade despite significant disputes-resolution restrictions.
- **temporal/microsoft_2015**: DODI 65.8 (rank 14) vs judge 68 (rank 46). Judge rationale: Document explicitly states software is 'licensed, not sold' but contradicts this with frequent 'purchase' and 'buy' language, creating false impression of ownership. Extensive aggressive clauses—unilateral termination, data deletion, class action waiver, broad content removal rights—combined with dense legal structure that obscures key terms make this significantly problematic for consumers.
- **temporal/microsoft_2021**: DODI 67.1 (rank 16) vs judge 68 (rank 46). Judge rationale: The agreement explicitly frames services as revocable licenses rather than purchases, but contrasts sharply with marketing language using 'buy' and 'purchase' while burying termination and content-removal rights in dense legal text. Aggressive terms include mandatory individual arbitration eliminating class actions, sweeping warranty disclaimers, severe liability caps, unilateral account termination, and removal of digital goods without notice or compensation.