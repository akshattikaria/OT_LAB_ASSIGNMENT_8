# Genuine failure: incorrect steady timing boundary

Date: 2026-11-03. Tool/model: ChatGPT, session-reported gpt-6.1-sol.

## Original code and observation

Original commit: **1546c0f6c477e69b394cb08d421205b4e5a249b2**.

The process benchmark started its supposed steady timer after calling Process.start(), then waited at a barrier for all children. Process.start() returns before child initialization finishes, so the timer included remaining worker startup. This contradicted its intended separation of steady work from end-to-end execution and could distort scaling comparisons.

A real tiny-task reproduction used four jobs, two workers and one PBKDF2 iteration/job. In docs/startup_timing_bug_observation.json, steady time was **0.059120924 s**, total timed kernel intervals were **0.000255204 s**, and the first job began **0.058199989 s** after the timer started. Almost all of the nominal steady interval preceded task execution.

This was an actual AI-generated measurement defect, caught by code review and reproduced before the recorded parallel benchmarks. It is not a deliberately slow algorithm or an invented failure.

## Correction

Fix commit: **3e037b9d4513de8b27bc4dfdc07524270818f7b5**.

Each worker now sends a timestamped readiness message, then waits at its barrier. The parent receives every readiness message before starting the steady timer and releasing that barrier. End-to-end timing still includes setup/initialization and cleanup. The same correction applies to synchronization workers; pipeline threads also signal readiness.

The corrected tiny-task observation is in startup_timing_fix_observation.json. Its steady interval was about **0.000643257 s**, while end-to-end remained **0.110224979 s**. These two single observations illustrate the timing boundary, not a controlled performance-speedup result.

Regression: `test_steady_timer_starts_after_all_workers_ready` asserts that the recorded start follows every readiness timestamp and that elapsed time equals the retained finish-minus-start boundary. It uses no fragile absolute timing threshold. All 29 final tests pass. The result audit checks this boundary for all 108 strong/weak runs and all synchronization cases.

Lesson: worker creation, readiness and useful work are different events. Record the timing boundary that supports each performance claim, and retain end-to-end costs as well.

## Separate execution issues

The first test run found that socket-based multiprocessing Manager listeners were blocked in this environment. Work stealing was changed to explicitly locked shared-memory arrays; initial_test_failure.txt retains the actual error. This is an environment/transport issue and is not counted as an extra mathematical defect.

A resource-resume attempt launched via stdin failed because spawn needs an importable main module. It was interrupted without retaining timings and replaced by the guarded distopt.resume_resources module. The delivered CLI uses guarded module entry points. Previously completed learning files were hash-preserved during recovery; results/resume_record.json records this.

The greedy counterexample, non-submodular control, imperfect efficiency, poor end-to-end scaling and task trade-offs are expected algorithm/system phenomena, not code failures.

## Assignment-wide count

| Track | Genuine corrected defect | Evidence |
| --- | --- | --- |
| A | Near-zero cancellation in sqrt(1+x²)−1 | Original/fix commits and regression in A package |
| B | Expanded floating-point QUBO erased a reward difference at huge coefficients | Original/fix commits, reproduction and range-guard regression in B package |
| D | Steady timing incorrectly included worker startup | Original/fix commits, observed timing records and readiness regression here |

Three genuine cases are now documented. All corrections here are AI-assisted; no manual student correction or second independent AI-tool comparison is claimed.
