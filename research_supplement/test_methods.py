import unittest
import numpy as np
from .curvature import logistic,grng_direction,regularized_kalman,minmax
from .submodular import DynamicLevels,private_distribution,generalized_noisy_max,dp_density_greedy_plus
from .quantum import states,output_jacobian,outputs,energy,energy_gradient,block_encoding
from .quantum_studies import tt_generate,tt_pullback


class MathematicalChecks(unittest.TestCase):
    def test_logistic_hessian_and_double_backprop(self):
        rng=np.random.default_rng(5);x=rng.normal(size=(12,4));y=rng.integers(0,2,12);w=rng.normal(size=4);_,g,h=logistic(w,x,y);eps=1e-5
        numeric=np.column_stack([(logistic(w+eps*np.eye(4)[j],x,y)[1]-logistic(w-eps*np.eye(4)[j],x,y)[1])/(2*eps) for j in range(4)])
        np.testing.assert_allclose(h,numeric,atol=1e-8)
        def reg(w):l,g,_=logistic(w,x,y);return l+.025*(g@g)
        numeric=np.array([(reg(w+eps*np.eye(4)[j])-reg(w-eps*np.eye(4)[j]))/(2*eps) for j in range(4)])
        np.testing.assert_allclose(g+.05*h@g,numeric,atol=1e-8)

    def test_kalman_covariance_is_positive(self):
        x=np.array([[1.,0],[1,1],[1,2],[1,3]]);mu,cov,trace=regularized_kalman(x,np.array([1,3,5,7.]))
        self.assertGreaterEqual(np.linalg.eigvalsh(cov).min(),-1e-12)
        self.assertLess(np.mean((x@mu-np.array([1,3,5,7]))**2),2.)

    def test_constant_minmax_convention(self):
        np.testing.assert_array_equal(minmax([3,3]),[1,1])

    def test_dynamic_insert_delete_invariants(self):
        weights=np.arange(36).reshape(6,6);weights=(weights+weights.T)/2
        f=lambda s:float(sum(weights[i,j] for i in s for j in set(range(6))-s))
        for seed in range(10):
            ds=DynamicLevels(f,2,2.,seed=seed)
            for i in range(6):ds.insert(i);ds.check_invariants()
            for i in [2,0,4]:ds.delete(i);ds.check_invariants();self.assertNotIn(i,ds.solution())
            for i in [4,2]:ds.insert(i);ds.check_invariants()

    def test_private_likelihood_ratio(self):
        c=[{0},{1},{0,1}];data=[{0},{1},{1}]
        _,_,p=private_distribution(data,c,[1,1,2],2,.7);_,_,q=private_distribution(data+[{0}],c,[1,1,2],2,.7)
        self.assertLessEqual(float(np.max(np.abs(np.log(p/q)))),.7+1e-12)

    def test_grnm_and_pure_composition(self):
        rng=np.random.default_rng(8);i,a=generalized_noisy_max([2.,1.,4.],[1.,.5,2.],1.,.1,rng)
        self.assertTrue(0<=i<3);self.assertTrue(np.isfinite(a).all())
        s,path,account=dp_density_greedy_plus(lambda s:float(len(s)),[1,2,1],2,1.,rng)
        self.assertLessEqual(sum([1,2,1][i] for i in s),2)
        self.assertLessEqual(account['total_pure_epsilon_upper_bound'],1.)

    def test_circuit_norms_and_parameter_shift(self):
        rng=np.random.default_rng(7);a=rng.normal(size=18);x=rng.normal(size=(3,3))
        np.testing.assert_allclose(np.sum(np.abs(states(a,x))**2,axis=1),1,atol=1e-12)
        _,jac,_=output_jacobian(a,x);eps=1e-5
        for k in [0,5,17]:
            p=a.copy();m=a.copy();p[k]+=eps;m[k]-=eps
            np.testing.assert_allclose(jac[...,k],(outputs(p,x)-outputs(m,x))/(2*eps),atol=1e-8)

    def test_tt_core_backprop(self):
        rng=np.random.default_rng(18);c=rng.normal(size=(3,2,2));z=rng.normal(size=8);g=rng.normal(size=6);analytic=tt_pullback(c,z,g);eps=1e-5
        numeric=np.zeros_like(c)
        for idx in np.ndindex(c.shape):
            p=c.copy();m=c.copy();p[idx]+=eps;m[idx]-=eps
            numeric[idx]=g@(tt_generate(p,z,6)-tt_generate(m,z,6))/(2*eps)
        np.testing.assert_allclose(analytic,numeric,atol=1e-8)

    def test_gradient_filter_ancilla(self):
        k=np.array([[.5,.2],[.2,.7]]);u=block_encoding(k);np.testing.assert_allclose(u.conj().T@u,np.eye(4),atol=1e-12)
        state=np.array([.6,.8]);out=u@np.r_[state,[0,0]]
        np.testing.assert_allclose(out[:2],k@state,atol=1e-12)

    def test_energy_gradient(self):
        a=np.random.default_rng(8).normal(size=9);g=energy_gradient(a);eps=1e-5
        for k in range(len(a)):
            p=a.copy();m=a.copy();p[k]+=eps;m[k]-=eps
            self.assertAlmostEqual(g[k],(energy(p)-energy(m))/(2*eps),places=7)


if __name__=='__main__':unittest.main()
