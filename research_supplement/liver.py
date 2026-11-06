"""CPU port of the authors' two-qubit hybrid architecture on public ILPD.

Architecture source: LauraMDonaire/QML-Liver, model_with_2_qubits.ipynb.
NumPy port; smaller epoch cap and validation-selected early stopping disclosed.
No diagnostic or clinical deployment claim.
"""
import csv
from pathlib import Path
import time
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score,balanced_accuracy_score,f1_score,roc_auc_score,confusion_matrix
from .common import Adam,sigmoid,array_digest
from .quantum import outputs,output_jacobian


def dataset():
    path=Path(__file__).parent/'data/ilpd.csv'
    with path.open() as stream:rows=list(csv.DictReader(stream))
    names=[n for n in rows[0] if n!='Sickness']
    x=np.array([[float(r[n]) if n!='Gender' and r[n] else (1. if r[n]=='Male' else 0.) if n=='Gender' else np.nan for n in names] for r in rows])
    y=np.array([int(r['Sickness'])==1 for r in rows],dtype=int)
    return x,y,names


def prepare(x,train,validation,test):
    medians=np.nanmedian(x[train],axis=0);filled=np.where(np.isnan(x),medians,x)
    mean=filled[train].mean(axis=0);scale=filled[train].std(axis=0);scale[scale==0]=1
    standardized=(filled-mean)/scale
    return standardized,{'training_medians':medians,'training_mean':mean,'training_scale':scale}


def focal(logit,y,class_weights):
    p=np.clip(sigmoid(logit),1e-9,1-1e-9);weight=class_weights[y.astype(int)]
    loss=-weight*(y*(1-p)*np.log(p)+(1-y)*p*np.log1p(-p))
    derivative=weight*np.where(y==1,p*(1-p)*np.log(p)-(1-p)**2,-p*(1-p)*np.log1p(-p)+p*p)
    return float(loss.mean()),derivative/len(y)


def initialize(rng,inputs):
    def glorot(a,b):return rng.uniform(-np.sqrt(6/(a+b)),np.sqrt(6/(a+b)),size=(a,b))
    return {'w1':glorot(inputs,256),'b1':np.zeros(256),'w2':glorot(256,128),'b2':np.zeros(128),'w3':glorot(128,2),'b3':np.zeros(2),'bottleneck':rng.normal(scale=.1,size=8),'wo':glorot(2,1).ravel(),'bo':np.array(0.)}


def classical_bottleneck(parameters,x):
    matrix=parameters[:4].reshape(2,2);bias=parameters[4:6];scale=parameters[6:8]
    a=np.tanh(x@matrix+bias);value=a*scale
    jac=np.zeros((len(x),2,8));xjac=np.zeros((len(x),2,2))
    for out in range(2):
        d=(1-a[:,out]**2)*scale[out]
        for inp in range(2):jac[:,out,inp*2+out]=d*x[:,inp];xjac[:,out,inp]=d*matrix[inp,out]
        jac[:,out,4+out]=d;jac[:,out,6+out]=a[:,out]
    return value,jac,xjac


def forward(p,x,method,rng=None,training=False,jacobians=False):
    z1=x@p['w1']+p['b1'];r1=np.maximum(0,z1);mask1=(rng.random(r1.shape)>.3)/.7 if training else np.ones_like(r1);a1=r1*mask1
    z2=a1@p['w2']+p['b2'];r2=np.maximum(0,z2);mask2=(rng.random(r2.shape)>.3)/.7 if training else np.ones_like(r2);a2=r2*mask2
    features=a2@p['w3']+p['b3']
    if method=='hybrid_quantum':
        if jacobians:q,jac,xjac=output_jacobian(p['bottleneck'],features,n=2,axes='x',encoding='x',with_features=True)
        else:q=outputs(p['bottleneck'],features,n=2,axes='x',encoding='x');jac=xjac=None
    else:q,jac,xjac=classical_bottleneck(p['bottleneck'],features)
    logit=q@p['wo']+p['bo']
    return logit,(x,z1,mask1,a1,z2,mask2,a2,q,jac,xjac)


def gradients(p,cache,derivative):
    x,z1,mask1,a1,z2,mask2,a2,q,jac,xjac=cache
    g={'wo':q.T@derivative,'bo':np.array(derivative.sum())}
    gq=derivative[:,None]*p['wo'];g['bottleneck']=np.einsum('bo,bop->p',gq,jac)
    df=np.einsum('bo,boq->bq',gq,xjac);g['w3']=a2.T@df;g['b3']=df.sum(0)
    dz2=(df@p['w3'].T)*mask2*(z2>0);g['w2']=a1.T@dz2;g['b2']=dz2.sum(0)
    dz1=(dz2@p['w2'].T)*mask1*(z1>0);g['w1']=x.T@dz1;g['b1']=dz1.sum(0)
    return g


def run():
    raw,y,names=dataset();runs=[]
    from sklearn.linear_model import LogisticRegression
    for seed in [31,41,51]:
        ids=np.arange(len(y));training,test=train_test_split(ids,test_size=.2,stratify=y,random_state=seed)
        train,validation=train_test_split(training,test_size=.2,stratify=y[training],random_state=seed)
        x,preprocessing=prepare(raw,train,validation,test);counts=np.bincount(y[train],minlength=2);weights=len(train)/(2*counts)
        init=initialize(np.random.default_rng(seed),x.shape[1]);init_classic=init['bottleneck'].copy();init_classic[:4]=np.eye(2).ravel();init_classic[4:6]=0;init_classic[6:8]=1
        for method in ['hybrid_quantum','matched_classical']:
            p={k:v.copy() for k,v in init.items()}
            if method=='matched_classical':p['bottleneck']=init_classic.copy()
            optimizers={k:Adam(v.shape,.001) for k,v in p.items()};rng=np.random.default_rng(seed+100);trace=[];best=None;bestloss=np.inf;stale=0;start=time.perf_counter();batch_calls=0
            for epoch in range(1,81):
                permutation=rng.permutation(train);losses=[]
                for i in range(0,len(train),32):
                    batch=permutation[i:i+32];logit,cache=forward(p,x[batch],method,rng,True,True);loss,derivative=focal(logit,y[batch],weights);losses.append(loss)
                    grads=gradients(p,cache,derivative)
                    for k in p:p[k]=optimizers[k].step(p[k],grads[k])
                    batch_calls+=1
                val_logits,_=forward(p,x[validation],method);val_loss,_=focal(val_logits,y[validation],weights)
                trace.append({'epoch':epoch,'training_batch_loss_mean':float(np.mean(losses)),'validation_focal_loss':val_loss})
                if val_loss<bestloss-1e-6:bestloss=val_loss;best={k:v.copy() for k,v in p.items()};stale=0;best_epoch=epoch
                else:stale+=1
                if stale>=10:break
            elapsed=time.perf_counter()-start;logits,_=forward(best,x[test],method);prob=sigmoid(logits);pred=(prob>=.5).astype(int)
            runs.append({'seed':seed,'method':method,'accuracy':accuracy_score(y[test],pred),'balanced_accuracy':balanced_accuracy_score(y[test],pred),'f1':f1_score(y[test],pred),'roc_auc':roc_auc_score(y[test],prob),'confusion_matrix':confusion_matrix(y[test],pred),'training_s':elapsed,'epochs':epoch,'best_epoch':best_epoch,'trainable_parameters':sum(v.size for v in p.values()),'circuit_parameter_count':8 if method=='hybrid_quantum' else 0,'batch_calls':batch_calls,'batched_statevector_calls':batch_calls*21 if method=='hybrid_quantum' else 0,'simulated_circuit_instances':(epoch*(len(train)*21+len(validation))+len(test)) if method=='hybrid_quantum' else 0,'test_probabilities':prob,'test_labels':y[test],'train_indices':train,'validation_indices':validation,'test_indices':test,'preprocessing':preprocessing,'trace':trace,'final_parameters':best})
        model=LogisticRegression(C=1,class_weight='balanced',max_iter=500).fit(x[train],y[train]);p=model.predict_proba(x[test])[:,1];pred=(p>=.5).astype(int)
        runs.append({'seed':seed,'method':'logistic_reference','accuracy':accuracy_score(y[test],pred),'balanced_accuracy':balanced_accuracy_score(y[test],pred),'f1':f1_score(y[test],pred),'roc_auc':roc_auc_score(y[test],p),'train_indices':train,'validation_indices':validation,'test_indices':test,'test_probabilities':p,'test_labels':y[test]})
    return {'runs':runs,'rows':len(raw),'feature_names':names,'class_counts':np.bincount(y),'data_digest':array_digest(raw,y),'scope':'Original NumPy port of authors Dense(256)-Dropout(.3)-Dense(128)-Dropout(.3)-Dense(2)-two-qubit/4 BasicEntangler layers-Dense(1) architecture, angle/RX embedding and Pauli-Z readout. Class-weighted gamma=1 focal loss; alpha unused as in the author TensorFlow default. New stratified train/validation/test splits, training-only imputation/scaling and 80-epoch cap with validation early stopping; no paper-score reproduction. Matched eight-parameter classical bottleneck shares encoder/output architecture, parameter count and training recipe, but has a different hypothesis class. Public ILPD benchmark only; no clinical validity claim.'}
