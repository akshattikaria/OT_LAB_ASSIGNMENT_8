"""Small Q-FLAIR QNN specialization, arXiv:2510.03389v2, Sec. III/A.1.

Grow a two-qubit feature map by choosing a Pauli rotation, feature and weight.
The two shifted oracle outputs reconstruct every weight/feature candidate.
The comparison queries the identical finite grid directly. Both are ideal CPU
simulations, not hardware experiments or reproductions of the paper's scores.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import balanced_accuracy_score

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.diag([1., -1.]).astype(complex)
PAULIS = {'I': I, 'X': X, 'Y': Y, 'Z': Z}
# A declared subset of the paper's pool. Qiskit labels use q1 tensor q0.
POOL = ('IX', 'IY', 'XI', 'YI', 'XX', 'YY', 'XZ', 'ZX')
GENERATORS = tuple(np.kron(PAULIS[p[0]], PAULIS[p[1]]) for p in POOL)


def rotate(states, generator, angles):
    states = np.asarray(states, dtype=complex)
    angles = np.broadcast_to(np.asarray(angles, dtype=float), states.shape[:-1])
    return (np.cos(angles / 2)[..., None] * states
            - 1j * np.sin(angles / 2)[..., None] * (states @ generator.T))


def coefficients(z0, zplus, zminus):
    """f(a)=u*cos(a)+v*sin(a)+c; equivalent to author amplitude/phase."""
    c = (zplus + zminus) / 2
    return np.asarray(z0) - c, (zplus - zminus) / 2, c


def reconstruct(abc, angles):
    u, v, c = abc
    return u * np.cos(angles) + v * np.sin(angles) + c


def loss(y, probabilities):
    # Probability of class 1 is the all-zero projector, as in the author QNN.
    y = np.asarray(y, dtype=float)
    p = np.clip(probabilities, 1e-12, 1 - 1e-12)
    return np.mean(-y * np.log(p) - (1 - y) * np.log1p(-p), axis=-1)


def candidate_search(states, features, y, weights, method, first=False):
    """Return each gate's best candidate and logical oracle evaluations.

    The direct path evaluates rotations on the grid, without fitted sine curves.
    Vectorizing independent CPU calculations does not change black-box query
    counts. Cached state vectors accelerate both simulators. An actual device
    would need to prepare the preceding circuit for each requested output.
    """
    n, f = features.shape
    result = []
    evaluations = 0
    z0 = np.abs(states[:, 0]) ** 2
    angles = weights[:, None, None] * features.T[None, :, :]
    for gate, generator in enumerate(GENERATORS):
        if method == 'qflair':
            probe = states[:1] if first else states
            zp = np.abs(rotate(probe, generator, np.pi / 2)[:, 0]) ** 2
            zm = np.abs(rotate(probe, generator, -np.pi / 2)[:, 0]) ** 2
            abc = coefficients(z0, np.broadcast_to(zp, n), np.broadcast_to(zm, n))
            probabilities = reconstruct(abc, angles)
            evaluations += 2 * len(probe)
        elif method == 'direct_grid':
            # Each (weight, feature, datum) is evaluated directly. This formula
            # is the all-zero amplitude of the full rotated state, not a fit.
            pg = (states @ generator.T)[:, 0]
            amplitude = (np.cos(angles / 2) * states[:, 0]
                         - 1j * np.sin(angles / 2) * pg)
            probabilities = np.abs(amplitude) ** 2
            evaluations += len(weights) * f * n
        else:
            raise ValueError('Unknown method')
        losses = loss(y, probabilities)
        # A deterministic tolerance breaks numerical symmetry consistently.
        w, feature = min(np.ndindex(losses.shape),
                         key=lambda k: (round(float(losses[k]), 11), k[1], k[0]))
        result.append({'gate': gate, 'pauli': POOL[gate], 'feature': feature,
                       'weight': float(weights[w]), 'grid_index': w,
                       'loss': float(losses[w, feature])})
    best = min(result, key=lambda r: (round(r['loss'], 11), r['gate'],
                                      r['feature'], r['grid_index']))
    return best, result, evaluations


def train(features, y, method='qflair', grid_size=41, max_gates=12, delta=1e-3):
    features, y = np.asarray(features, float), np.asarray(y, int)
    if (features.ndim != 2 or y.shape != (len(features),) or len(features) == 0
            or not np.isfinite(features).all() or not set(y) <= {0, 1}
            or grid_size < 3 or grid_size % 2 == 0 or max_gates < 1):
        raise ValueError('Invalid training data or budget')
    weights = np.linspace(-1., 1., grid_size)
    states = np.zeros((len(y), 4), complex)
    states[:, 0] = 1
    previous = float(loss(y, np.ones(len(y))))
    chain, trace = [], []
    total = 0
    start = time.perf_counter()
    converged = False
    for iteration in range(max_gates):
        best, candidates, queries = candidate_search(
            states, features, y, weights, method, first=iteration == 0)
        states = rotate(states, GENERATORS[best['gate']],
                        best['weight'] * features[:, best['feature']])
        direct_loss = float(loss(y, np.abs(states[:, 0]) ** 2))
        if abs(direct_loss - best['loss']) > 1e-9:
            raise AssertionError('Selected reconstruction does not match circuit')
        improvement = previous - direct_loss
        if improvement < -1e-9:
            raise AssertionError('Identity candidate should prevent increasing loss')
        chain.append(dict(best))
        total += queries
        trace.append({'iteration': iteration, 'previous_loss': previous,
                      'selected': dict(best), 'loss': direct_loss,
                      'improvement': improvement, 'candidates': candidates,
                      'oracle_evaluations': queries})
        previous = direct_loss
        if improvement < delta:
            converged = True
            break
    return {'method': method, 'chain': chain, 'trace': trace,
            'loss': previous, 'oracle_evaluations': total,
            'training_wall_s': time.perf_counter() - start,
            'stopping_reason': 'loss_threshold' if converged else 'gate_cap',
            'grid_size': grid_size, 'max_gates': max_gates, 'delta': delta}


def predict_probability(features, chain):
    states = np.zeros((len(features), 4), complex)
    states[:, 0] = 1
    for step in chain:
        states = rotate(states, GENERATORS[step['gate']],
                        step['weight'] * features[:, step['feature']])
    return np.abs(states[:, 0]) ** 2


def scale_train_only(train_x, test_x):
    lo, hi = train_x.min(axis=0), train_x.max(axis=0)
    span = np.where(hi > lo, hi - lo, 1.)
    transform = lambda x: np.c_[np.clip(2 * (x - lo) / span - 1, -1, 1) * np.pi,
                                np.full(len(x), np.pi)]
    return transform(train_x), transform(test_x), {'min': lo.tolist(), 'max': hi.tolist()}


def select_threshold(y, probabilities):
    values = np.unique(probabilities)
    options = np.r_[0., (values[1:] + values[:-1]) / 2, 1., .5]
    return float(min(options, key=lambda t: (
        -balanced_accuracy_score(y, probabilities >= t), abs(t - .5), t)))


def dataset(seed, kind, dimensions):
    # Same raw pool/row identities at both dimensions; two signal coordinates.
    rng = np.random.default_rng(seed)
    x = rng.uniform(-1, 1, (1024, 12))
    y = ((x[:, 0] + .5 * x[:, 1]) > 0).astype(int) if kind == 'linear' else (
        x[:, 0] * x[:, 1] > 0).astype(int)
    order = [rng.permutation(np.flatnonzero(y == k)) for k in [0, 1]]
    tr = np.r_[order[0][:32], order[1][:32]]
    te = np.r_[order[0][32:64], order[1][32:64]]
    rng.shuffle(tr)
    rng.shuffle(te)
    return x[tr, :dimensions], x[te, :dimensions], y[tr], y[te], tr, te


def run_experiments():
    cases = []
    for kind in ['linear', 'xor']:
        for dimensions in [4, 12]:
            for seed in [11, 41, 59]:
                train_x, test_x, y, test_y, train_ids, test_ids = dataset(seed, kind, dimensions)
                tr, te, scaler = scale_train_only(train_x, test_x)
                order = ['qflair', 'direct_grid']
                np.random.default_rng(seed + dimensions).shuffle(order)
                methods = {}
                for method in order:
                    model = train(tr, y, method)
                    training_p = predict_probability(tr, model['chain'])
                    threshold = select_threshold(y, training_p)
                    t = time.perf_counter()
                    test_p = predict_probability(te, model['chain'])
                    inference_s = time.perf_counter() - t
                    model.update(threshold=threshold, test_probabilities=test_p.tolist(),
                                 test_accuracy=float(np.mean((test_p >= threshold) == test_y)),
                                 balanced_accuracy=float(balanced_accuracy_score(test_y, test_p >= threshold)),
                                 test_loss=float(loss(test_y, test_p)), inference_wall_s=inference_s,
                                 inference_circuit_evaluations=len(test_y))
                    methods[method] = model
                a, b = methods['qflair'], methods['direct_grid']
                if abs(a['loss'] - b['loss']) > 1e-9:
                    raise AssertionError('Paired finite-search optimum mismatch')
                if np.max(np.abs(np.array(a['test_probabilities']) - b['test_probabilities'])) > 1e-8:
                    raise AssertionError('Paired selected circuits disagree')
                t = time.perf_counter()
                lr = LogisticRegression(C=1., max_iter=1000).fit(tr[:, :-1], y)
                lr_seconds = time.perf_counter() - t
                lp = lr.predict_proba(te[:, :-1])[:, 1]
                cases.append({'dataset': kind, 'dimensions': dimensions, 'seed': seed,
                              'raw_train_x': train_x.tolist(), 'raw_test_x': test_x.tolist(),
                              'train_y': y.tolist(), 'test_y': test_y.tolist(),
                              'train_ids': train_ids.tolist(), 'test_ids': test_ids.tolist(),
                              'scaler': scaler, 'method_order': order, 'methods': methods,
                              'logistic': {'test_accuracy': float(np.mean((lp >= .5) == test_y)),
                                           'balanced_accuracy': float(balanced_accuracy_score(test_y, lp >= .5)),
                                           'training_wall_s': lr_seconds,
                                           'parameter_count': dimensions + 1},
                              'query_ratio': b['oracle_evaluations'] / a['oracle_evaluations']})
    return {'source': 'https://arxiv.org/abs/2510.03389v2', 'pool': list(POOL),
            'n_qubits': 2, 'observable': '|00><00| (author QNN convention)',
            'source_equations': 'Sec. III, Eqs. 13–24 and Appendix A.1 / Algorithm 1',
            'scope': 'Scoped QNN port, ideal CPU simulation, not QSVM, hardware or paper-score reproduction.',
            'budgets': {'grid_size': 41, 'max_gates': 12, 'delta': 1e-3,
                        'train_rows': 64, 'test_rows': 64, 'seeds': [11, 41, 59]},
            'counting': 'Logical black-box circuit-output requests in training; first empty-ansatz shifts shared across rows; zero-angle outputs reused; independent audit and inference counted separately. Simulator vectorization/cached states are not quantum hardware.',
            'runs': cases}


def audit_result(path=None):
    data = json.loads(Path(path or Path(__file__).parent / 'results/qflair.json').read_text())
    from scipy.linalg import expm
    assert len(data['runs']) == 12 and data['n_qubits'] == 2
    worst = 0.
    for case in data['runs']:
        assert set(case['train_ids']).isdisjoint(case['test_ids'])
        raw = dataset(case['seed'], case['dataset'], case['dimensions'])
        np.testing.assert_array_equal(raw[0], case['raw_train_x'])
        np.testing.assert_array_equal(raw[1], case['raw_test_x'])
        np.testing.assert_array_equal(raw[2], case['train_y'])
        np.testing.assert_array_equal(raw[3], case['test_y'])
        np.testing.assert_array_equal(raw[4], case['train_ids'])
        np.testing.assert_array_equal(raw[5], case['test_ids'])
        tr, te, scaler = scale_train_only(np.array(case['raw_train_x']), np.array(case['raw_test_x']))
        assert scaler == case['scaler']
        for method, model in case['methods'].items():
            n = len(tr)
            expected = 0
            for i, step in enumerate(model['trace']):
                count = (2 * (1 if i == 0 else n) * len(POOL) if method == 'qflair'
                         else model['grid_size'] * tr.shape[1] * n * len(POOL))
                assert count == step['oracle_evaluations']
                expected += count
                assert step['improvement'] >= -1e-9
            assert model['oracle_evaluations'] == expected
            assert model['threshold'] == select_threshold(case['train_y'], predict_probability(tr, model['chain']))
            # Independent dense matrix-exponential replay, no rotate/reconstruct helper.
            probabilities = []
            for x in te:
                state = np.array([1., 0, 0, 0], complex)
                for step in model['chain']:
                    unitary = expm(-.5j * step['weight'] * x[step['feature']] * GENERATORS[step['gate']])
                    state = unitary @ state
                probabilities.append(float(abs(state[0]) ** 2))
            err = float(np.max(np.abs(np.array(probabilities) - model['test_probabilities'])))
            worst = max(worst, err)
            assert err < 1e-8
            assert model['test_accuracy'] == float(np.mean((np.array(probabilities) >= model['threshold']) == case['test_y']))
            assert np.isclose(model['test_loss'], loss(case['test_y'], np.array(probabilities)), atol=1e-10)
        assert np.isclose(case['query_ratio'], case['methods']['direct_grid']['oracle_evaluations'] / case['methods']['qflair']['oracle_evaluations'])
    return {'passed': True, 'cases': 12, 'paired_training_runs': 24,
            'independent_matrix_exponential_max_error': worst,
            'scope': 'Stored raw data, disjoint splits, train-only scaling/thresholds, paired circuit outputs and logical query accounts.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path)
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    if args.audit:
        print(json.dumps(audit_result(args.out), indent=2))
    else:
        if args.out is None or args.out.exists():
            parser.error('Supply a new --out file')
        data = run_experiments()
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(data, indent=2) + '\n')
        print(json.dumps(audit_result(args.out), indent=2))


if __name__ == '__main__':
    main()
