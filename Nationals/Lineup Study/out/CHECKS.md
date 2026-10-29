# Second way checks

Each headline number recomputed by an independent route.

| Number | First way | Second way | Difference | Agrees | How |
|---|---|---|---|---|---|
| 2026 shape A slope (runs per game per slot) | -0.0815586 | -0.0815586 | 8.3e-17 | yes | 512 shape aggregate formula vs statsmodels OLS on lineups |
| 2026 shape A SE | 0.0351968 | 0.0351968 | 1.1e-16 | yes | aggregate sandwich vs statsmodels cluster SE |
| 1926 to 2025 shape A slope | 0.000158036 | 0.000158036 | 3.5e-17 | yes | statsmodels vs numpy covariance over variance |
| 2026 exact shape A games | 14 | 14 | 0 | yes | exact shape table vs tags rebuilt from player seasons |
| 2026 exact shape A wins | 11 | 11 | 0 | yes | exact shape table vs scores in lineups |
| Permutation p value for the best of 512 | 0.117 | 0.117 | 0 | yes | json vs recount of the null file |
| 2026 Markov per slot toward A (uncalibrated) | -0.00182077 | -0.00166 | 0.00016 | yes | ratio of sums vs regression through the origin (close, not identical by design) |
| 2026 Markov best minus actual per 162 | 4.58168 | 4.58168 | 0 | yes | summary table vs markov file |
| 2026 runs per win | 9.97869 | 9.97894 | 0.00024 | yes | lineups table vs games table |
| 2026 within team season slope | -0.0924218 | -0.0924218 | 1.4e-17 | yes | statsmodels demeaned vs numpy within |
