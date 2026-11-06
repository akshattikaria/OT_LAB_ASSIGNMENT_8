# Explain the Track E experiment

**What did you optimize?** When connected EVs charge, minimizing the electricity bill while meeting energy needs, departure deadlines and station power limits.

**What is a decision variable?** x[i,t] is 1 if EV i charges in slot t, otherwise 0.

**Why power times time?** kW times hours gives kWh. At 7 kW for 15 minutes, input energy is 7*0.25 = 1.75 kWh.

**What is the baseline?** Charge immediately with arrival-order priority. It respects station power but can miss later vehicles' deadlines.

**How does greedy work?** Process earlier departures first and reserve each vehicle's cheapest available slots. Earlier reservations are not reconsidered.

**Why can it fail?** A slot that is cheap for one flexible vehicle may be essential to another with fewer alternatives. A local choice can block a globally feasible plan.

**What does ILP do?** It chooses all binary vehicle-slot actions jointly under exact energy and shared-power constraints. SciPy/HiGHS solves the formulation.

**Did you write the solver from scratch?** No. The solver library is acknowledged. The model, heuristics, audit, experiments and tests were generated with AI assistance, and small cases were checked independently by exhaustive enumeration.

**Is every solver result optimal?** No. A time-limited candidate can be feasible but suboptimal. Status, MIP gap and independent validation must all be examined.

**Why exclude failed schedules from cost comparisons?** Undercharging trivially saves money. Fair comparisons must deliver the same required energy and satisfy the constraints.

**Why no saving with flat prices?** Equal energy at equal price costs the same regardless of charging time. Schedule timing can still affect feasibility and load shape.

**What did the experiments show?** Synthetic flexible-window cases averaged 49.44% lower cost than FCFS. ILP served all 75 main instances and certified 70 optimal within the time budget. These percentages do not predict real-station savings.

**Why can ILP cost more computation?** It builds a joint constrained model and may search among integer choices. Uniform-power instances have useful network-flow structure; unequal charging powers can be harder.

**What are the limitations?** Synthetic data/prices, known future sessions, assigned plugs, fixed rates, slot-aligned demand and no battery dynamics. Peak power is capped, not minimized.

**What would real deployment need?** Actual session/tariff data, physical charger controls, uncertainty handling, charging losses and operating constraints, plus testing with information available at decision time.
