# Validation record

Date: 2026-10-31.

- `python -m unittest discover -s tests -v`: 29 tests passed in the implementation session. The exhaustive-oracle test includes 80 random instances.
- Every one of the 711 saved run records was independently re-audited against its saved input.
- All 79 input SHA-256 hashes were checked.
- All 75 construction witnesses were rechecked for full feasibility.
- Each of 79 instances has exactly three runs for each of three methods.
- Saved summary values equal a fresh summary computed from the raw runs.
- Both generated scientific figures were visually inspected for labels and layout.

The unit tests establish specific checked properties, not an absence of all possible defects. Raw solver status, objective, bound and gap are retained, including time-limited outcomes.

The packaged CLI was smoke-tested with both `demo` and a nine-instance `benchmark` run in separate temporary output directories. Both completed successfully; the main recorded results were preserved.
