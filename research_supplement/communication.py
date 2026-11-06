"""Constrained subspace training and executable low-rank FL controls."""
import numpy as np


def subspace_step(params,e,target,u,compressed=False):
    v1,a1,v2,a2=params
    h1=np.tanh(e@v1);x1=e+h1@a1@u.T
    wire=(x1-e)@u
    received=e+wire@u.T if compressed else x1
    h2=np.tanh(received@v2);x2=received+h2@a2@u.T
    error=x2-target;loss=float(np.sum(error*error)/(2*len(e)));gx2=error/len(e)
    ga2=h2.T@gx2@u;gh2=(gx2@u@a2.T)*(1-h2*h2);gv2=received.T@gh2
    gx1=gx2+gh2@v2.T;sent_gradient=gx1@u
    reconstructed_gradient=sent_gradient@u.T if compressed else gx1
    ga1=h1.T@reconstructed_gradient@u;gh1=(reconstructed_gradient@u@a1.T)*(1-h1*h1);gv1=e.T@gh1
    return loss,[gv1,ga1,gv2,ga2],{'activation_error':float(np.linalg.norm(received-x1)),'raw_gradient_projection_error':float(np.linalg.norm(gx1-sent_gradient@u.T))}


def grassmann_step(u,gradients,rate):
    euclidean=-2*gradients.T@gradients@u
    tangent=euclidean-u@(u.T@euclidean)
    return np.linalg.qr(u-rate*tangent)[0]


def subspace_study():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(4000+seed);e=rng.normal(size=(16,32));u=np.linalg.qr(rng.normal(size=(32,4)))[0]
        target=e+rng.normal(size=(16,4))@u.T
        initial=[rng.normal(scale=.1,size=shape) for shape in [(32,8),(8,4),(32,8),(8,4)]]
        trajectories=[];final=[];maximum_activation_error=maximum_gradient_error=0.;raw_projection_error=0.
        for compressed in [False,True]:
            p=[v.copy() for v in initial];trace=[]
            for step in range(100):
                loss,g,diagnostic=subspace_step(p,e,target,u,compressed);trace.append(loss)
                p=[v-.03*gradient for v,gradient in zip(p,g)]
                maximum_activation_error=max(maximum_activation_error,diagnostic['activation_error'])
                raw_projection_error=max(raw_projection_error,diagnostic['raw_gradient_projection_error'])
            trajectories.append(trace);final.append(p)
        parameter_error=max(float(np.linalg.norm(a-b)) for a,b in zip(*final))
        gradients=rng.normal(size=(20,32));unew=grassmann_step(u,gradients,.001)
        old_error=np.linalg.norm(gradients-gradients@u@u.T)**2;new_error=np.linalg.norm(gradients-gradients@unew@unew.T)**2
        rows.append({'seed':seed,'rank':4,'width':32,'dense_loss_trace':trajectories[0],'compressed_loss_trace':trajectories[1],'max_trajectory_difference':float(np.max(np.abs(np.array(trajectories[0])-trajectories[1]))),'final_parameter_difference':parameter_error,'max_activation_reconstruction_error':maximum_activation_error,'raw_gradient_projection_error':raw_projection_error,'dense_boundary_payload_bytes':2*16*32*8,'compressed_boundary_payload_bytes':2*16*4*8,'one_time_shared_basis_bytes':32*4*8,'grassmann_orthogonality_error':float(np.linalg.norm(unew.T@unew-np.eye(4))),'grassmann_residual_before':float(old_error),'grassmann_residual_after':float(new_error)})
    return rows


def low_rank_fl():
    rows=[]
    for seed in range(5):
        rng=np.random.default_rng(4500+seed);targets=rng.normal(size=(4,12,8));optimum=targets.mean(0);start=rng.normal(size=(12,8))
        for method in ['dense','projection_no_feedback','projection_feedback','projection_feedback_refresh']:
            w=start.copy();residual=np.zeros_like(targets);previous=np.zeros_like(w);trace=[];rng=np.random.default_rng(4600+seed);p=np.linalg.qr(rng.normal(size=(12,3)))[0]
            for step in range(100):
                g=w[None,:,:]-targets
                if method=='dense':aggregate=g.mean(0);conservation=0.
                else:
                    if step>0:
                        # This server-derived SVD policy and optional random
                        # refresh are original explicit controls. The full
                        # OFLight construction was not accessible/verified;
                        # this is not an asserted OFLight implementation.
                        if method.endswith('refresh') and step%5==0:p=np.linalg.qr(rng.normal(size=(12,3)))[0]
                        else:p=np.linalg.svd(previous,full_matrices=False)[0][:,:3]
                    corrected=g+residual if 'feedback' in method and 'no_feedback' not in method else g
                    encoded=np.einsum('dr,kdn->krn',p,corrected)
                    reconstructed=np.einsum('dr,krn->kdn',p,encoded)
                    if 'feedback' in method and 'no_feedback' not in method:
                        residual=corrected-reconstructed;conservation=float(np.linalg.norm(corrected-reconstructed-residual))
                    else:conservation=0.
                    # Ideal superposition, normalized by four clients; no
                    # radio channel or physical network traffic is measured.
                    aggregate=p@encoded.mean(0);previous=aggregate.copy()
                w-=.2*aggregate
                trace.append({'round':step,'distance_to_exact_mean':float(np.linalg.norm(w-optimum)),'global_objective':float(np.mean(np.sum((w[None]-targets)**2,axis=(1,2)))/2),'feedback_conservation_error':conservation})
            rows.append({'seed':seed,'method':method,'final_distance':float(np.linalg.norm(w-optimum)),'logical_uplink_bytes_per_client_round':12*8*8 if method=='dense' else 3*8*8,'basis_downlink_bytes_per_round':0 if method=='dense' else 12*3*8,'model_downlink_bytes_per_round':12*8*8,'trace':trace})
    return rows


def run():
    return {'subspace':subspace_study(),'low_rank_fl':low_rank_fl(),'scope':'Subspace Networks Eq. 7–11 on a two-block residual network with frozen high-rank embeddings, fixed shared subspace and an independently checked Grassmann update. Dense vs compressed constrained-model trajectories are compared; arbitrary dense activation gradients are NOT claimed to reconstruct exactly. Low-rank FL implements server projection, ideal OTA sum and error feedback as OFLight-related controls. Its SVD/refresh policies are our explicit choices because the full OFLight algorithm was unavailable; no full-paper fidelity or RF/throughput claim.'}
