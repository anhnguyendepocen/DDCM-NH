"""
execfile('cpi.py')

This file stores the CPI index values
"""
from __future__ import division #omit for python 3.x
import numpy as np
import pandas as pd
import itertools
import sys, os
import pickle
from scipy import stats


cpi=[148.4,153.0,156.7,159.3,162.7,168.3,172.8,174.9,178.3]

#Saving the list
pickle.dump(cpi,open('/mnt/Research/nealresearch/new-hope-secure/newhopemount/codes/model_v2/simulate_sample/cpi.p','wb'))


