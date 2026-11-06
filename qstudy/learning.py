"""Same split, transformed features, C and SVC learner; two different kernels."""
import time
import numpy as np
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector
from sklearn.datasets import make_moons,make_circles
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import rbf_kernel
from sklearn.svm import SVC


def feature_map(x):
    if np.asarray(x).shape!=(2,) or not np.all(np.isfinite(x)):raise ValueError('Two finite features required')
    qc=QuantumCircuit(2,name='feature map')
    for _ in range(2):
        qc.h([0,1]);qc.rz(2*float(x[0]),0);qc.rz(2*float(x[1]),1);qc.cx(0,1);qc.rz(2*(np.pi-x[0])*(np.pi-x[1]),1);qc.cx(0,1)
    return qc


def analytic_feature_state(x):
    """Independent four-amplitude formula, used for tests/audit only."""
    h=np.array([[1,1],[1,-1]])/np.sqrt(2);hh=np.kron(h,h);z0=np.array([1,-1,1,-1]);z1=np.array([1,1,-1,-1])
    phase=np.exp(-1j*(x[0]*z0+x[1]*z1+(np.pi-x[0])*(np.pi-x[1])*z0*z1));state=np.array([1,0,0,0],complex)
    for _ in range(2):state=phase*(hh@state)
    return state


def dataset(family,seed,train_size=60,test_size=60):
    if family not in ('moons','circles') or min(train_size,test_size)<4:raise ValueError('Invalid dataset')
    count=train_size+test_size
    x,y=make_moons(n_samples=count,noise=.15,random_state=seed) if family=='moons' else make_circles(n_samples=count,noise=.08,factor=.45,random_state=seed)
    ix_train,ix_test=train_test_split(np.arange(count),train_size=train_size,test_size=test_size,random_state=seed+100,stratify=y)
    scaler=StandardScaler().fit(x[ix_train]);transform=lambda a:np.pi/2*np.tanh(scaler.transform(a))
    return {'x_raw':x,'y_raw':y,'train_indices':ix_train,'test_indices':ix_test,'x_train':transform(x[ix_train]),'x_test':transform(x[ix_test]),'y_train':y[ix_train],'y_test':y[ix_test],'mean':scaler.mean_,'scale':scaler.scale_}


def quantum_grams(x_train,x_test):
    n=len(x_train);m=len(x_test);train=np.eye(n);test=np.empty((m,n));encoders=[feature_map(x) for x in np.r_[x_train,x_test]];inverses=[c.inverse() for c in encoders[:n]];calls=0;start=time.perf_counter()
    def overlap(i,j):
        nonlocal calls
        circuit=encoders[i].compose(inverses[j]);calls+=1
        return float(np.clip(abs(Statevector.from_instruction(circuit).data[0])**2,0,1))
    for i in range(n):
        for j in range(i):train[i,j]=train[j,i]=overlap(i,j)
    train_s=time.perf_counter()-start;start=time.perf_counter()
    for i in range(m):
        for j in range(n):test[i,j]=overlap(n+i,j)
    test_s=time.perf_counter()-start
    return train,test,{'training_kernel_s':train_s,'test_kernel_s':test_s,'overlap_circuit_evaluations':calls,'train_overlap_circuits':n*(n-1)//2,'test_overlap_circuits':n*m,'feature_definitions':n+m,'encoding_block_applications':2*calls,'trainable_circuit_parameters':0}


def fit_pair(data):
    x=data['x_train'];xt=data['x_test'];y=data['y_train'];yt=data['y_test'];records=[];saved={};models={}
    for name in ('quantum','rbf'):
        if name=='quantum':ktrain,ktest,counters=quantum_grams(x,xt)
        else:
            gamma=1/(x.shape[1]*x.var());start=time.perf_counter();ktrain=rbf_kernel(x,x,gamma=gamma);train_s=time.perf_counter()-start;start=time.perf_counter();ktest=rbf_kernel(xt,x,gamma=gamma);test_s=time.perf_counter()-start
            counters={'training_kernel_s':train_s,'test_kernel_s':test_s,'overlap_circuit_evaluations':0,'trainable_circuit_parameters':0,'gamma':float(gamma)}
        if np.linalg.eigvalsh(ktrain).min()<-1e-8:raise AssertionError('Ideal training kernel is not positive semidefinite')
        model=SVC(C=1.0,kernel='precomputed');start=time.perf_counter();model.fit(ktrain,y);fit_s=time.perf_counter()-start;start=time.perf_counter();prediction=model.predict(ktest);predict_s=time.perf_counter()-start
        records.append({'model':name,'accuracy':float(np.mean(prediction==yt)),'training_accuracy':float(np.mean(model.predict(ktrain)==y)),'svc_fit_s':fit_s,'predict_s':predict_s,
                        'training_total_s':counters['training_kernel_s']+fit_s,'inference_total_s':counters['test_kernel_s']+predict_s,'support_vectors':int(model.n_support_.sum()),'learned_classifier_scalars':int(model.dual_coef_.size+model.intercept_.size),**counters})
        saved[name+'_train']=ktrain;saved[name+'_test']=ktest;saved[name+'_prediction']=prediction;saved[name+'_support']=model.support_;saved[name+'_dual']=model.dual_coef_;saved[name+'_intercept']=model.intercept_;models[name]=model
    # Shot-only sensitivity of the ideal-trained quantum classifier, not noisy training.
    shot_records=[];rng=np.random.default_rng(991)
    for shots in (128,512,2048):
        count=rng.binomial(shots,np.clip(saved['quantum_test'],0,1));sampled=count/shots;prediction=models['quantum'].predict(sampled)
        saved[f'shot_{shots}_counts']=count;saved[f'shot_{shots}_prediction']=prediction
        shot_records.append({'shots_per_overlap':shots,'synthetic_binary_samples':int(count.size*shots),'accuracy':float(np.mean(prediction==yt)),'note':'Independent binomial shot model for test-kernel entries at fixed ideal-trained SVC; no calibrated device model or QPU training is implied.'})
    return records,saved,shot_records
