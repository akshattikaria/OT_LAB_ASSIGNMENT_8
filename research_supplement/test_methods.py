import unittest
import numpy as np
from .curvature import logistic,grng_direction,regularized_kalman,minmax
from .submodular import DynamicLevels,private_distribution,generalized_noisy_max,dp_density_greedy_plus,exact_dp_distribution
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
        np.testing.assert_array_equal(minmax([3,3]),[0,0])

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

    def test_complete_private_algorithm_distribution(self):
        cover=[{0},{1},{0,1}];data=[{0},{1},{1}]
        def objective(dataset):return lambda s:float(sum(bool(set(row)&set().union(*(cover[i] for i in s))) for row in dataset))
        p=exact_dp_distribution(objective(data),[1,2,1],2,.8);q=exact_dp_distribution(objective(data+[{0}]),[1,2,1],2,.8)
        self.assertEqual(set(p),set(q));self.assertLessEqual(max(abs(np.log(p[s]/q[s])) for s in p),.8+1e-10)

    def test_subspace_parameter_gradients_and_trajectory(self):
        from .communication import subspace_step
        rng=np.random.default_rng(95);e=rng.normal(size=(3,6));target=rng.normal(size=(3,6));u=np.linalg.qr(rng.normal(size=(6,2)))[0];params=[rng.normal(scale=.1,size=s) for s in [(6,3),(3,2),(6,3),(3,2)]]
        value,g,_=subspace_step(params,e,target,u,False);value_c,gc,_=subspace_step(params,e,target,u,True)
        self.assertAlmostEqual(value,value_c,places=12)
        for a,b in zip(g,gc):np.testing.assert_allclose(a,b,atol=1e-12)
        eps=1e-5
        for k,idx in [(0,(1,2)),(1,(1,1)),(2,(4,1)),(3,(0,1))]:
            p=[a.copy() for a in params];m=[a.copy() for a in params];p[k][idx]+=eps;m[k][idx]-=eps
            numeric=(subspace_step(p,e,target,u)[0]-subspace_step(m,e,target,u)[0])/(2*eps)
            self.assertAlmostEqual(g[k][idx],numeric,places=7)

    def test_implicit_hypergradient(self):
        from .hpo import hypergradient,ridge_solution
        rng=np.random.default_rng(92);x=rng.normal(size=(10,4));y=rng.normal(size=10);v=rng.normal(size=(8,4));vy=rng.normal(size=8);ell=-.8;eps=1e-5
        loss=lambda a:np.mean((v@ridge_solution(x,y,a)[0]-vy)**2)/2
        self.assertAlmostEqual(hypergradient(x,y,v,vy,ell),(loss(ell+eps)-loss(ell-eps))/(2*eps),places=7)

    def test_norm_oracle_duality_certificates(self):
        from .hpo import lmo
        g=np.array([1.,-3.,2.])
        for norm,dual in [('l1',3.),('l2',np.linalg.norm(g)),('linf',6.)]:self.assertAlmostEqual(float(g@lmo(g,norm)),-dual,places=12)
        a=np.arange(12.).reshape(4,3);d=lmo(a,'spectral');self.assertLessEqual(np.linalg.norm(d,2),1+1e-12);self.assertAlmostEqual(float(np.sum(a*d)),-np.linalg.svd(a,compute_uv=False).sum(),places=10)

    def test_pipeline_hand_trace(self):
        from .strategies import pipeline_time
        elapsed,forward,backward=pipeline_time([2.,1.],[4.,2.],[.5],2)
        self.assertEqual(elapsed,16.);np.testing.assert_allclose(forward,[[2,3.5],[4,5.5]])

    def test_mcl_known_partition(self):
        from .placement import mcl
        a=np.array([[2.,2,0,0],[2,2,0,0],[0,0,2,2],[0,0,2,2]])
        groups,p=mcl(a);self.assertEqual({tuple(g) for g in groups},{(0,1),(2,3)});np.testing.assert_allclose(p.sum(0),1,atol=1e-12)

    def test_svmplus_primal_dual_and_inference(self):
        from .svmplus import fit,predict
        x=np.array([[-2.,0],[-1,1],[-.7,0],[.8,0],[1,1],[2,0]]);y=np.array([-1,-1,-1,1,1,1]);p=x[:,:1]
        model=fit(x,y,p,[1.,1.,1.,1.]);self.assertTrue(model['valid']);self.assertLess(model['gap'],.001);self.assertLess(model['feasibility_error'],1e-6);self.assertTrue(np.all(predict(model,x)==y))

    def test_liver_focal_and_classical_backprop(self):
        from .liver import initialize,forward,focal,gradients
        rng=np.random.default_rng(98);p=initialize(rng,3);p['bottleneck'][6:8]=1;x=rng.normal(size=(3,3));y=np.array([0,1,1]);weights=np.ones(2)
        logits,cache=forward(p,x,'matched_classical',jacobians=True);loss,d=focal(logits,y,weights);g=gradients(p,cache,d);eps=1e-5
        for key,idx in [('w1',(1,1)),('w3',(20,1)),('bottleneck',(2,)),('wo',(0,)),('bo',())]:
            plus={k:v.copy() for k,v in p.items()};minus={k:v.copy() for k,v in p.items()};plus[key][idx]+=eps;minus[key][idx]-=eps
            lp=focal(forward(plus,x,'matched_classical')[0],y,weights)[0];lm=focal(forward(minus,x,'matched_classical')[0],y,weights)[0]
            self.assertAlmostEqual(float(g[key][idx]),(lp-lm)/(2*eps),places=6)

    def test_quantum_input_jacobian(self):
        rng=np.random.default_rng(102);theta=rng.normal(size=8);x=rng.normal(size=(4,2));_,_,jac=output_jacobian(theta,x,n=2,axes='x',encoding='x',with_features=True);eps=1e-5
        for k in range(2):
            plus=x.copy();minus=x.copy();plus[:,k]+=eps;minus[:,k]-=eps
            np.testing.assert_allclose(jac[...,k],(outputs(theta,plus,n=2,axes='x',encoding='x')-outputs(theta,minus,n=2,axes='x',encoding='x'))/(2*eps),atol=1e-8)

    def test_preprocessing_has_no_test_leakage(self):
        from .liver import prepare
        x=np.array([[1.,2],[3,4],[100,np.nan],[90,500]]);_,a=prepare(x,[0,1],[2],[3]);x[3]=[-5000,-6000];_,b=prepare(x,[0,1],[2],[3])
        for key in a:np.testing.assert_array_equal(a[key],b[key])


if __name__=='__main__':unittest.main()
