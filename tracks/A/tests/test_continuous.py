import unittest
import numpy as np

from contopt.checks import audit_run,finite_gradient,finite_hessian,relative_error
from contopt.optimizers import FIRST_ORDER,FirstOrder,train
from contopt.problems import ExpFit,Logistic,MLP,Ridge,make_dataset
from contopt.supplement import conjugate_gradient,curvature_experiment,foundations,landscapes,nonlinear_fit,smooth_convex_value


class Updates(unittest.TestCase):
    def scalar(self,method,w,lr,steps=1):
        state=FirstOrder(method,lr,1);q=np.array([float(w)])
        for _ in range(steps):q=state.step(q,lambda x:2*x)
        return q[0]
    def test_gradient_descent(self):self.assertAlmostEqual(self.scalar("GD",5,.1,2),3.2)
    def test_momentum(self):self.assertAlmostEqual(self.scalar("Momentum",5,.1,2),2.3)
    def test_nesterov(self):self.assertAlmostEqual(self.scalar("NAG",5,.1,2),2.48)
    def test_adagrad(self):self.assertAlmostEqual(self.scalar("AdaGrad",3,1,2),2-4/np.sqrt(52),places=7)
    def test_rmsprop(self):self.assertAlmostEqual(self.scalar("RMSProp",3,.1),3-.6/np.sqrt(3.6),places=7)
    def test_adam_bias_correction(self):self.assertAlmostEqual(self.scalar("Adam",3,.1),2.9,places=7)
    def test_sgd_matches_gd_on_one_sample(self):self.assertEqual(self.scalar("SGD",3,.1),self.scalar("GD",3,.1))
    def test_invalid_learning_rate(self):
        for lr in (0,-.1,float("nan")):
            with self.assertRaises(ValueError):FirstOrder("GD",lr,2)


class Derivatives(unittest.TestCase):
    def test_ridge_gradient_hessian(self):
        p,w,_,_=make_dataset("ridge",1)
        self.assertLess(relative_error(p.grad(w),finite_gradient(p.value,w)),1e-7)
        self.assertLess(relative_error(p.hess(w),finite_hessian(p.grad,w)),1e-7)
    def test_backprop_all_parameters_full_and_batch(self):
        p,w,_,_=make_dataset("mlp",1)
        for indices in (None,np.array([0,2,5,9])):
            self.assertLess(relative_error(p.grad(w,indices),finite_gradient(lambda q:p.value(q,indices),w)),1e-7)
    def test_regularized_gn_matches_exact_ridge_hessian(self):
        p,w,_,_=make_dataset("ridge",3);r,J=p.residual_jac(w)
        np.testing.assert_allclose(J.T@J,p.hess(w),atol=1e-12)
        np.testing.assert_allclose(J.T@r,p.grad(w),atol=1e-12)
    def test_exponential_derivatives(self):
        x=np.linspace(0,1,30);p=ExpFit(x,2*np.exp(.7*x));w=np.array([1.,-.2])
        self.assertLess(relative_error(p.grad(w),finite_gradient(p.value,w)),1e-7)
        self.assertLess(relative_error(p.hess(w),finite_hessian(p.grad,w)),1e-7)
    def test_logistic_curvature(self):
        rng=np.random.default_rng(12);p=Logistic(rng.normal(size=(50,4)),rng.integers(0,2,50));w=rng.normal(size=4);v=rng.normal(size=4)
        self.assertLess(relative_error(p.hess(w),finite_hessian(p.grad,w)),1e-7)
        np.testing.assert_allclose(p.hvp(w,v),p.hess(w)@v,atol=1e-12)
        np.testing.assert_allclose(p.fisher(w),p.hess(w)-p.l2*np.eye(p.d),atol=1e-12)
    def test_stable_large_logits(self):
        p=MLP([[1,1],[-1,-1]],[1,0]);w=np.ones(p.d)*1000
        self.assertTrue(np.isfinite(p.value(w)));self.assertTrue(np.all(np.isfinite(p.grad(w))))


class Training(unittest.TestCase):
    def test_newton_and_gn_reach_known_ridge_optimum(self):
        for seed in range(10):
            p,w,_,_=make_dataset("ridge",seed)
            for method in ("Newton","GaussNewton"):
                r=train(p,w,method,epochs=4)
                self.assertEqual(r["status"],"stationary")
                self.assertAlmostEqual(r["final_objective"],p.value(p.reference()),places=10)
                self.assertTrue(audit_run(p,r)["valid"])
    def test_equal_epoch_gradient_example_budget(self):
        p,w,_,_=make_dataset("ridge",5,n=35)
        for m in FIRST_ORDER:
            r=train(p,w,m,.001,epochs=2,batch_size=8)
            self.assertEqual(r["counts"]["gradient_examples"],70,m)
    def test_minibatch_average_is_full_gradient(self):
        p,w,_,_=make_dataset("mlp",10,n=40)
        avg=np.mean([p.grad(w,np.array([i])) for i in range(p.n)],axis=0)
        np.testing.assert_allclose(avg,p.grad(w),atol=1e-12)
    def test_gd_and_mini_identical_with_full_batch(self):
        p,w,_,_=make_dataset("ridge",2,n=30)
        a=train(p,w,"GD",.01,epochs=3);b=train(p,w,"MiniBatchSGD",.01,epochs=3,batch_size=30)
        np.testing.assert_allclose(a["theta"],b["theta"],atol=1e-12)
    def test_seeded_training_reproducibility(self):
        p,w,_,_=make_dataset("mlp",4,n=40)
        a=train(p,w,"Adam",.01,epochs=3,seed=12);b=train(p,w,"Adam",.01,epochs=3,seed=12)
        self.assertEqual(a["theta"],b["theta"])
    def test_audit_rejects_false_objective(self):
        p,w,_,_=make_dataset("ridge",2);r=train(p,w,"GD",.01,epochs=2)
        r["final_objective"]+=1;self.assertFalse(audit_run(p,r)["valid"])
    def test_divergence_is_recorded(self):
        p,w,_,_=make_dataset("ridge",2);r=train(p,w,"GD",100,epochs=30)
        self.assertEqual(r["status"],"diverged")
        self.assertTrue(np.isfinite(r["final_objective"]))
    def test_invalid_initial_and_budget(self):
        p,w,_,_=make_dataset("ridge",2)
        with self.assertRaises(ValueError):train(p,np.zeros(3),"GD")
        with self.assertRaises(ValueError):train(p,w,"GD",epochs=0)
    def test_invalid_data(self):
        with self.assertRaises(ValueError):Ridge([[float("nan")]], [1])
        with self.assertRaises(ValueError):Ridge([[1]], [1],-1)


class Controls(unittest.TestCase):
    def test_small_positive_convex_loss_is_not_cancelled(self):
        value=smooth_convex_value(1e-10)
        self.assertGreater(value,0)
        self.assertAlmostEqual(value/5e-21,1.0,places=12)

    def test_bounds_and_saddles(self):
        r=landscapes();self.assertTrue(r["bounds_verified"])
        self.assertAlmostEqual(r["saddle"][0]["trace"][-1]["objective"],1,places=8)
        self.assertLess(r["saddle"][1]["trace"][-1]["objective"],1e-8)
        self.assertLess(r["double_well"][0]["global_gap"],1e-10)
        self.assertGreater(r["double_well"][1]["global_gap"],.1)
    def test_gd_learning_rate_limits(self):
        r=landscapes()["learning_rate"]
        self.assertAlmostEqual(r[1]["trace"][1]["x"],3)
        self.assertAlmostEqual(r[2]["trace"][-1]["objective"],9)
        self.assertGreater(r[3]["trace"][-1]["objective"],9)
    def test_conjugate_gradient(self):
        H=np.array([[4.,1.],[1.,2.]]);b=np.array([2.,1.]);x,n,residual=conjugate_gradient(lambda v:H@v,b)
        np.testing.assert_allclose(x,np.linalg.solve(H,b),atol=1e-10);self.assertLess(residual,1e-10)
    def test_fisher_and_hvp(self):
        c=curvature_experiment()["checks"]
        self.assertLess(c["hvp_dense_error"],1e-12);self.assertLess(c["hvp_fd_error"],1e-7)
        self.assertLess(c["expected_fisher_hessian_error"],1e-12)
        self.assertGreater(c["empirical_expected_fisher_difference"],1e-3)
    def test_nonlinear_gn_reference(self):
        r=nonlinear_fit();self.assertTrue(r["reference"]["success"])
        for run in r["runs"]:self.assertAlmostEqual(run["final_objective"],r["reference"]["objective"],places=7)
    def test_corrected_slide_derivative(self):
        c=foundations()["slide_10_check"]
        self.assertEqual(c["gradient_at_zero"],-3);self.assertAlmostEqual(c["GD_step_lr_0_1"],.3)
        self.assertAlmostEqual(c["reference_weight"],1.2)


if __name__=="__main__":unittest.main(verbosity=2)
