# Formulation and soundness

## Language and compilation pipeline

Grammar: `fn name(params) { (let name = expr;)* return expr; }`. Parameters/bindings are immutable and unique. Expressions support uint64 literals/names, parentheses, unary plus/minus, and +, -, *, ^, &, |, <<, >>. Precedence is explicit in the parser. No loop, branch, mutation, function call, pointer, division, I/O or exception exists.

Each operation is evaluated modulo 2^64. Unary minus is modular negation. Shift amounts use their low six bits; right shift is logical unsigned. Literal values must be 0 through 2^64−1. These are the toy language's defined semantics, not assumptions about arbitrary signed C or floating-point programs.

The lexer emits positioned tokens. The parser produces its own AST; no Python eval, exec or ast parser is used. Lowering emits immutable three-address SSA with one definition per register. The validator requires prior definitions for every operand, correct arity, valid constants/arguments and a defined return value. Canonicalization renumbers by instruction order, allowing safe state-key comparisons. A separate register interpreter and generated unsigned C provide two further evaluation paths beyond the AST reference.

## Four transformations

1. Constant folding/propagation replaces constant-only operations with their exact modular result, propagates aliases and applies valid identities such as x+0=x, x*1=x, x*0=0 and x xor x=0. It preserves the mask on shifts, including counts 64 and 65.
2. Common-subexpression elimination keys pure operations by opcode and resolved operands, canonicalizing only commutative operators. SSA immutability means earlier results cannot become stale. Subtraction and shifts are not commuted.
3. Dead-code elimination walks backward from the returned register, retaining dependencies. Removal is safe because all expressions are pure and total; removing division-by-zero traps, I/O or stores would require a different analysis and is outside this language.
4. Strength reduction changes multiplication by a positive power of two 2^k to an unsigned shift by k, including k=63. Multiplication by zero/non-powers is left unchanged. Unsigned wrapping makes the identity valid on overflow. The pass can introduce a new shift-count constant; cleanup order affects the final IR.

Each pass validates/canonicalizes its result and does not mutate its input. Finite differential tests support these arguments but are not a proof of correctness for an unrestricted compiler.

## Compiler decision

Let P contain four passes. Decision pi is a permutation using every pass once. Let T_p(I) transform IR I. Minimize

C(T_pi4(T_pi3(T_pi2(T_pi1(I0)))))

where C(I) sums instruction weights: multiplication 4, all other instructions 1, including argument and constant loads. This fixed synthetic target model was specified before the main benchmark. It is not measured CPU cycles or a universal strength-reduction model.

DP state is (M,I): used-pass bit mask M plus canonical transformed IR I. Terminal value V(all,I)=C(I). Recurrence:

V(M,I)=min_{p not in M} V(M union {p}, T_p(I)).

The implementation memoizes the full state, returns a lexicographically deterministic optimal continuation, and records cache/state/transition counts. The IR component is essential: the same subset can leave different code after different orders. Equal transformed states can share a suffix; different code is not silently merged by subset alone. Four passes have at most 65 unmerged prefix states and 24 terminal permutations. Worst-case search still grows rapidly with more passes.

The fixed order is fold,CSE,strength,DCE. Greedy chooses the next pass minimizing immediate score; there are 4+3+2+1=10 candidate transformations. Full permutation enumeration is an independent finite optimality oracle. The proof concerns exactly these transformations, four single uses and the stated cost. It does not claim to minimize native runtime, machine instructions or all possible compiler sequences.

## Correctness and measurements

AST/IR/native C must produce identical uint64 values on the same inputs, including wraparound/high bits and arbitrary shift counts. Generated C uses uint64_t and masks shifts. Hex strings preserve precise uint64 benchmark inputs/results in portable JSON. Native timed calls return a consumed checksum; a separate 64-iteration AST loop verifies the C driver. Timings use varying LCG inputs, so generated work is not a constant-input loop.

Eight variants comprise baseline, four single-pass ablations, fixed, greedy and DP. Main workload: four synthetic families, five generated programs/family. Each has three Python compile repeats; every variant is timed five times at O0, while baseline/DP are additionally timed five times at O2. Each timing makes 100,000 native calls. Trial order is shuffled in advance, with equal per-variant warmup and seed/iteration budgets. Medians use all repeats; family means average within-program ratios. Shared-host variability and short runs limit inference.

IR instruction counts exclude the return/driver and equal executed register-body instructions per invocation because source code is straight-line. Static objdump instruction counts include padding; they are not dynamic retired-instruction counters. nm symbol sizes measure each native function, not the entire shared library. Source-function bytes measure generated C text. Python compile time includes fresh lex/parse/lower, transformation/search and C generation. Native C compilation is measured per combined translation unit containing all eight variants; it is not attributed to one variant.

O0 deliberately exposes pedagogical transformations. O2 is the stronger host-compiler control. The mixed family's lower IR cost produced larger/slower O2 native functions, demonstrating model mismatch rather than contradicting DP's declared finite objective. No global production-compiler advantage or statistical significance is claimed.
