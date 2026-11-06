# Short demonstration and viva guide

The captioned video shows actual EV command output and project evidence. It is an edited guided demonstration, not a claim of a live unscripted recording or a physical charging station. You can present it, add your own narration, or demonstrate the same commands live as required by sir.

1. Explain the process: EVs have arrival/departure windows and need a fixed number of charging slots. Shared station capacity and prices vary by slot.
2. Explain x_it, the cost objective, exact energy equality and the station limit. Undercharging is infeasible, even if the bill is lower.
3. Run `cd tracks/E` then `python -m evcharge demo`. Show all methods feasible with fictional costs 406, 182 and 182.
4. Show the 75-case table. Flexible-case savings are 49.44% on 15 certified matched pairs; baseline/greedy/ILP main feasibility is 64/70/75 out of 75. Flat prices save zero.
5. Show a trade-off: xv6 loses elapsed speed despite less spinning, or compiler O2 erases gains. Explain why the internal objective and actual runtime differ.
6. Show J: 391 to 74 tests and 41.5% lower median wall time, but three of 16 full-suite-detected faults missed. Line coverage is a surrogate.
7. Explain one real AI bug/fix from A, B or D, then distinguish quantum query advantage from CPU simulation speed.

Practice changing a tariff or capacity in a copied tiny EV input and predicting the effect before running it. Be able to explain code and modify it without AI during the viva. Do not claim physical QPU access, real station savings or a completed second-tool comparison.
