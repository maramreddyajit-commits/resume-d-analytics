# Product decision: do not ship this simulated variant

The PM needs a decision that respects performance quality, not just a small conversion p-value. This reproducible trial generates independent randomized units, with binary conversion and positive latency. The illustrative protocol uses a two-sided 5% conversion test and a maximum 10 ms increase in mean latency. Analysis is fixed-horizon; platform splits are explicitly exploratory.

The generator includes a genuine 1.5 percentage-point conversion effect and a 15 ms latency penalty. Report the observed result from METRICS.md rather than substituting either input as a measured outcome. The point estimate, Newcombe/Wilson interval and bootstrap interval quantify uncertainty under the simulation. SRM checks for a departure from expected 50/50 allocation at threshold 0.001; no flag is not proof instrumentation is correct.

Recommendation: do not ship under this scenario's latency guardrail. Build a latency-reduced variant, instrument one stable unit per assignment, define a fixed outcome observation window, and power a new trial for a practically meaningful conversion effect. The current synthetic p-value cannot establish a real product improvement.

Bootstrap uses 10,000 binomial draws per arm: for a binary empirical distribution this is equivalent to sampling its rows with replacement. At all-zero/all-one boundaries, percentile bootstrap degenerates, so the dashboard also uses score intervals and Fisher's exact test. The two-proportion test uses pooled null SE; its CI is not simply pooled-SE ±1.96, avoiding an incorrect confidence interval definition.

The independent check compares the two-sided z p-value with Pearson's uncorrected 2×2 chi-square test. The tiny fixture (1/4 vs 3/4) has +50 percentage points and Fisher p≈0.4857, illustrating that a large observed difference can remain uncertain. The peeking simulation reports how often any unadjusted look is significant, compared with the final look. Do not use repeated fixed-horizon p-values as sequential inference.

Identification requires random assignment, consistent treatment/exposure, no cross-unit interference and complete outcome measurement. The generator enforces these by construction; no real instrumentation quality is inferred.
