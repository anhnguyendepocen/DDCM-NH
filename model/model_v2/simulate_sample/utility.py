"""
Defines two classes: Parameters and Utility

-Parameters: defines a set of parameters

-Utility class: takes parameters, X's, and given choices and 
computes utility at a given point in time
It also computes next-period states: married, nkids, theta

pip2.7 install --user --upgrade panda

os.chdir("/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model")


"""
from __future__ import division #omit for python 3.x
import numpy as np
import pandas as pd
import sys, os
from scipy import stats

class Parameters:

	"""

	List of structural parameters and prices

	"""
	def __init__(self,alphap,alphaf,eta,gamma1,gamma2,
		sigmatheta,betaw,betam,betak,eitc,afdc,snap,cpi,q,scalew,shapew,
		lambdas,kappas,pafdc,psnap):

		self.alphap,self.alphaf,self.eta=alphap,alphaf,eta
		self.gamma1,self.gamma2=gamma1,gamma2
		self.sigmatheta,self.betaw,self.betam,self.betak=sigmatheta,betaw,betam,betak
		self.eitc,self.afdc,self.snap,self.cpi,self.q=eitc,afdc,snap,cpi,q
		self.scalew,self.shapew=scalew,shapew
		self.lambdas,self.kappas=lambdas,kappas
		self.pafdc,self.psnap=pafdc,psnap


class Utility:
	""" 
	
	This class defines the economic environment of the agent

	"""
	def __init__(self,param,N,xwage,xmarr,xkid,ra,theta0,
		nkids0,married0,hours,cc,age_t0):
		"""
		Set up model's data and paramaters

		theta0, nkids0, married0: ability, number of kids, and marital status
		at period t-1 (periodt-1). "periodt" represents choice at 
		periodt-1. 

	
		"""
		
		self.param=param
		self.N,self.xwage,self.xmarr=N,xwage,xmarr
		self.xkid,self.ra,self.theta0=xkid,np.reshape(ra,self.N),theta0
		self.nkids0,self.married0= nkids0,married0
		self.hours,self.cc,self.age_t0=hours,cc,age_t0



	def waget(self,periodt):
		"""
		Computes w (hourly wage) for periodt

		
		This method returns t=0,1...,8 
		(at t=0 we don't observe wages for those who do not work)
		(that's why I need to simulate w0 instead of just using observed one)

		lnw =beta1*age + beta1*age2 + beta3d_HS + constant+ e

		"""

		age_ra=self.xwage[:,0].copy()
		age=age_ra+periodt
		age2=age**2

		xw=np.concatenate((np.reshape(age,(self.N,1)),
					np.reshape(age2,(self.N,1)),
					np.reshape(self.xwage[:,1],(self.N,1)),
					np.reshape(self.xwage[:,2],(self.N,1))),axis=1)

		betas=self.param.betaw[0:-1,0]
		epsilon=np.sqrt(self.param.betaw[-1,0])*np.random.rand(self.N)
		return np.exp( np.dot(xw,betas)+epsilon )

	def q_prob(self):
		"""
		Draws a free child care slot from a binomial distribution
		"""
		return np.random.binomial(1,self.param.q,self.N)

	def price_cc(self):
		"""
		Draws a price offer for a child care slot
		"""
		return (np.random.weibull(self.param.shapew,(self.N,1)))*self.param.scalew

	def prob_afdc(self):
		"""
		Draws a vector of participation shocks of AFDC
		"""
		return np.random.binomial(1,self.param.pafdc,self.N)

	def prob_snap(self):
		"""
		Draws a vector of participation shocks of SNAP
		"""
		return np.random.binomial(1,self.param.psnap,self.N)



	def marriaget(self,periodt,marriedt_1):
		"""
		Computes probability of marriage at periodt (t) conditional on marital status
		at t-1

		marriage0 is given, so this method returns t=1,2,3...
		

		pr(married)=F(beta1*age + beta7*married_t-1 + beta_constant )

		
		"""

		age_ra=self.xmarr[:,0].copy()
		age=age_ra+(periodt-1) #age at t-1
		betas=self.param.betam[0:-1,0]
		epsilon=self.param.betam[-1,0]*np.random.rand(self.N)
		x_marr2=np.concatenate( (np.reshape(age,(self.N,1)),
			np.reshape(marriedt_1,(self.N,1)),
			np.ones((self.N,1))),axis=1 )
		
		phat=np.dot(x_marr2,betas) + epsilon
		phat[phat<0]=0
		phat[phat>1]=1

		return np.random.binomial(1,phat) #1 if stayed married at t+1

	def kidst(self,periodt,nkids,marriage):
		"""
		Computes whether the individual has a kid in periodt (t).
		For a given array of marriage (1,0) and number of kids

		kids0 is given, so this method returns t=1,2,3...

		age and age2 are taking from baseline

		marriage and nkids are vectors or shape N,1

		The equation:
		pr(having kid t)=F(beta1*age + beta2*age2 + beta3*nkids + beta4*marriage 
			 + beta_constant)

		"""
		age_ra=self.xkid[:,0].copy()
		age=age_ra+(periodt-1) #age at period t-1
		age2=age**2
		betas=self.param.betak[0:-1,0]
		epsilon=self.param.betak[-1,0]*np.random.rand(self.N)
		xkids2=np.concatenate((np.reshape(age,(self.N,1)),np.reshape(age2,(self.N,1)),
					nkids,marriage,np.ones((self.N,1))),axis=1)

		phat=np.dot(xkids2,betas) + epsilon
		phat[phat<0]=0
		phat[phat>1]=1
		dummy=np.random.binomial(1,phat)

		return  np.reshape(dummy,(self.N,1)) #1 if have a kid a t+1


	def dincomet(self, periodt,hours,wage,marr,kid):
		"""
		Computes annual disposable income given weekly hours worked, hourly wage,
		marital status and number of kids. 
		Everyone receives EITC. Only the treatment group has NH. NH ends between t=2 and t=3
		
		EITC parameters: in the self.eitc list

		6r1,r2: phase-in and phase-out rates
		b1,b2: minimum income for max credit/beginning income for phase-out
		state_eitc=fraction of federal eitc

		""" 
		
		#from hourly wage to annual earnings
		pwage=np.reshape(hours,self.N)*np.reshape(wage,self.N)*52

		#To nominal prices (2003 prices)
		pwage=pwage/(self.param.cpi[8]/self.param.cpi[periodt])

		#the EITC parameters
		dic_eitc=self.param.eitc[periodt]

		#The AFDC parameters
		afdc_param=self.param.afdc[0]

		#The SNAP parameters
		snap_param=self.param.snap[0]

		#family size
		nfam = np.ones(self.N) + kid[:,0] + marr[:,0]

		#1 children
		r1_1=dic_eitc['r1_1']
		r2_1=dic_eitc['r2_1']
		b1_1=dic_eitc['b1_1']
		b2_1=dic_eitc['b2_1']
		state_eitc1=dic_eitc['state_eitc1']

		#2+ children
		r1_2=dic_eitc['r1_2']
		r2_2=dic_eitc['r2_2']
		b1_2=dic_eitc['b1_2']
		b2_2=dic_eitc['b2_2']
		state_eitc2=dic_eitc['state_eitc2']

		#3 children
		state_eitc3=dic_eitc['state_eitc3']

		#Obtaining individual's disposable income from EITC
		eitc_fed=np.zeros(self.N)
		eitc_state=np.zeros(self.N)
		
		#one child
		kid_boo=kid[:,0]==1
		eitc_fed[(pwage<b1_1) & (kid_boo) ]=r1_1*pwage[(pwage<b1_1) & (kid_boo)]
		eitc_fed[(pwage>=b1_1) & (pwage<b2_1) & (kid_boo)]=r1_1*b1_1
		eitc_fed[(pwage>=b2_1) & (kid_boo)]=np.maximum(r1_1*b1_1-r2_1*(pwage[(pwage>=b2_1) & (kid_boo)]-b2_1),np.zeros(pwage[(pwage>=b2_1) & (kid_boo)].shape[0]))
		eitc_state[kid_boo]=state_eitc1*eitc_fed[kid_boo]

		#+2 children
		kid_boo=kid[:,0]>=2
		eitc_fed[(pwage<b1_2) & (kid_boo) ]=r1_2*pwage[(pwage<b1_2) & (kid_boo)]
		eitc_fed[(pwage>=b1_2) & (pwage<b2_2) & (kid_boo)]=r1_2*b1_2
		eitc_fed[(pwage>=b2_2) & (kid_boo)]=np.maximum(r1_2*b1_2-r2_2*(pwage[(pwage>=b2_2) & (kid_boo)]-b2_2),np.zeros(pwage[(pwage>=b2_2) & (kid_boo)].shape[0]))
		eitc_state[kid_boo]=state_eitc2*eitc_fed[kid_boo]
		
		#+3	children (only state EITC)
		kid_boo=kid[:,0]>=3
		eitc_state[kid_boo]=state_eitc3*eitc_fed[kid_boo]

		dincome_eitc=pwage+eitc_fed+eitc_state

		##Obtaining NH income supplement#

		if periodt<=2:

			#the wage subsidy
			wsubsidy=np.zeros(self.N)
			wsubsidy[pwage<=8500]=0.25*pwage[pwage<=8500]
			wsubsidy[pwage>8500]=3825-0.2*pwage[pwage>8500]
			wsubsidy[wsubsidy<0]=0

			#Child allowance
			

			#Fade-out level (3 possible periods)
			bar_e_extra=[300,1200,2100] #for a family of four children or more
			bar_e=np.zeros(self.N)
			bar_e[kid[:,0]<=4]=30000
			bar_e[kid[:,0]>4]=30000+bar_e_extra[periodt]

			#Maximum level of CA
			xstar=np.zeros(self.N)
			xstar[kid[:,0]<=4]=1700-kid[kid[:,0]<=4,0]*100
			xstar[kid[:,0]>4]=1300

			#r_e: phase-out rate
			beta_aux=xstar/(8500-bar_e)

			#per-child allowance
			childa=np.zeros(self.N) 
			childa[pwage<=8500]=xstar[pwage<=8500]
			childa[pwage>8500]=xstar[pwage>8500] - beta_aux[pwage>8500]*(pwage[pwage>8500] - 8500)
			childa[childa<0]=0

			#total child allowance
			total_childa=childa*kid[:,0]

			#disposable income
			dincome_nh=pwage+wsubsidy+total_childa
			supp=dincome_nh-dincome_eitc
			boo=(supp>=0) & (hours>=30)
			boo_ra=self.ra==1 
			nh_supp=(wsubsidy+total_childa)*boo*boo_ra
		else:
			nh_supp = 0 #NH ends
			#dincome=boo_ra*(boo*dincome_nh+(1-boo)*dincome_eitc) + \
			#(1-boo_ra)*dincome_eitc 

		#The AFDC (1995-1996. TANF implemented 1997, t=2)
		afdc_benefit = np.zeros(self.N)
		if periodt<=1:
			afdc_takeup=self.prob_afdc() #generates random afdc take-up
			cutoff = np.zeros(self.N)
			benefit_std = np.zeros(self.N)
			for nf in range(1,13):
				if nf<12:
					boo_k=nfam == nf
				else:
					boo_k=nfam >= nf
				cutoff[boo_k] = afdc_param['cutoff'][nf-1]
				benefit_std[boo_k] = afdc_param['benefit_std'][nf-1]

			boo_eli=(pwage<=cutoff) & (afdc_takeup==1)
			boo_min=benefit_std<=benefit_std-(pwage - 30)*.67
			afdc_benefit[boo_eli]=(1-boo_min[boo_eli])*(benefit_std[boo_eli]-(pwage[boo_eli] - 30)*.67) + boo_min[boo_eli]*benefit_std[boo_eli]
			afdc_benefit[afdc_benefit<0]=0
			#boo_max=afdc_benefit>0
			#dincome[boo_max]=dincome[boo_max] + afdc_benefit[boo_max]
		
		#SNAP benefits: vary by period/family size.
		std_deduction=np.zeros(self.N)
		net_i_test=np.zeros(self.N)
		gross_i_test=np.zeros(self.N)
		max_b=np.zeros(self.N)
		snap_takeup = self.prob_snap()
		for nf in range(1,15):
			if nf<=4:
				std_deduction[nfam==nf]=snap_param['std_deduction'][nf-1,periodt]
			elif nf==5:
				std_deduction[nfam==nf]=snap_param['std_deduction'][2,periodt]
			elif nf>=6:
				std_deduction[nfam==nf]=snap_param['std_deduction'][3,periodt]
			
			if nf<=8:
				net_i_test[nfam==nf]=snap_param['net_income_test'][nf-1,periodt]
				gross_i_test[nfam==nf]=snap_param['gross_income_test'][nf-1,periodt]
				max_b[nfam==nf]=snap_param['max_benefit'][nf-1,periodt]


			else:
				net_i_test[nfam==nf] = snap_param['net_income_test'][7,periodt] + snap_param['net_income_test'][8,periodt]*nfam[nfam==nf]

				gross_i_test[nfam==nf] = snap_param['gross_income_test'][7,periodt] + snap_param['gross_income_test'][8,periodt]*nfam[nfam==nf]

				max_b[nfam==nf] = snap_param['max_benefit'][7,periodt] + snap_param['max_benefit'][8,periodt]*nfam[nfam==nf]
			
		net_inc = pwage + afdc_benefit + nh_supp - std_deduction
		boo_net_eli = net_inc <= net_i_test
		boo_gro_eli = pwage <= gross_i_test
		boo_unemp=hours==0
		snap = snap_takeup*((max_b - 0.3*net_inc)*boo_net_eli*boo_gro_eli*(1-boo_unemp) + boo_unemp*(max_b - 0.3*net_inc))
		snap[snap<0]=0

		dincome = pwage + afdc_benefit + nh_supp + snap + eitc_fed + eitc_state

		#Back to real prices
		return dincome*(self.param.cpi[8]/self.param.cpi[periodt])

	def consumptiont(self,periodt,h,cc,dincome,marr,nkids,wage, free,price):
		"""
		Computes per-capita consumption:
		(income - cc_payment)/family size

		where cc_payment is determined using NH formula and price offer

		"""
		pwage=np.reshape(h,self.N)*np.reshape(wage,self.N)*52

		d_work=h>=3
		agech=np.reshape(self.age_t0,(self.N)) + periodt

		nkids=np.reshape(nkids,self.N)
		marr=np.reshape(marr,self.N)
		ones=np.ones(self.N)
		

		copayment=np.zeros(self.N)
		copayment[price[:,0]<400]=price[price[:,0]<400,0]
		copayment[(price[:,0]>400) & (pwage<=8500) ] = 400
		copayment[(price[:,0]>400) & (pwage>8500)] = 315 + 0.01*pwage[(price[:,0]>400) & (pwage>8500)] 


		#consumption pc (incorporate child care subsidy)
		if periodt<=2:#NH eligibility period
			cc_cost =  (ones-self.ra.reshape(self.N))*price[:,0]*(ones-free.reshape(self.N)) +\
			self.ra*( (ones-free.reshape(self.N))*(d_work*copayment + (1-d_work)*price[:,0] ) ) 
		else:
			cc_cost = price[:,0]*(ones-free.reshape(self.N))
		
		#old kids don't pay for child care
		cc_cost[agech>5]=0

		incomepc=(dincome - cc*cc_cost)/(ones+nkids+marr)
		incomepc[incomepc<=0]=1
		
		return incomepc



	def thetat(self,periodt,theta0,h,cc,dincome,marr,nkids,wage,free,price):
		"""
		Computes theta at period (t+1) (next period)
		t+1 goes from 1-8
		
		Inputs must come from period t

		"""
		#age of child
		agech=np.reshape(self.age_t0,(self.N)) + periodt

		#log consumption pc
		incomepc_aux=np.log(self.consumptiont(periodt,h,cc,dincome,marr,nkids,wage,free,price))
		incomepc=incomepc_aux-np.mean(incomepc_aux)
		
		#log leisure (T=148 hours a week)
		leisure=np.log(148-h) - np.mean(np.log(148-h))

		#random shock
		omega=self.param.sigmatheta*np.random.randn(self.N)
		
				
		#Parameters
		gamma1=self.param.gamma1
		gamma2=self.param.gamma2
		
		theta1=np.zeros(self.N)

		#The production of HC: young, cc=0
		boo=(agech<=5) & (cc==0)
		theta1[boo] = gamma1[0][0]*np.log(theta0[boo]) + gamma2[0][0]*incomepc[boo] +\
		(1 - gamma1[0][0] - gamma2[0][0] )*leisure[boo] + omega[boo]

		#The production of HC: young, cc=1
		boo=(agech<=5) & (cc==1)
		theta1[boo] = gamma1[0][1]*np.log(theta0[boo]) + gamma2[0][1]*incomepc[boo] +\
		(1 - gamma1[0][1] - gamma2[0][1] )*leisure[boo] + omega[boo]

		#The production of HC: old
		boo=(agech>5)
		theta1[boo] = gamma1[1]*np.log(theta0[boo]) + gamma2[1]*incomepc[boo] +\
		(1 - gamma1[1] - gamma2[1] )*leisure[boo] + omega[boo]

		return np.exp(theta1)


	def Ut(self,periodt,dincome,marr,cc,nkids,ht,thetat,wage,free,price):
		"""
		Computes current-period utility

		"""

		#age of child
		#agech=np.reshape(self.age_t0,(self.N)) + periodt

		#log-theta
		ltheta=np.log(thetat)

		#Work dummies
		d_workf=ht==30
		d_workp=ht==15
		d_unemp=ht==0

		#Consumption: depends on ra, cc, and period
		ct=self.consumptiont(periodt,ht,cc,dincome,marr,nkids,wage,free,price)

		#parameters
		ap=self.param.alphap
		af=self.param.alphaf
		eta=self.param.eta
		ut_h=d_workp*ap + d_workf*af

		#Current-period utility
		ut=np.log(ct) + ut_h +  eta*ltheta

		if (np.any(np.isnan(ct))==True) | (np.any(np.isinf(ct))==True) :
			raise ValueError('Consumption is not a real number')

		if (np.any(np.isnan(ht))==True) | (np.any(np.isinf(ht))==True) :
			raise ValueError('Hours is not a real number')

		if (np.any(np.isnan(ut_h))==True) | (np.any(np.isinf(ut_h))==True) :
			raise ValueError('Hours contribution to utility is not a real number')

		if (np.any(np.isnan(thetat))==True) | (np.any(np.isinf(thetat))==True) :
			raise ValueError('Theta is not a real number')

		if (np.any(np.isnan(np.log(thetat)))==True) | (np.any(np.isinf(np.log(thetat)))==True) :
			raise ValueError('Log of Theta is not a real number')

		if (np.any(np.isnan(ut))==True) | (np.any(np.isinf(ut))==True) :
			raise ValueError('Utility is not a real number')

	
		return ut


	def simulate(self,periodt,wage0,free,price):
		"""
		Takes states (theta0, nkids0, married0, wage0) and given choices
		(self: hours and childcare) to compute current-period utility value.

		"""

		income=self.dincomet(periodt, self.hours,wage0,self.married0,self.nkids0)
		#theta=self.thetat(periodt,self.theta0,self.hours,self.childcare,income,self.married0,self.nkids0)
		

		return self.Ut(periodt,income,self.married0,self.cc,self.nkids0,self.hours,
			self.theta0,wage0,free,price)

	def measures(self,periodt,thetat):
		"""
		For a given periodt and measure, computes the SSRS, given a value for theta.
		There is only one measure for period
		"""
		if periodt==2:
			loc=0
		elif periodt==5:
			loc=1

		lambdam=self.param.lambdas[loc]
		cuts=[self.param.kappas[loc][0],self.param.kappas[loc][1],
		self.param.kappas[loc][2],self.param.kappas[loc][3]]
				
		z_star=lambdam*np.log(thetat) + np.random.randn(self.N)

		#the SSRS measure
		z=np.zeros(self.N)
		z[z_star<=cuts[0]]=1
		z[(z_star>cuts[0]) & (z_star<=cuts[1])]=2
		z[(z_star>cuts[1]) & (z_star<=cuts[2])]=3
		z[(z_star>cuts[2]) & (z_star<=cuts[3])]=4
		z[(z_star>cuts[3])]=5


		return z
			





