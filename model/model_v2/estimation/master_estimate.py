"""
execfile('master_estimate.py')

This file returns the structural parameters' estimates

This master file implements the Wald metric to estimate the structural
parameters

"""

from __future__ import division #omit for python 3.x
import numpy as np
import pandas as pd
import pickle
import itertools
import sys, os
from scipy import stats
#from scipy.optimize import minimize
from scipy.optimize import fmin_bfgs
from joblib import Parallel, delayed
from scipy import interpolate
import matplotlib.pyplot as plt
#sys.path.append("C:\\Users\\Jorge\\Dropbox\\Chicago\\Research\\Human capital and the household\]codes\\model")
sys.path.append("/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample")
import utility as util
import gridemax
import time
import int_linear
import emax as emax
import simdata as simdata
sys.path.append("/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/estimation")
import estimate as estimate

np.random.seed(1)

betas_nelder=np.load('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/betas_modelv2_nelder_v11.npy')


#Utility function
eta=betas_nelder[0]
alphap=betas_nelder[1]
alphaf=betas_nelder[2]

#wage process
wagep_betas=np.array([betas_nelder[3],betas_nelder[4],betas_nelder[5],
	betas_nelder[6],betas_nelder[7]]).reshape((5,1))

#Production function [young[cc0,cc1],old]
gamma1=[[betas_nelder[8],betas_nelder[10]],betas_nelder[12]]
gamma2=[[betas_nelder[9],betas_nelder[11]],betas_nelder[13]]
sigmatheta=0

#Measurement system: three measures for t=2, one for t=5
kappas=[[[betas_nelder[14],betas_nelder[15],betas_nelder[16],betas_nelder[17]]
,[betas_nelder[18],betas_nelder[19],betas_nelder[20],betas_nelder[21]],
[betas_nelder[22],betas_nelder[23],betas_nelder[24],betas_nelder[25]]],
[[betas_nelder[26],betas_nelder[27],betas_nelder[28],betas_nelder[29]]]]
#First measure is normalized. starting arbitrary values
lambdas=[[1,betas_nelder[30],betas_nelder[31]],[betas_nelder[32]]]


#Weibull distribution of cc prices
scalew=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/aux_model/scale.csv').values
shapew=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/aux_model/shape.csv').values
q=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/aux_model/q_prob.csv').values


#Probability of afdc takeup
pafdc=.60

#Probability of snap takeup
psnap=.70

#Data
#X_aux=pd.read_csv('C:\\Users\\Jorge\\Dropbox\\Chicago\\Research\\Human capital and the household\\results\\Model\\Xs.csv')
X_aux=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/Model/sample_model_v2.csv')
x_df=X_aux

#Sample size 
N=X_aux.shape[0]

#Data for wage process
#see wage_process.do to see the order of the variables.
x_w=x_df[ ['age_ra', 'd_HS2', 'constant' ] ].values


#Data for marriage process
#Parameters: marriage. Last one is the constant
x_m=x_df[ ['age_ra', 'constant']   ].values
marriagep_betas=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/marriage_process/betas_m_v2.csv').values

#Data for fertility process (only at X0)
#Parameters: kids. last one is the constant
x_k=x_df[ ['age_ra', 'age_ra2', 'constant']   ].values
kidsp_betas=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/kids_process/betas_kids_v2.csv').values


#Minimum set of x's (for interpolation)
x_wmk=x_df[  ['age_ra', 'age_ra2', 'd_HS2', 'age_t0','age_t02','constant'] ].values

#Data for treatment status
passign=x_df[ ['d_RA']   ].values

#The EITC parameters
eitc_list = pickle.load( open( '/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample/eitc_list.p', 'rb' ) )

#The AFDC parameters
afdc_list = pickle.load( open( '/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample/afdc_list.p', 'rb' ) )

#The SNAP parameters
snap_list = pickle.load( open( '/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample/snap_list.p', 'rb' ) )

#CPI index
cpi =  pickle.load( open( '/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample/cpi.p', 'rb' ) )

#Here: the estimates from the auxiliary model
###
###

#Assuming random start
theta0=np.exp(np.random.randn(N))

#number of kids at baseline
nkids0=x_df[ ['nkids_baseline']   ].values

#marital status at baseline
married0=x_df[ ['d_marital_2']   ].values

#age of child at baseline
agech0=x_df[['age_t0']].values

#Defines the instance with parameters
param0=util.Parameters(alphap, alphaf, eta, gamma1, gamma2,sigmatheta,
	wagep_betas, marriagep_betas, kidsp_betas, eitc_list,afdc_list,snap_list,
	cpi,q,scalew,shapew,lambdas,kappas,pafdc,psnap)



###Auxiliary estimates### 

moments_vector=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/aux_model/moments_vector.csv').values


#This is the var cov matrix of aux estimates
var_cov=pd.read_csv('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/aux_model/var_cov.csv').values

#The W matrix in Wald metric
#Using diagonal of Var-Cov matrix of simulated moments
w_matrix  = np.zeros((var_cov.shape[0],var_cov.shape[0]))
for i in range(var_cov.shape[0]):
	w_matrix[i,i] = var_cov[i,i]


#Creating a grid for the emax computation
dict_grid=gridemax.grid()

#For montercarlo integration
D=50

#For II procedure
M=1000

output_ins=estimate.Estimate(param0,x_w,x_m,x_k,x_wmk,passign,agech0,theta0,nkids0,
	married0,D,dict_grid,M,N,moments_vector,w_matrix)

start_time = time.time()
output=output_ins.optimizer()

time_opt=time.time() - start_time
print 'Done in'
print("--- %s seconds ---" % (time_opt))

def sym(a):
	return ((1/(1+np.exp(-a))) - 0.5)*2

#the list of estimated parameters
eta_opt=output.x[0]
alphap_opt=output.x[1]
alphaf_opt=output.x[2]
betaw0=output.x[3]
betaw1=output.x[4]
betaw2=output.x[5]
betaw3=output.x[6]
betaw4=np.exp(output.x[7])
gamma1_young_cc0=sym(output.x[8])
gamma2_young_cc0=sym(output.x[9])
gamma1_young_cc1=sym(output.x[10])
gamma2_young_cc1=sym(output.x[11])
gamma1_old=sym(output.x[12])
gamma2_old=sym(output.x[13])
kappas_000=output.x[14]
kappas_001=output.x[15]
kappas_002=output.x[16]
kappas_003=output.x[17]
kappas_010=output.x[18]
kappas_011=output.x[19]
kappas_012=output.x[20]
kappas_013=output.x[21]
kappas_020=output.x[22]
kappas_021=output.x[23]
kappas_022=output.x[24]
kappas_023=output.x[25]
kappas_100=output.x[26]
kappas_101=output.x[27]
kappas_102=output.x[28]
kappas_103=output.x[29]
lambdas_01=output.x[30]
lambdas_02=output.x[31]
lambdas_10=output.x[32]


betas_opt=np.array([eta_opt, alphap_opt,alphaf_opt,betaw0,betaw1,betaw2,
	betaw3,betaw4,gamma1_young_cc0,gamma2_young_cc0,gamma1_young_cc1,
	gamma2_young_cc1,gamma1_old,gamma2_old,
	kappas_000,kappas_001,kappas_002,kappas_003,
	kappas_010,kappas_011,kappas_012,kappas_013,
	kappas_020,kappas_021,kappas_022,kappas_023,
	kappas_100,kappas_101,kappas_102,kappas_103,
	lambdas_01,lambdas_02,lambdas_10])

np.save('/mnt/Research/nealresearch/new-hope-secure/newhopemount/results/betas_modelv2_nelder_v12.npy',betas_opt)




#this will not be necessary once running optimizer (this will go in optimizer(.))
#beta0=np.array([np.log(eta),alphap,alphaf,wagep_betas[0],wagep_betas[1],wagep_betas[2],
#	wagep_betas[3],np.log(wagep_betas[4]),gamma1[0][0],gamma2[0][0],
#	gamma1[0][1],gamma2[0][1],gamma1[1],gamma2[1]])

#dic_qw=output_ins.ll(beta0)


"""
##obtaining emax instance##
emax_instance=output_ins.emax(param0)
		
##obtaining samples##
choices=output_ins.samples(param0,emax_instance)



##Getting the betas of the auxiliary model##
dic_betas=output_ins.aux_model(choices)

beta_inputs_old=dic_betas['beta_inputs_old']
beta_inputs_old.shape


beta_kappas_t5=dic_betas['beta_kappas_t5']
beta_kappas_t5.shape
beta_lambdas_t5=dic_betas['beta_lambdas_t5']
beta_lambdas_t5.shape
beta_lambdas_t2=dic_betas['beta_lambdas_t2']
beta_lambdas_t2.shape
"""



