# Observed greedy search-work defect

Date: 2026-11-04. ChatGPT, session-reported model gpt-6.1-sol.

Original commit: **692a02f4653aa65d42e8bcb667c521471f118a7e**.

The original greedy candidate comprehension called the same pass twice: once to score the candidate and again to retain its IR. Passes are pure, so output correctness was unaffected, but this wasted transformation work and made the reported ten transition evaluations understate actual calls. It could bias a compile-time comparison against DP.

This was caught by review and reproduced with instrumented pass wrappers before the recorded benchmark. The actual observation in greedy_search_redundancy_observation.json reports **10 transitions but 20 transformation calls**, with the complete call list and original commit identity.

Fix commit: **7bfdfdba4a729798ec0a4033b2560e3f04dbc6ae**.

Each candidate is now transformed once, scored and retained, and the selected result is reused. Regression `test_greedy_applies_each_candidate_once` instruments the actual functions and requires ten calls matching reported transitions. All 29 tests pass; the final measured compiler uses this correction.

This is an actual redundant-work/accounting defect, not an incorrect-output claim. No deliberately broken implementation or artificial failure was introduced. The original/fix pair is preserved in history.bundle.

Earlier A/B/D packages already document three separate corrected failures: near-zero numerical cancellation, unsafe large expanded QUBO coefficients, and steady timing that included worker startup. The assignment minimum is therefore already covered independently of this additional F observation. No manual student correction or second independent tool contribution is claimed.

Greedy's suboptimal score, strength reduction's negative single-pass timing, DP's higher compilation cost and the negative O2 result are measured algorithm/model/system outcomes, not mislabeled implementation bugs.
