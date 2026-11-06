import hashlib
import itertools
from pathlib import Path
import unittest
import numpy as np
from scipy.linalg import expm

from qopt import simulator as s
from qopt.models import VQEOracle,parameter_shift,fs_metric,hamiltonian
from qopt.experiment import load_problems,classical_baselines,shot_study,qaoa_train
from qopt.optimizers import spsa_gradient,train_vqe
from qopt.qnn import dataset,outputs,loss_and_gradient

ROOT=Path(__file__).resolve().parents[1]


def dense_one(n,q,U):
    result=np.array([[1]],complex)
    for k in reversed(range(n)):result=np.kron(result,U if k==q else np.eye(2))
    return result


class QuantumTests(unittest.TestCase):
    def assertClose(self,a,b,tol=1e-9):np.testing.assert_allclose(a,b,rtol=0,atol=tol)

    def test_rotation_unitarity(self):
        for axis in 'XYZ':
            for angle in (-3.7,0.,.42):
                U=s.rotation(axis,angle);self.assertClose(U.conj().T@U,np.eye(2))

    def test_little_endian_basis(self):
        for q in range(4):self.assertEqual(np.argmax(abs(s.one(s.zero(4),q,s.X))),1<<q)

    def test_dense_single_gate(self):
        rng=np.random.default_rng(1);v=rng.normal(size=16)+1j*rng.normal(size=16);v/=np.linalg.norm(v)
        for q in range(4):
            U=s.rotation('Y',.73);self.assertClose(s.one(v,q,U),dense_one(4,q,U)@v)

    def test_cnot_truth_table(self):
        for control,target in itertools.permutations(range(3),2):
            for index in range(8):
                v=np.eye(8)[index];expected=index^(((index>>control)&1)<<target)
                self.assertEqual(np.argmax(abs(s.cx(v,control,target))),expected)

    def test_bell_state(self):
        self.assertClose(s.statevector(2,[('h',0),('cx',0,1)]),np.array([1,0,0,1])/np.sqrt(2))

    def test_density_matches_outer_product(self):
        gates=s.hardware_gates(np.random.default_rng(2).normal(size=12),3,2)
        v=s.statevector(3,gates);self.assertClose(s.density(3,gates),np.outer(v,v.conj()))

    def test_density_single_gate_dense(self):
        v=s.statevector(2,[('h',0),('cx',0,1)]);rho=np.outer(v,v.conj());U=s.rotation('Y',.39);D=dense_one(2,1,U)
        self.assertClose(s.density_one(rho,1,U),D@rho@D.conj().T)

    def test_depolarizing_identity(self):
        v=s.statevector(2,[('h',0),('cx',0,1)]);rho=np.outer(v,v.conj())
        self.assertClose(s.depolarize(rho,0,0),rho)
        self.assertClose(s.depolarize(rho,0,1),np.eye(4)/4)

    def test_noisy_density_physical(self):
        gates=s.hardware_gates(np.random.default_rng(3).normal(size=24),3,4);rho=s.density(3,gates,.03)
        self.assertClose(rho,rho.conj().T);self.assertAlmostEqual(np.trace(rho).real,1)
        self.assertGreaterEqual(np.linalg.eigvalsh(rho)[0],-1e-12)

    def test_readout_endpoints(self):
        p=np.arange(1,9)/36
        self.assertClose(s.readout(p,3,0),p);self.assertClose(s.readout(p,3,.5),np.ones(8)/8)
        self.assertClose(s.readout(p,3,1),p[::-1])

    def test_pauli_dense_oracle(self):
        v=s.hardware_state(np.arange(12)/7,3,2);rho=np.outer(v,v.conj())
        for term in ([(0,'Y')],[(1,'X'),(2,'Y')],[(0,'Z'),(1,'Y'),(2,'X')]):
            D=s.dense_pauli(3,term);expected=np.vdot(v,D@v).real
            self.assertAlmostEqual(s.pauli_expectation(v,term),expected)
            self.assertAlmostEqual(s.pauli_expectation(rho,term),expected)

    def test_measurement_basis_y_and_mixed_axes(self):
        v=s.hardware_state(np.arange(12)/5,3,2)
        for term in ([(0,'Y')],[(0,'X'),(2,'Y')],[(1,'Z')]):
            expected=s.pauli_expectation(v,term)
            for state in (v,np.outer(v,v.conj())):self.assertAlmostEqual(s.measured_pauli(state,term,None,None),expected)

    def test_seeded_born_sampling(self):
        v=s.statevector(1,[('ry',0,.8)]);term=[(0,'Z')]
        a=s.measured_pauli(v,term,20000,np.random.default_rng(4));b=s.measured_pauli(v,term,20000,np.random.default_rng(4))
        self.assertEqual(a,b);self.assertLess(abs(a-np.cos(.8)),.03)

    def test_invalid_simulator_inputs(self):
        for call in (lambda:s.zero(0),lambda:s.one(s.zero(2),2,s.X),lambda:s.cx_permutation(2,0,0),
                     lambda:s.rotation('A',0),lambda:s.probabilities(np.ones(4)),lambda:s.depolarize(np.eye(2)/2,0,1.1),
                     lambda:s.measured_pauli(s.zero(1),[(0,'Z')],0,np.random.default_rng(1)),lambda:s.density(7,[])):
            with self.assertRaises(ValueError):call()

    def test_shift_analytic_ry(self):
        f=lambda a:s.pauli_expectation(s.statevector(1,[('ry',0,a[0])]),[(0,'Z')])
        self.assertClose(parameter_shift(f,np.array([.37])),[-np.sin(.37)])

    def test_shift_vqe_finite_difference(self):
        theta=np.random.default_rng(5).normal(size=8);oracle=VQEOracle();gradient=parameter_shift(oracle,theta);eps=1e-5
        fd=np.array([(oracle(theta+np.eye(8)[j]*eps)-oracle(theta-np.eye(8)[j]*eps))/(2*eps) for j in range(8)])
        self.assertClose(gradient,fd,1e-8)

    def test_vqe_dense_energy_and_bound(self):
        oracle=VQEOracle();H=hamiltonian();ground=np.linalg.eigvalsh(H)[0]
        for theta in np.random.default_rng(6).normal(size=(15,8)):
            v=s.hardware_state(theta,2,2);E=oracle(theta)
            self.assertAlmostEqual(E,np.vdot(v,H@v).real);self.assertGreaterEqual(E,ground-1e-12)

    def test_metric_finite_difference(self):
        theta=np.random.default_rng(7).normal(size=8);state=lambda a:s.hardware_state(a,2,2)
        psi=state(theta);eps=1e-5;D=np.column_stack([(state(theta+eps*e)-state(theta-eps*e))/(2*eps) for e in np.eye(8)])
        expected=np.real(D.conj().T@(np.eye(4)-np.outer(psi,psi.conj()))@D)
        self.assertClose(fs_metric(state,theta),expected,1e-8)

    def test_metric_global_phase_and_ry(self):
        rz=lambda a:s.statevector(1,[('rz',0,a[0])]);ry=lambda a:s.statevector(1,[('ry',0,a[0])])
        self.assertClose(fs_metric(rz,np.array([.5])),[[0]])
        self.assertClose(fs_metric(ry,np.array([.5])),[[.25]])

    def test_metric_psd_and_rank(self):
        metric=fs_metric(lambda a:s.hardware_state(a,2,2),np.arange(8)/3)
        self.assertClose(metric,metric.T);self.assertGreaterEqual(np.linalg.eigvalsh(metric)[0],-1e-12)
        self.assertLessEqual(np.linalg.matrix_rank(metric,tol=1e-9),6)

    def test_spsa_two_calls(self):
        calls=[]
        def f(a):calls.append(a.copy());return float(a@a)
        spsa_gradient(f,np.arange(50)/10,.1,np.random.default_rng(8));self.assertEqual(len(calls),2)

    def test_spsa_average_directions(self):
        class Direction:
            def __init__(self,d):self.d=np.array(d)
            def choice(self,*args,**kwargs):return self.d
        theta=np.array([.3,-.8]);A=np.array([[2.,.3],[.3,1.]])
        gradients=[spsa_gradient(lambda x:float(x@A@x),theta,.01,Direction(d)) for d in itertools.product((-1,1),repeat=2)]
        self.assertClose(np.mean(gradients,axis=0),2*A@theta)

    def test_vqe_work_accounting(self):
        for method in ('ShiftGD','ShiftAdam','SPSA','QNG'):
            run=train_vqe(method,0,steps=5,shots=32);w=run['work'];per_step=2 if method=='SPSA' else 16
            self.assertEqual(w['objective_calls'],5*per_step+2)
            self.assertEqual(w['shots'],w['objective_calls']*4*32)
            self.assertEqual(w['metric_preparations'],85 if method=='QNG' else 0)
            self.assertEqual(w['state_preparations'],w['objective_calls']+w['metric_preparations'])
            self.assertEqual(w['diagnostic_preparations'],2)

    def test_same_vqe_initialization(self):
        runs=[train_vqe(method,0,steps=5) for method in ('ShiftGD','ShiftAdam','SPSA','QNG')]
        for r in runs:self.assertClose(r['initial'],runs[0]['initial'])

    def test_track_b_exact_minima_and_bits(self):
        p=load_problems(ROOT/'inputs'/'track_b');self.assertEqual(p['maxcut_4bit'].minimum,-4);self.assertEqual(p['knapsack_6bit'].minimum,-6)
        self.assertClose(p['knapsack_6bit'].states[10],[0,1,0,1,0,0]);self.assertTrue(p['knapsack_6bit'].encoded_feasible[10])

    def test_track_b_input_hashes(self):
        expected={'maxcut_4bit_model.json':'6d6b2f5f23cb92d7960eb89b3026e63e110b5fddbf25ab7cd13c4a696bdc8d01',
                  'maxcut_4bit_classical.json':'24d35147ab696875ed43fd82ec625a4681da5320b3987085f049097b4bcadaf1',
                  'knapsack_6bit_model.json':'2134dce6d3689b2443022eac9a3db7d94f5a94fb5ab0d33a21b9f62feebcb79e',
                  'knapsack_6bit_classical.json':'80d16a9c2d11fb49aaa4fc8c6301b39f3b4b624d6c46eeb8ab1b257130104e9a'}
        for name,sha in expected.items():self.assertEqual(hashlib.sha256((ROOT/'inputs'/'track_b'/name).read_bytes()).hexdigest(),sha)

    def test_qaoa_gate_decomposition(self):
        for problem in load_problems(ROOT/'inputs'/'track_b').values():
            for p in (1,2):
                theta=np.arange(2*p)/7+.31;v=problem.qaoa_state(theta,p);u=s.statevector(problem.n,problem.qaoa_gates(theta,p))
                self.assertAlmostEqual(abs(np.vdot(v,u))**2,1)

    def test_qaoa_independent_dense_exponential(self):
        for problem in load_problems(ROOT/'inputs'/'track_b').values():
            p=2;theta=np.array([.17,.23,.31,.47]);v=np.ones(1<<problem.n,dtype=complex)/np.sqrt(1<<problem.n)
            mixer=sum((dense_one(problem.n,q,s.X) for q in range(problem.n)),np.zeros((1<<problem.n,1<<problem.n),complex))
            for k in range(p):v=expm(-1j*theta[p+k]*mixer)@expm(-1j*theta[k]*np.diag(problem.energies))@v
            self.assertClose(v,problem.qaoa_state(theta,p))

    def test_shot_study_counts_and_metrics(self):
        problems=load_problems(ROOT/'inputs'/'track_b');p=problems['maxcut_4bit'];prob=np.ones(16)/16
        runs=[{'seed':0,'model':'maxcut_4bit','p':1,'probabilities':prob.tolist()}]
        rows=shot_study(problems,runs,repetitions=2);self.assertEqual(len(rows),8)
        for r in rows:
            self.assertEqual(sum(r['counts']),r['shots']);self.assertTrue(all(isinstance(k,int) and k>=0 for k in r['counts']))
            self.assertAlmostEqual(r['expected_energy'],np.array(r['counts'])@p.energies/r['shots'])

    def test_fresh_classical_baselines(self):
        rows=classical_baselines(load_problems(ROOT/'inputs'/'track_b'),repeats=2)['results']
        self.assertClose([r['minimum'] for r in rows],[-4,-6,np.linalg.eigvalsh(hamiltonian())[0]])
        self.assertTrue(all(len(r['timings_s'])==2 for r in rows))

    def test_qnn_loss_chain_rule(self):
        data=dataset(0);X=data['Xtrain'][:5];y=data['ytrain'][:5];theta=np.random.default_rng(10).normal(size=8)
        _,g=loss_and_gradient(theta,X,y);eps=1e-5
        def loss(a):
            p=.02+.96*(1-outputs(a,X))/2
            return np.mean(-y*np.log(p)-(1-y)*np.log(1-p))
        fd=[(loss(theta+eps*e)-loss(theta-eps*e))/(2*eps) for e in np.eye(8)]
        self.assertClose(g,fd,1e-8)
        self.assertGreater(np.linalg.norm(parameter_shift(loss,theta)-g),1e-3)

    def test_qnn_reproducible_dataset(self):
        a=dataset(2);b=dataset(2)
        for k in a:self.assertClose(a[k],b[k])
        self.assertClose(a['ytest'],(a['Xtest'][:,0]+.5*a['Xtest'][:,1]>0).astype(float))


if __name__=='__main__':unittest.main()
