# Extracted unchanged from phels23/Q-FLAIR, commit 4f331783fc5bda5492fa3fffff0a845b0805eb39
# QNN/QNN_cost.py; original Apache-2.0 license is included alongside.
import numpy as np

def determine_sine_curve(f0,fp,fm):
	'''
	determine a,b, and c values for a cos(theta(xj-xi)-b)+c
	by solving equation for f0=k(theta0),fp=k(thetaPI/2), and fm=k(theta-PI/2)
	Rotosolve implementation adapted from
	[Pennylane](https://docs.pennylane.ai/en/stable/_modules/pennylane/optimize/rotosolve.html#RotosolveOptimizer)
	Args:
		f0: kernel for theta=0
		fp: kernel for theta=+pi/2
		fm: kernel for theta=-pi/2
	Returns:
		Solution for system of three cos equations.
	'''
	c = 0.5 * (fp + fm)
	b = np.arctan2(2 * (f0 - c), fp - fm)
	a = np.sqrt((f0 - c) ** 2 + 0.25 * (fp - fm) ** 2)
	b = -b + np.pi / 2
	return a, b, c

def eq_sin(theta,a,b,c):
	'''
	Cosinus function with free parameters
	Args:
		theta: angle
		a: amplitude
		b: shift
		c: offset
	Returns:
		Solution of Cosinus function.
	'''
	return a*np.cos(theta-b)+c
