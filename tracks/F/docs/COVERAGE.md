# Track F coverage

| Assignment requirement | Evidence | Status |
| --- | --- | --- |
| Mini-compiler lexer | Own positioned token scanner | Implemented |
| Parser | Own precedence parser and immutable bindings | Implemented |
| Intermediate representation | Three-address SSA, canonicalization, validation and interpreter | Implemented |
| Code generator | Typed unsigned C, compiled and executed natively | Implemented |
| At least two passes, four for full-credit scope | Fold/propagate, CSE, DCE, strength reduction | Four explicit passes implemented |
| Compiler decision formulation | Four-pass order minimizes declared weighted IR cost | Formulated |
| Named Chapter 6 method | Full-state memoized DP vs greedy/fixed and all 24 orders | Implemented; finite optimum verified |
| Instruction counts | IR body counts and saved static native disassembly counts | Measured with distinct definitions |
| Runtime | 1,000 native timings; same varying inputs and checksums | Measured at O0, plus O2 control |
| Code size | Generated function bytes and native symbol sizes | Measured |
| Compile time | 480 Python compiler timings; 40 native builds | Measured separately |
| Output preservation | AST/IR/native triangulation, random/all-order checks, fresh-build audit | Passed |
| AI provenance | Prompt excerpts, actual defect observation, original/fix commits | Included |

The core Track F request is fulfilled on a small appropriate language. Loop passes, register allocation, mutable memory/control-flow analysis and a production-language frontend are not claimed. No LLVM or GCC plugin is implied. The synthetic cost optimum is distinguished from measured native performance, including the negative O2 result.

Overall E/A/B/C/D/F now have working packages. Next is G (xv6), then H (DBMS), I (remaining quantum/QML algorithms) and J (software-engineering optimization). Final integration, full chapter checklist, outstanding research-paper reproductions, independent second-AI-tool comparison, complete chat exports, public repository and demonstration remain pending. Earlier A/B/D provide three documented corrected AI failures; F adds a real search-work/accounting correction.
