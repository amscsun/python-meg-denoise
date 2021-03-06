from numpy import *
import scipy.linalg
from denoise import *

def dss1(data, weights = None, keep1 = None, keep2 = None):
    """docstring for dss1"""
    
    if not any(weights): weights = array([])
    if not keep1: keep1 = array([])
    if not keep2: keep2 = 10.0 ** -12
    
    m, n, o = theshapeof(data)
    data, data_mean = demean(data, weights) # remove weighted mean
    
    # weighted mean over trials (--> bias function for DSS)
    xx, ww = mean_over_trials(data, weights)
    print "xx.shape", xx.shape
    ww = ww.min(1)
    
    # covariance of raw and biased data
    c0, nc0 = tscov(data, None, weights)
    c1, nc1 = tscov(xx, None, ww)
    c1 = c1 / o
    
    todss, fromdss, ratio, pwr = dss0(c0, c1, keep1, keep2)
    
    return todss, fromdss, ratio, pwr


def dss0(c1, c2, keep1, keep2):
    """docstring for dss0"""
    
    # SANITY CHECKS GO HERE
    
    # derive PCA and whitening matrix from unbiased covariance
    topcs1, evs1 = pcarot(c1)
    if keep1:
        topcs1 = topcs1[:, arange(keep1)]
        evs1 = evs1[arange(keep1)]
    
    if keep2:
        idx = where(evs1/max(evs1) > keep2)
        topcs1 = topcs1[:, idx]
        evs1 = evs1[idx]
        
    # apply whitening and PCA matrices to the biased covariance
    # (== covariance of bias whitened data)
    N = diag(sqrt(1/evs1))
    c3 = dot(dot(dot(dot(N.T, topcs1.squeeze().T), c2), topcs1.squeeze()), N)
    
    # derive the dss matrix
    topcs2, evs2 = pcarot(c3)
    todss = topcs1.squeeze() * N * topcs2
    fromdss = linalg.pinv(todss)
    
    # dss to data projection matrix
    cxy = c1 * todss # covariance between unbiased data and selected DSS component
    
    # estimate power per DSS component
    pwr = zeros((todss.shape[1], 1))
    
    for k in xrange(todss.shape[1]):
        to_component = todss[:, k] * fromdss[k, :]
        cc = to_component.T * c1 * to_component
        cc = diag(cc)
        pwr[k] = sum(cc**2)
    
    ratio = diag(todss.T * c2 * todss) / diag(todss.T * c1 * todss)
    
    return todss, fromdss, ratio, pwr

