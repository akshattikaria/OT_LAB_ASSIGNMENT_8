import itertools
import math
import unittest
import numpy as np
from qiskit.quantum_info import Statevector,Operator
from qstudy.circuits import deutsch_jozsa,bernstein_vazirani,qft,phase_estimation,grover,grover_rounds,modular_multiply,shor_order_circuit,factor_from_sample,cut_values,qaoa,vqe,vqe_energy,HAM,marginal,annealing
from qstudy.learning import feature_map,analytic_feature_state,quantum_grams,dataset


class CircuitTests(unittest.TestCase):
    def test_all_deutsch_functions(self):
        for table in itertools.product((0,1),repeat=2):self.assertAlmostEqual(marginal(deutsch_jozsa(table),1)[0],float(table[0]==table[1]),places=10)
    def test_all_promised_two_bit_dj_functions(self):
        count=0
        for table in itertools.product((0,1),repeat=4):
            if sum(table) in (0,2,4):self.assertAlmostEqual(marginal(deutsch_jozsa(table),2)[0],float(sum(table) in (0,4)),places=10);count+=1
        self.assertEqual(count,8)
    def test_dj_promise_rejected(self):
        with self.assertRaises(ValueError):deutsch_jozsa([0,0,0,1])
    def test_all_three_bit_hidden_strings(self):
        for secret in range(8):self.assertAlmostEqual(marginal(bernstein_vazirani(3,secret),3)[secret],1,places=10)
    def test_qft_matches_independent_fourier_matrix(self):
        for n in (1,2,3,4):
            size=1<<n;expected=np.exp(2j*np.pi*np.outer(np.arange(size),np.arange(size))/size)/np.sqrt(size)
            np.testing.assert_allclose(Operator(qft(n)).data,expected,atol=1e-12)
    def test_fourier_inverse_identity(self):
        qc=qft(4);qc.compose(qft(4).inverse(),inplace=True);np.testing.assert_allclose(Operator(qc).data,np.eye(16),atol=1e-12)
    def test_qpe_every_three_bit_exact_phase(self):
        for value in range(8):self.assertAlmostEqual(marginal(phase_estimation(3,value/8),3)[value],1,places=10)
    def test_qpe_non_grid_dirichlet_distribution(self):
        phase=1/3;size=16;expected=np.abs(np.array([sum(np.exp(2j*np.pi*np.arange(size)*(phase-m/size)))/size for m in range(size)]))**2
        np.testing.assert_allclose(marginal(phase_estimation(4,phase),4),expected,atol=1e-12)
    def test_grover_every_two_bit_mark(self):
        for mark in range(4):self.assertAlmostEqual(marginal(grover(2,mark),2)[mark],1,places=10)
    def test_grover_analytic_probability_sizes(self):
        for n in (3,4,5):
            r=grover_rounds(n);expected=np.sin((2*r+1)*np.arcsin(2**(-n/2)))**2
            self.assertAlmostEqual(marginal(grover(n,3),n)[3],expected,places=10)
    def test_modular_matrix_bijection(self):
        for a in (2,7,11,13,14):
            matrix=modular_multiply(15,a);np.testing.assert_allclose(matrix.conj().T@matrix,np.eye(16));self.assertEqual(matrix[15,15],1)
    def test_invalid_modular_multiply(self):
        with self.assertRaises(ValueError):modular_multiply(15,3)
    def test_shor_order_finding_peaks_without_period_in_circuit(self):
        expected=np.zeros(16);expected[[0,4,8,12]]=.25;np.testing.assert_allclose(marginal(shor_order_circuit(15,2,4),4),expected,atol=1e-10)
    def test_factor_postprocessing_rejects_unhelpful_results(self):
        self.assertEqual(factor_from_sample(4,4,15,2)['factors'],[3,5]);self.assertEqual(factor_from_sample(12,4,15,2)['factors'],[3,5])
        self.assertEqual(factor_from_sample(0,4,15,2)['factors'],[]);self.assertEqual(factor_from_sample(8,4,15,2)['factors'],[]);self.assertEqual(factor_from_sample(8,4,15,14)['factors'],[])
    def test_vqe_dense_energy_and_shift_gradient(self):
        theta=np.array([.2,-.6,1.1,.7]);state=Statevector.from_instruction(vqe(theta)).data
        z=np.diag([1,-1]);x=np.array([[0,1],[1,0]]);identity=np.eye(2);dense=.5*np.kron(z,identity)-.4*np.kron(identity,z)+.3*np.kron(x,x)+.2*np.kron(z,z)
        np.testing.assert_allclose(HAM.to_matrix(),dense);self.assertAlmostEqual(vqe_energy(theta),np.real(state.conj()@dense@state))
        for i in range(4):
            step=np.eye(4)[i];shift=(vqe_energy(theta+np.pi/2*step)-vqe_energy(theta-np.pi/2*step))/2;finite=(vqe_energy(theta+1e-6*step)-vqe_energy(theta-1e-6*step))/2e-6
            self.assertAlmostEqual(shift,finite,places=7)
    def test_qaoa_baseline_and_problem_optimum(self):
        values=cut_values();self.assertEqual(values.max(),4);self.assertEqual(sum(values==4),2);self.assertAlmostEqual(float(marginal(qaoa([0,0]),4)@values),2.5)
    def test_anneal_zero_time_uniform(self):
        np.testing.assert_allclose(marginal(annealing(0,8),4),np.ones(16)/16,atol=1e-12)


class LearningTests(unittest.TestCase):
    def test_feature_map_independent_amplitudes(self):
        for x in ([0,0],[.2,-.5],[-1.1,.7]):np.testing.assert_allclose(Statevector.from_instruction(feature_map(x)).data,analytic_feature_state(x),atol=1e-12)
    def test_overlap_grams_and_counts(self):
        x=np.array([[.1,.2],[.3,-.4],[-.8,.7]]);xt=np.array([[0,1],[.9,.4]]);train,test,counters=quantum_grams(x,xt);a=np.array([analytic_feature_state(t) for t in x]);b=np.array([analytic_feature_state(t) for t in xt])
        np.testing.assert_allclose(train,abs(a.conj()@a.T)**2,atol=1e-12);np.testing.assert_allclose(test,abs(b.conj()@a.T)**2,atol=1e-12);self.assertEqual(counters['overlap_circuit_evaluations'],9);self.assertGreaterEqual(np.linalg.eigvalsh(train).min(),-1e-10)
    def test_no_test_leakage_and_reproducibility(self):
        a=dataset('moons',0);b=dataset('moons',0);np.testing.assert_array_equal(a['x_train'],b['x_train']);self.assertFalse(set(a['train_indices'])&set(a['test_indices']))
        np.testing.assert_allclose(a['mean'],a['x_raw'][a['train_indices']].mean(axis=0));self.assertEqual(np.bincount(a['y_test']).tolist(),[30,30])
    def test_invalid_features_rejected(self):
        with self.assertRaises(ValueError):feature_map([1,float('nan')])


if __name__=='__main__':unittest.main()
