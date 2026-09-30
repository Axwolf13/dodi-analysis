# Matching audit: substring (v1.0) vs whole-word counting (v1.1)

Both columns use the documented 25/50/25 weights; only the counting differs.

## 1. Term hits across all 51 documents

| Term | v1.0 substring | v1.1 word | Change |
|---|---:|---:|---:|
| buy | 55 | 55 | +0 |
| purchase | 428 | 446 | +18 |
| own | 837 | 488 | -349 |
| acquire | 69 | 82 | +13 |
| possess | 8 | 8 | +0 |
| license | 785 | 976 | +191 |
| subscription | 784 | 784 | +0 |
| access | 1167 | 1158 | -9 |
| service | 5917 | 5904 | -13 |
| grant | 349 | 349 | +0 |
| rent | 374 | 22 | -352 |

Red-flag phrases combined: 3382 substring hits, 3364 whole-word hits.

## 2. Score changes

Mean absolute change: 5.1 points. Largest rises and falls:

| Document | v1.0 | v1.1 | Change |
|---|---:|---:|---:|
| validation/microsoft | 64.5 | 90.0 | +25.5 |
| temporal/facebook_2018 | 55.4 | 77.3 | +21.9 |
| temporal/facebook_2021 | 59.2 | 80.2 | +21.0 |
| temporal/facebook_2015 | 52.1 | 72.1 | +20.0 |
| temporal/ubisoft_2018 | 79.9 | 98.4 | +18.5 |
| temporal/adobe_2021 | 94.5 | 94.5 | +0.0 |
| temporal/adobe_2018 | 90.6 | 90.1 | -0.5 |
| temporal/adobe_2015 | 86.2 | 85.7 | -0.5 |
| validation/reddit | 91.1 | 90.1 | -1.0 |
| validation/discord | 47.9 | 46.8 | -1.1 |

## 3. Face validity: GOG's rank among the 10 platforms (1 = least deceptive)

| Year | v1.0 rank | v1.1 rank | Least deceptive under v1.1 |
|---|---:|---:|---|
| 2015 | 1 | 1 | gog |
| 2018 | 1 | 1 | gog |
| 2021 | 1 | 1 | gog |
| 2024 | 1 | 1 | gog |

## 4. Temporal trend (mean score across the 10 platforms)

| Year | v1.0 | v1.1 |
|---|---:|---:|
| 2015 | 72.5 | 77.5 |
| 2018 | 74.9 | 80.2 |
| 2021 | 75.9 | 80.3 |
| 2024 | 77.3 | 81.7 |

Platforms scoring higher in 2024 than 2015: v1.0 7 of 10, v1.1 7 of 10.

## 5. Agreement with reviewed ToS;DR expert grades

| Scorer | Spearman vs ToS;DR (n = 10) |
|---|---|
| DODI v1.0 substring | +0.472 (p = 0.168) |
| DODI v1.1 word | +0.452 (p = 0.189) |

## 6. Agreement with the LLM judges

| Judge | n | v1.0 | v1.1 |
|---|---:|---|---|
| Haiku | 51 | +0.052 (p = 0.719) | +0.118 (p = 0.410) |
| Sonnet | 11 | +0.064 (p = 0.852) | +0.261 (p = 0.437) |

## 7. Saturated components

| | v1.0 | v1.1 |
|---|---:|---:|
| Ratio component capped (ratio >= 10 or no ownership words) | 18 of 51 | 24 of 51 |
| Red-flag component capped (>= 50 hits) | 23 of 51 | 23 of 51 |
