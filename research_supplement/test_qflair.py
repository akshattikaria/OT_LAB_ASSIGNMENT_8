import unittest
import numpy as np
from scipy.linalg import expm
from . import qflair as q
from .author_checks.qflair_reconstruction import determine_sine_curve, eq_sin


class QFlairChecks(unittest.TestCase):
    def test_rotation_against_matrix_exponential(self):
        rng = np.random.default_rng(9)
        states = rng.normal(size=(5, 4)) + 1j * rng.normal(size=(5, 4))
        states /= np.linalg.norm(states, axis=1)[:, None]
        for generator in q.GENERATORS:
            np.testing.assert_allclose(generator @ generator, np.eye(4), atol=1e-12)
            for angle in [-2.1, 0., .8]:
                expected = states @ expm(-.5j * angle * generator).T
                np.testing.assert_allclose(q.rotate(states, generator, angle), expected, atol=1e-12)

    def test_reconstruction_against_direct_and_author_function(self):
        rng = np.random.default_rng(10)
        states = rng.normal(size=(6, 4)) + 1j * rng.normal(size=(6, 4))
        states /= np.linalg.norm(states, axis=1)[:, None]
        for generator in q.GENERATORS:
            z = [np.abs(q.rotate(states, generator, a)[:, 0]) ** 2 for a in [0, np.pi / 2, -np.pi / 2]]
            abc = q.coefficients(*z)
            author = determine_sine_curve(*z)
            for angle in np.linspace(-4, 4, 17):
                actual = np.abs(q.rotate(states, generator, angle)[:, 0]) ** 2
                np.testing.assert_allclose(q.reconstruct(abc, angle), actual, atol=1e-12)
                np.testing.assert_allclose(q.reconstruct(abc, angle), eq_sin(angle, *author), atol=1e-12)

    def test_candidate_grid_matches_exhaustive_matrix_calculation(self):
        rng = np.random.default_rng(12)
        x = rng.normal(size=(7, 3)); y = np.array([0, 1, 1, 0, 1, 0, 1])
        states = rng.normal(size=(7, 4)) + 1j * rng.normal(size=(7, 4))
        states /= np.linalg.norm(states, axis=1)[:, None]
        grid = np.linspace(-1, 1, 7)
        best, _, _ = q.candidate_search(states, x, y, grid, 'qflair')
        values = []
        for g, generator in enumerate(q.GENERATORS):
            for f in range(x.shape[1]):
                for w in grid:
                    p = np.array([abs((expm(-.5j * w * row[f] * generator) @ state)[0]) ** 2
                                  for state, row in zip(states, x)])
                    values.append(float(q.loss(y, p)))
        self.assertAlmostEqual(best['loss'], min(values), places=10)

    def test_full_training_matches_direct_grid(self):
        a, b, y, _, _, _ = q.dataset(41, 'xor', 4)
        tr, _, _ = q.scale_train_only(a, b)
        models = [q.train(tr, y, m, grid_size=15, max_gates=5) for m in ['qflair', 'direct_grid']]
        self.assertAlmostEqual(models[0]['loss'], models[1]['loss'], places=10)
        np.testing.assert_allclose(q.predict_probability(tr, models[0]['chain']), q.predict_probability(tr, models[1]['chain']), atol=1e-9)

    def test_reconstruction_query_budget_independent_of_feature_count(self):
        states = np.zeros((9, 4), complex); states[:, 0] = 1
        y = np.arange(9) % 2; grid = np.linspace(-1, 1, 9)
        counts = []
        for d in [2, 20]:
            x = np.random.default_rng(3).normal(size=(9, d))
            _, _, a = q.candidate_search(states, x, y, grid, 'qflair', first=True)
            _, _, b = q.candidate_search(states, x, y, grid, 'direct_grid', first=True)
            counts.append(a); self.assertEqual(b, 9 * d * len(grid) * len(q.POOL))
        self.assertEqual(counts, [2 * len(q.POOL)] * 2)

    def test_preprocessing_does_not_use_test_rows(self):
        tr = np.array([[1., 2], [3, 5], [2, 7]])
        a, _, sa = q.scale_train_only(tr, np.array([[4., 6]]))
        b, _, sb = q.scale_train_only(tr, np.array([[400., -600]]))
        np.testing.assert_array_equal(a, b); self.assertEqual(sa, sb)
        np.testing.assert_array_equal(a[:, -1], np.full(3, np.pi))

    def test_sdk_circuit_matches_stored_chain_convention(self):
        from qiskit import QuantumCircuit
        from qiskit.circuit.library import PauliEvolutionGate
        from qiskit.quantum_info import Statevector, SparsePauliOp
        chain = [{'gate': 0, 'feature': 0, 'weight': .7},
                 {'gate': 7, 'feature': 1, 'weight': -.2},
                 {'gate': 5, 'feature': 0, 'weight': .3}]
        row = np.array([.3, .9]); circ = QuantumCircuit(2)
        for s in chain:
            circ.append(PauliEvolutionGate(SparsePauliOp(q.POOL[s['gate']]), time=s['weight'] * row[s['feature']] / 2), [0, 1])
        expected = Statevector.from_instruction(circ).probabilities()[0]
        self.assertAlmostEqual(q.predict_probability(row[None, :], chain)[0], expected, places=12)

    def test_nll_and_invalid_training(self):
        self.assertAlmostEqual(float(q.loss(np.array([0, 1]), np.array([.2, .8]))), -np.log(.8))
        self.assertAlmostEqual(float(q.loss([0, 1], [.2, .8])), -np.log(.8))
        self.assertTrue(np.isfinite(q.loss(np.array([0, 1]), np.array([1., 0.]))))
        with self.assertRaises(ValueError):q.train(np.empty((0, 2)), np.array([]))

    def test_fixed_dataset_splits_are_disjoint_and_nested(self):
        for kind in ['linear', 'xor']:
            small = q.dataset(11, kind, 4); large = q.dataset(11, kind, 12)
            self.assertTrue(set(small[4]).isdisjoint(small[5]))
            np.testing.assert_array_equal(small[0], large[0][:, :4])
            np.testing.assert_array_equal(small[1], large[1][:, :4])
            np.testing.assert_array_equal(small[2], large[2])


if __name__ == '__main__':
    unittest.main()
