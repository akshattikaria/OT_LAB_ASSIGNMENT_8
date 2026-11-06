# Viva answers

1. **What did you build?** A small arithmetic compiler with a lexer, parser, SSA intermediate representation, four optimization passes and native C output.
2. **What does the lexer do?** Converts characters into tokens such as identifiers, literals, operators and punctuation, retaining positions for syntax errors.
3. **What does the parser do?** Uses the grammar and precedence to build an expression tree and checks immutable, defined variable names.
4. **What is an AST?** A tree describing the source's structure. It keeps expression nesting rather than machine details.
5. **What is SSA?** Each intermediate register is assigned exactly once. Immutable definitions make reuse and dependency analysis easier.
6. **What are your four passes?** Constant folding/propagation, common-subexpression elimination, dead-code elimination and strength reduction.
7. **Constant folding versus propagation?** Folding computes 2*4 as 8. Propagation substitutes that known value into later expressions using it.
8. **What is CSE?** Reuse an earlier pure calculation instead of computing it again, such as x+y and y+x for commutative addition.
9. **What is DCE?** Remove instructions that cannot affect the returned result. It is safe here because operations have no side effects or traps.
10. **What is strength reduction?** Replace a costly modeled operation with a cheaper equivalent, such as unsigned x*8 with x<<3. Real hardware may not reward that rewrite.
11. **How do you handle overflow?** Every operation wraps modulo 2^64. Native C uses uint64_t, so signed-overflow undefined behavior is avoided.
12. **What about shifting by 64?** The toy language masks the count with 63, and generated C does the same. It never performs an undefined 64-bit shift count of 64.
13. **What is the compiler optimization problem?** Choose a permutation of four passes minimizing final weighted IR cost, each pass once.
14. **What is the cost model?** Multiply has weight four; each other IR instruction has weight one. It is a fixed teaching model, not measured CPU cycles.
15. **How does DP work?** Cache the best remaining continuation for a used-pass subset plus its current canonical IR. Try every unused next pass and take the best terminal score.
16. **Why not cache only the subset?** Different orders of the same passes can leave different code. Discarding the IR would incorrectly merge distinct states.
17. **Why canonicalize registers?** Identical computation with different temporary numbers should use the same state key; numbering alone is irrelevant.
18. **Why compare with exhaustive search?** Four passes have only 24 complete orders, so every claimed finite optimum is independently checkable.
19. **What did DP improve?** It matched the exhaustive score optimum on all 20 programs and beat greedy's score on ten. This says nothing automatically about native runtime.
20. **Does DP cost more to compile?** Yes. It explores more states than greedy's ten candidate transitions; the recorded median Python compile time was about 10.08 ms versus 2.71 ms for greedy.
21. **Why O0 and O2?** O0 exposes our passes' teaching effects. O2 is a stronger host-compiler control and already performs many similar optimizations.
22. **Did your compiler beat GCC O2?** No such claim. Extra gains were small or negative; mixed programs averaged a 0.889 ratio and about 2.45 times the baseline native function bytes.
23. **What is instruction count here?** IR body instructions and static native disassembly instructions are separate measures. Neither is a measured retired hardware counter.
24. **How was runtime measured?** A native C loop generates varying inputs and accumulates outputs into a checked checksum, with equal call counts, shuffled trials and all repeat timings retained.
25. **How was correctness checked?** Independent AST evaluation, IR execution and native results agree on edge/random vectors, with all-order tests and an audit that freshly rebuilds C.
26. **Why can code size grow after a good IR optimization?** The IR cost is a model. Target code generation, subsequent host optimizations and instruction selection can produce a different native outcome.
27. **What did the actual AI defect do?** Greedy transformed every candidate twice while reporting ten transitions. Instrumentation found twenty calls. Reusing the computed candidate fixed the waste/accounting.
28. **What is outside scope?** Loops, branches, mutable memory, production C parsing, LLVM/GCC plugins, register allocation and universal runtime optimality.
29. **How would you extend it?** Add control-flow analysis and side-effect rules before loop/memory passes, expand real workloads, and use a target-calibrated cost model with careful validation.

Live demo: run tests and `python -m toycc demo`, inspect examples/demo.toy, compile it to a fresh C file, show the 15-to-6 instruction change, explain the DP state and then show the O2 negative-control chart.
