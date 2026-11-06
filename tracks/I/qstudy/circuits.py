"""Explicit little-endian circuits. No built-in algorithm constructors are used."""
from fractions import Fraction
import math
import numpy as np
from qiskit import QuantumCircuit
from qiskit.circuit.library import UnitaryGate
from qiskit.quantum_info import Statevector,SparsePauliOp

EDGES=((0,1),(1,2),(2,3),(3,0),(0,2))
HAM=SparsePauliOp.from_list([('ZI',.5),('IZ',-.4),('XX',.3),('ZZ',.2)])


def marginal(circuit,nbits):
    if not 1<=nbits<=circuit.num_qubits:raise ValueError('Invalid output register')
    probs=np.abs(Statevector.from_instruction(circuit).data)**2
    result=np.zeros(1<<nbits)
    for index,value in enumerate(probs):result[index%len(result)]+=value
    return result


def truth_oracle(table):
    n=int(math.log2(len(table)))
    if n<1 or 1<<n!=len(table) or any(x not in (0,1) for x in table):raise ValueError('Boolean truth table length must be 2^n')
    qc=QuantumCircuit(n+1,name='truth oracle')
    for value,bit in enumerate(table):
        if not bit:continue
        zero=[i for i in range(n) if not (value>>i)&1]
        for i in zero:qc.x(i)
        qc.mcx(list(range(n)),n)
        for i in zero:qc.x(i)
    return qc


def deutsch_jozsa(table):
    oracle=truth_oracle(table);n=oracle.num_qubits-1
    if sum(table) not in (0,len(table)//2,len(table)):raise ValueError('Deutsch-Jozsa promise violated')
    qc=QuantumCircuit(n+1,name='Deutsch-Jozsa');qc.x(n);qc.h(range(n+1));qc.compose(oracle,inplace=True);qc.h(range(n));return qc


def bernstein_vazirani(n,secret):
    if n<1 or not 0<=secret<1<<n:raise ValueError('Invalid hidden string')
    qc=QuantumCircuit(n+1,name='Bernstein-Vazirani');qc.x(n);qc.h(range(n+1))
    for i in range(n):
        if (secret>>i)&1:qc.cx(i,n)
    qc.h(range(n));return qc


def qft(n):
    if not 1<=n<=12:raise ValueError('Invalid Fourier size')
    qc=QuantumCircuit(n,name='QFT')
    for j in reversed(range(n)):
        qc.h(j)
        for k in reversed(range(j)):qc.cp(np.pi/(1<<(j-k)),j,k)
    for j in range(n//2):qc.swap(j,n-1-j)
    return qc


def phase_estimation(bits,phase):
    if not 1<=bits<=8 or not math.isfinite(phase):raise ValueError('Invalid phase estimation input')
    qc=QuantumCircuit(bits+1,name='QPE');qc.x(bits);qc.h(range(bits))
    for j in range(bits):qc.cp(2*np.pi*phase*(1<<j),j,bits)
    qc.compose(qft(bits).inverse(),range(bits),inplace=True);return qc


def phase_oracle(n,marked):
    if n<2 or not 0<=marked<1<<n:raise ValueError('Invalid Grover mark')
    qc=QuantumCircuit(n,name='phase oracle');zero=[i for i in range(n) if not (marked>>i)&1]
    for i in zero:qc.x(i)
    qc.h(n-1);qc.mcx(list(range(n-1)),n-1);qc.h(n-1)
    for i in zero:qc.x(i)
    return qc


def grover_rounds(n):return int(round(np.pi/(4*np.arcsin(2**(-n/2)))-.5))


def grover(n,marked,rounds=None):
    oracle=phase_oracle(n,marked);rounds=grover_rounds(n) if rounds is None else rounds
    if not isinstance(rounds,int) or rounds<0:raise ValueError('Invalid Grover rounds')
    qc=QuantumCircuit(n,name='Grover');qc.h(range(n))
    for _ in range(rounds):
        qc.compose(oracle,inplace=True);qc.h(range(n));qc.x(range(n));qc.h(n-1);qc.mcx(list(range(n-1)),n-1);qc.h(n-1);qc.x(range(n));qc.h(range(n))
    return qc


def modular_multiply(modulus,a):
    if modulus<3 or not 1<a<modulus or math.gcd(modulus,a)!=1:raise ValueError('Multiplier must be invertible modulo N')
    size=1<<math.ceil(math.log2(modulus));matrix=np.zeros((size,size),complex)
    for x in range(size):matrix[a*x%modulus if x<modulus else x,x]=1
    return matrix


def shor_order_circuit(modulus=15,a=2,bits=4):
    unitary=modular_multiply(modulus,a);width=int(math.log2(len(unitary)));qc=QuantumCircuit(bits+width,name='Shor order finding');qc.x(bits);qc.h(range(bits))
    for j in range(bits):qc.append(UnitaryGate(np.linalg.matrix_power(unitary,1<<j),label=f'M{a}^{1<<j}').control(1),[j]+list(range(bits,bits+width)))
    qc.compose(qft(bits).inverse(),range(bits),inplace=True);return qc


def factor_from_sample(measured,bits,modulus,a):
    if not 0<=measured<1<<bits:raise ValueError('Invalid phase sample')
    order=Fraction(measured,1<<bits).limit_denominator(modulus).denominator
    # Do not search denominators/multiples classically to manufacture success.
    if measured==0 or order%2 or pow(a,order,modulus)!=1:return {'candidate_order':order,'factors':[]}
    half=pow(a,order//2,modulus);factors=sorted({d for d in (math.gcd(half-1,modulus),math.gcd(half+1,modulus)) if 1<d<modulus})
    return {'candidate_order':order,'factors':factors}


def cut_values():return np.array([sum(((x>>i)&1)!=((x>>j)&1) for i,j in EDGES) for x in range(16)],float)


def qaoa(theta):
    if len(theta)%2 or not len(theta):raise ValueError('QAOA needs gamma and beta per layer')
    p=len(theta)//2;qc=QuantumCircuit(4,name='QAOA');qc.h(range(4))
    for gamma,beta in zip(theta[:p],theta[p:]):
        for i,j in EDGES:qc.rzz(float(gamma),i,j)
        for i in range(4):qc.rx(2*float(beta),i)
    return qc


def vqe(theta):
    if len(theta)!=4:raise ValueError('VQE ansatz has four angles')
    qc=QuantumCircuit(2,name='VQE');qc.ry(float(theta[0]),0);qc.ry(float(theta[1]),1);qc.cx(0,1);qc.ry(float(theta[2]),0);qc.ry(float(theta[3]),1);return qc


def vqe_energy(theta):return float(np.real(Statevector.from_instruction(vqe(theta)).expectation_value(HAM)))


def annealing(total_time,steps=128):
    if total_time<0 or steps<1:raise ValueError('Invalid annealing schedule')
    qc=QuantumCircuit(4,name='Trotter anneal');qc.h(range(4));dt=total_time/steps
    for k in range(steps):
        s=(k+.5)/steps
        for i in range(4):qc.rx(-2*dt*(1-s),i)
        for i,j in EDGES:qc.rzz(dt*s,i,j)
    return qc
