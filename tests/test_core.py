import math
import random
import unittest
from dataclasses import replace

import numpy as np

from evcharge.data import SCENARIOS, generate, greedy_trap, infeasible_example, teaching_example
from evcharge.model import Instance, Vehicle
from evcharge.solvers import baseline, exhaustive, greedy, integer_optimize
from evcharge.verify import audit


class KnownAnswers(unittest.TestCase):
    def test_teaching_values(self):
        case = teaching_example()
        self.assertEqual(audit(case,baseline(case).schedule)["cost"],406)
        for solver in (greedy,integer_optimize,exhaustive):
            check = audit(case,solver(case).schedule)
            self.assertTrue(check["feasible"],check)
            self.assertAlmostEqual(check["cost"],182)
            self.assertEqual(check["energy_kwh"],35)

    def test_flat_prices_equal_service_equal_cost(self):
        case = teaching_example(flat=True)
        for solver in (baseline,greedy,integer_optimize):
            check = audit(case,solver(case).schedule)
            self.assertTrue(check["feasible"])
            self.assertAlmostEqual(check["cost"],280)

    def test_greedy_can_fail_on_feasible_input(self):
        case = greedy_trap()
        check = audit(case,greedy(case).schedule)
        self.assertFalse(check["feasible"])
        self.assertEqual(check["unmet_kwh"],7)
        exact = integer_optimize(case)
        self.assertEqual(exact.status,"optimal")
        self.assertAlmostEqual(audit(case,exact.schedule)["cost"],35)
        self.assertTrue(audit(case,baseline(case).schedule)["feasible"])

    def test_overloaded_is_infeasible(self):
        case = infeasible_example()
        self.assertEqual(integer_optimize(case).status,"infeasible")
        self.assertEqual(exhaustive(case).status,"infeasible")
        for solver in (baseline,greedy):
            self.assertFalse(audit(case,solver(case).schedule)["feasible"])

    def test_quarter_hour_units(self):
        case = Instance("units",15,(8,)*4,(7,)*4,(Vehicle("A",0,4,2),))
        check = audit(case,integer_optimize(case).schedule)
        self.assertTrue(check["feasible"])
        self.assertEqual(check["energy_kwh"],3.5)
        self.assertEqual(check["cost"],28)

    def test_empty_fleet(self):
        case = Instance("empty",15,(8,)*4,(0,)*4,())
        for solver in (baseline,greedy,integer_optimize,exhaustive):
            self.assertTrue(audit(case,solver(case).schedule)["feasible"])

    def test_zero_demand(self):
        case = Instance("zero",15,(8,)*4,(0,)*4,(Vehicle("A",0,4,0),))
        for solver in (baseline,greedy,integer_optimize):
            check = audit(case,solver(case).schedule)
            self.assertTrue(check["feasible"])
            self.assertEqual(check["cost"],0)

    def test_demand_exceeds_window(self):
        case = Instance("short",15,(8,)*4,(7,)*4,(Vehicle("A",0,2,3),))
        case.validate()  # Well-formed, but mathematically infeasible.
        self.assertEqual(integer_optimize(case).status,"infeasible")
        self.assertEqual(exhaustive(case).status,"infeasible")

    def test_variable_capacity_and_power(self):
        case = Instance("mixed",15,(1,5,3,2),(7,11,18,7),
                        (Vehicle("A",0,4,2,7),Vehicle("B",0,4,2,11)))
        ilp, oracle = integer_optimize(case), exhaustive(case)
        self.assertEqual(ilp.status,oracle.status)
        self.assertTrue(audit(case,ilp.schedule)["feasible"])
        self.assertAlmostEqual(audit(case,ilp.schedule)["cost"],oracle.details["objective"])

    def test_no_capacity(self):
        case = Instance("none",15,(8,)*4,(0,)*4,(Vehicle("A",0,4,1),))
        self.assertEqual(integer_optimize(case).status,"infeasible")


class CheckerAdversarial(unittest.TestCase):
    def setUp(self):
        self.case = teaching_example()
        self.good = baseline(self.case).schedule

    def test_fractional(self):
        x = self.good.astype(float); x[0,0] = 0.5
        self.assertFalse(audit(self.case,x)["feasible"])

    def test_nan(self):
        x = self.good.astype(float); x[0,0] = math.nan
        self.assertFalse(audit(self.case,x)["feasible"])

    def test_negative(self):
        x = self.good.astype(float); x[0,0] = -1
        self.assertFalse(audit(self.case,x)["feasible"])

    def test_excess_energy(self):
        x = self.good.copy(); x[0,2] = 1
        self.assertFalse(audit(self.case,x)["feasible"])

    def test_missing_energy(self):
        x = self.good.copy(); x[0,0] = 0
        self.assertFalse(audit(self.case,x)["feasible"])

    def test_departure_is_exclusive(self):
        x = self.good.copy(); x[0,0] = 0; x[0,3] = 1
        result = audit(self.case,x)
        self.assertFalse(result["feasible"])
        self.assertEqual(result["outside_window_slots"],1)

    def test_station_overload(self):
        x = self.good.copy(); x[3,2] = 0; x[3,1] = 1
        result = audit(self.case,x)
        self.assertFalse(result["feasible"])
        self.assertEqual(result["max_capacity_excess_kw"],7)

    def test_wrong_shape(self):
        self.assertFalse(audit(self.case,np.zeros((1,6)))["feasible"])

    def test_none(self):
        self.assertFalse(audit(self.case,None)["feasible"])

    def test_small_numerical_error_is_accepted(self):
        x = self.good.astype(float); x[0,0] -= 1e-9
        self.assertTrue(audit(self.case,x)["feasible"])


class InputValidation(unittest.TestCase):
    def test_bad_prices(self):
        for value in (float("nan"),float("inf"),-1,"8",True):
            with self.subTest(value=value),self.assertRaises(ValueError):
                replace(teaching_example(),prices=(value,)*6).validate()

    def test_duplicate_ids(self):
        v = Vehicle("A",0,6,1)
        with self.assertRaises(ValueError):
            replace(teaching_example(),vehicles=(v,v)).validate()

    def test_bad_window(self):
        for v in (Vehicle("A",0,0,1),Vehicle("A",-1,3,1),Vehicle("A",0,7,1),Vehicle("A",0.5,3,1)):
            with self.subTest(v=v),self.assertRaises(ValueError):
                replace(teaching_example(),vehicles=(v,)).validate()

    def test_bad_demand(self):
        for demand in (-1,0.5,True):
            with self.subTest(demand=demand),self.assertRaises(ValueError):
                replace(teaching_example(),vehicles=(Vehicle("A",0,6,demand),)).validate()

    def test_bad_power_or_lengths(self):
        with self.assertRaises(ValueError):
            replace(teaching_example(),vehicles=(Vehicle("A",0,6,1,0),)).validate()
        with self.assertRaises(ValueError):
            replace(teaching_example(),capacity_kw=(14,)).validate()

    def test_json_roundtrip(self):
        original = teaching_example()
        self.assertEqual(original,Instance.from_dict(original.to_dict()))


class IndependentOracle(unittest.TestCase):
    def test_eighty_random_small_instances(self):
        for seed in range(80):
            rng = random.Random(seed)
            vehicles = []
            for i in range(3):
                a = rng.randrange(0,4); d = rng.randrange(a+1,7)
                vehicles.append(Vehicle(str(i),a,d,rng.randrange(0,min(3,d-a)+1),rng.choice((3,7,11))))
            case = Instance(f"oracle{seed}",15,tuple(rng.randrange(0,15) for _ in range(6)),
                            tuple(rng.choice((7,14,21)) for _ in range(6)),tuple(vehicles))
            with self.subTest(seed=seed):
                exact, oracle = integer_optimize(case), exhaustive(case)
                self.assertEqual(exact.status,oracle.status)
                if oracle.status == "optimal":
                    checked = audit(case,exact.schedule)
                    self.assertTrue(checked["feasible"],checked)
                    self.assertAlmostEqual(checked["cost"],oracle.details["objective"],places=6)
                    self.assertAlmostEqual(checked["cost"],exact.details["objective"],places=6)

    def test_oracle_guard(self):
        case,_ = generate(20,0)
        with self.assertRaises(ValueError):
            exhaustive(case,max_candidates=100)

    def test_generator_reproducibility_and_witnesses(self):
        for scenario in SCENARIOS:
            for n in (10,20,30):
                with self.subTest(scenario=scenario,n=n):
                    a,x = generate(n,3,scenario)
                    b,y = generate(n,3,scenario)
                    self.assertEqual(a,b)
                    np.testing.assert_array_equal(x,y)
                    self.assertTrue(audit(a,x)["feasible"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
