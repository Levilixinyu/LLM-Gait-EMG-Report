# Supplementary original-rating agreement analysis

This post-hoc sensitivity analysis was authorized after inspection of the existing results. It uses the preserved original independent ratings, not final discussion outcomes. No report, score, category or original exclusion was changed. All 18 original cross-tabulations were reproduced.

Nominal AC1 = (Pa - Pe)/(1 - Pe), where Pa is observed agreement, Pe = sum[p_k(1-p_k)]/(q-1), and p_k is the mean of the two raters' marginal proportions. The fixed rubric has q=3 for coverage (including reference limitations) and q=2 for any-error. Categories are not dropped when absent. Point estimates retain the original item/report weighting.

Exploratory 95% percentile intervals use 20,000 participant-cluster bootstrap samples, seed 20260925. Each draw retains all reports, items and exclusions for the sampled participant; 25 stroke and 10 control participants are sampled within their respective cohorts. These intervals do not address shared-reference dependence or selected sampling. Empty replicates are reported as undefined, never converted to zero.

| Pair | Cohort | Domain | Assessed/planned | Agreement | Kappa | AC1 | Cluster 95% interval |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rater1__rater2 | stroke | case_requirements | 357/357 | 95.5% | 0.550 | 0.953 | 0.930 to 0.972 |
| rater1__rater2 | stroke | G03 | 75/75 | 100.0% | Undefined | 1.000 | 1.000 to 1.000 |
| rater1__rater2 | stroke | any_error | 65/75 | 81.5% | 0.600 | 0.660 | 0.492 to 0.817 |
| rater1__rater2 | control | case_requirements | 90/90 | 86.7% | 0.309 | 0.853 | 0.773 to 0.927 |
| rater1__rater2 | control | G03 | 29/30 | 100.0% | Undefined | 1.000 | 1.000 to 1.000 |
| rater1__rater2 | control | any_error | 29/30 | 62.1% | 0.290 | 0.295 | -0.030 to 0.647 |
| rater1__rater3 | stroke | case_requirements | 357/357 | 94.4% | 0.305 | 0.942 | 0.913 to 0.965 |
| rater1__rater3 | stroke | G03 | 75/75 | 100.0% | Undefined | 1.000 | 1.000 to 1.000 |
| rater1__rater3 | stroke | any_error | 54/75 | 68.5% | 0.132 | 0.542 | 0.329 to 0.729 |
| rater1__rater3 | control | case_requirements | 90/90 | 87.8% | 0.200 | 0.868 | 0.812 to 0.919 |
| rater1__rater3 | control | G03 | 29/30 | 100.0% | Undefined | 1.000 | 1.000 to 1.000 |
| rater1__rater3 | control | any_error | 29/30 | 55.2% | 0.171 | 0.199 | -0.206 to 0.608 |
| rater2__rater3 | stroke | case_requirements | 357/357 | 95.0% | 0.559 | 0.947 | 0.914 to 0.974 |
| rater2__rater3 | stroke | G03 | 75/75 | 100.0% | Undefined | 1.000 | 1.000 to 1.000 |
| rater2__rater3 | stroke | any_error | 60/75 | 81.7% | 0.222 | 0.765 | 0.614 to 0.886 |
| rater2__rater3 | control | case_requirements | 90/90 | 92.2% | 0.614 | 0.914 | 0.863 to 0.963 |
| rater2__rater3 | control | G03 | 30/30 | 96.7% | 0.000 | 0.966 | 0.895 to 1.000 |
| rater2__rater3 | control | any_error | 30/30 | 80.0% | 0.143 | 0.740 | 0.597 to 0.882 |

AC1 is not a replacement for kappa or evidence that a disputed judgment is correct. Interpret both coefficients with raw agreement, marginal distributions and excluded rows. No qualitative kappa bands are applied to AC1. A constant-label AC1 of 1 and interval [1,1] cannot establish discrimination outside the observed category. Different reviewer pairs may evaluate different report subsets. No pair is ranked and no significance tests compare coefficients.

References: [Gwet, 2008](https://doi.org/10.1348/000711006X126600); [Vach and Gerke, 2023](https://pubmed.ncbi.nlm.nih.gov/37234937/).
