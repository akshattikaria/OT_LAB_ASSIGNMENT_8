# Integration validation

The retained **4 November 2026** run passes 243 original track host tests: A30, B30, C32, D29, E29, F29, G14, H17, I23 and J10. Seven supplement tests and nine original ChatGPT baseline tests also pass. These are separate from cachetools subject tests and archived xv6 guest tests. Original track code and results were not changed or remeasured by the 6 November comparison update.

On **6 November**, the unchanged ChatGPT and supplied Gemini candidates each passed the same nine test methods, including 100 exhaustive small cases per candidate. Logs and JSON results are retained. No repair was necessary. A separate function benchmark records four input cases, one warmup each and seven paired repetitions with seeded shuffled candidate order: 56 timed function calls. Imports, references and validation are excluded from timing; raw inputs, calls, medians and ranges are retained. Gemini generation latency remains a student estimate of about 60 ± 3 seconds; ChatGPT's is unavailable.

The seven original track audit CLIs (C/D/F/G/H/I/J) passed in isolated copies on 4 November. Those programs can write audit.json, so copied trees preserve every imported byte. Logs are under validation/track_audit_replays/. A/B/E correctness is covered by their host tests and retained records; no absent command is invented.

The updated integrated audit verifies all 2,013 imported file hashes, checklist evidence paths, new comparison source/result identities and paired-trial summaries, 30 HPO policy rows, ASHA constraints, 20 compression runs/conservation checks, 28 layouts, embedding/scheduling invariants, 14 real OpenMP control trials, selected arithmetic and PDF/video metadata. It does not replace historical timings.

All 22 updated PDF pages were rendered for visual review, including enlarged checks of the changed comparison/conclusion pages. All six 1080p video scenes were checked; ffprobe confirms the approximately 100-second silent captioned demonstration. It uses actual retained EV CLI output and project results. See validation/report_visual_check.json for completed review evidence.

The final ZIP is checked for CRC integrity, full manifest equality and imported-file agreement, then re-extracted for a relocation audit. Original A-J sources remain unchanged. Global integration history and per-track histories stay separate. The screenshot's private URL, account and browser details are not redistributed; a textual observation and digest preserve evidence attribution.
