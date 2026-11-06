# Mathematical formulation and experimental scope

## Process and evidence of inefficiency

The process is allocating power over time to connected EVs. Charging immediately can purchase energy in expensive periods even when the vehicle remains connected through cheaper periods. Shared power also means an early flexible vehicle can occupy capacity needed by an urgent one.

The synthetic baseline experiments measure this mechanism. They do not establish that a particular real charging station is inefficient. A field claim requires actual station demand, tariffs and operating constraints.

## Variables and units

| Symbol | Meaning | Unit |
|---|---|---|
| i, t | Vehicle and slot indices | — |
| x_it | 1 if EV i charges in slot t; otherwise 0 | binary |
| a_i, d_i | Arrival and exclusive departure boundaries | slots |
| r_i | Required number of charging slots | slots |
| P_i | Fixed charging power when on | kW |
| Delta | slot_minutes/60 | hours |
| c_t | Energy price | rupees/kWh |
| C_t | Shared station power limit | kW |
| E_i = r_i P_i Delta | Required energy at the charging input | kWh |

Minimize:

\[
\sum_i\sum_t c_t P_i\Delta x_{it}.
\]

Subject to:

\[
\sum_t x_{it}=r_i\ \forall i,\qquad \sum_i P_i x_{it}\le C_t\ \forall t,
\]

\[
x_{it}=0\text{ outside }[a_i,d_i),\qquad x_{it}\in\{0,1\}.
\]

The implementation creates variables only for available vehicle-slot pairs. Exact energy equality prevents claiming savings from undercharging and prevents excess charging.

## Assumptions

- Offline scheduling: every method knows the same complete arrival, departure, demand and tariff inputs.
- Every vehicle has an assigned plug throughout its window. The generator provides one plug per vehicle. There is no plug queue or vehicle movement between plugs.
- Main experiments: 48 fifteen-minute slots, 08:00-20:00. Teaching examples and the greedy trap use one-hour slots for hand checking.
- Charging is on/off at fixed power and may pause/resume at slot boundaries. This is a scheduling abstraction, not physical charger-control software.
- Synthetic demands are exactly slot-aligned. No arbitrary real energy request is silently rounded.
- Most cases use 7 kW per EV. The mixed-power stress scenario uses illustrative 7, 11 and 22 kW rates. All prices are fictional.
- Energy is defined at the charging input; battery losses, state-of-charge taper, degradation and switching penalties are outside scope.
- Cost is the sole objective. Peak power is capped and reported, not independently minimized.

## Strategy selection

| Criterion | Baseline | Greedy | Binary integer model |
|---|---|---|---|
| Role | Current-process reference | Chapter 6 heuristic | Chapter 6 integer optimization |
| Decisions | Charge now by arrival priority | Earlier deadlines, cheapest available slots | Joint vehicle-slot allocation |
| Scale | N vehicles, T slots | N vehicles, T slots | At most N*T binary variables, N+T main constraints |
| Quality | No cost or feasibility guarantee | No cost or feasibility guarantee | Optimal only when certified; timeout candidates separate |
| Hardware | CPU | CPU | CPU, SciPy/HiGHS |
| Parallelism | None requested | None requested | No explicit application parallelism; internal solver threading uncontrolled |
| Approximate computation | O(N*T + N log N) | O(N*T log T + N log N) | Solver-dependent, bounded solve time |
| Suitability | Simple reproducible reference | Fast discrete decisions | Linear objective, binary actions and linear constraints |

GD/Adam do not directly produce binary charging decisions. Backpropagation computes gradients, not schedules. Quantum methods belong in their separate tracks; we select this case's methods according to its variables and constraints.

## Uniform-power structure

For identical power P, each slot admits floor(C_t/P) active EVs. A min-cost flow network can have source-to-vehicle arcs of capacity r_i, vehicle-to-time arcs of capacity 1 with charging costs, and time-to-sink arcs of capacity floor(C_t/P). A flow of sum(r_i) gives full service. Thus this restricted problem is not intrinsically hard just because it is written with binaries.

Mixed powers consume unequal station capacity, removing that simple unit-flow interpretation. The ILP interface handles both cases. This project does not claim a new algorithm or superiority over a specialized min-cost-flow implementation.

## Fairness and reproducibility

1. Inputs and available information are identical across methods. Five seeds vary the generated data; the scheduling algorithms are deterministic.
2. Every generated main input has an audited feasible witness. It is never supplied to a solver. Generation retries are recorded, and the feasible-workload selection bias is disclosed.
3. Three timed repetitions use deterministically shuffled method order. All failures/timeouts remain in the evidence. Quality tables use repeat 0, not the best result.
4. Cost savings use matching instances with feasible schedules on both sides. Claims against an optimum require an optimal solver status. Service-failure rates are reported separately.
5. A timeout is not infeasibility. Independently recomputed feasibility does not depend on solver status or its constraint matrix.
6. Method timing includes model construction but excludes imports, data generation, report generation and independent auditing. Audit time is retained separately.
7. The known overload and greedy trap test genuine limitations. No improvement is promised for flat-price or tightly constrained cases.

## Extensions

Real sessions need explicit slot mapping and energy accounting. Continuous charging rates change the formulation. Uncertain departures need rolling-horizon decisions with equal information across competitors. Fewer physical plugs need plug-assignment/queue constraints. Peak-demand charges, service priorities and battery wear need new objective terms and checks.
