from copy import copy
import numpy as np

import pandas as pd
from syscore.genutils import str2Bool
    
def diversification_mult_single_period(corrmatrix, weights, floor_at_zero=True):
    """
    Given N assets with a correlation matrix of H and  weights W summing to 1, 
    the diversification multiplier will be 1 / [ ( W x H x WT ) 1/2 ]
    
    :param corrmatrix: Correlation matrix
    :type corrmatrix: np.array square, 2-dim 
    
    :param weights: Weights of assets
    :type weights: list of floats (aligned with corrmatrix)

    :param floor_at_zero: remove negative correlations before proceeding
    :type floor_at_zero: bool or str
    
    :returns: float 

    >>> corrmatrix=np.array([[1.0,0.0], [0.0,1.0]])
    >>> weights=[.5,.5]
    >>> diversification_mult_single_period(corrmatrix, weights)
    1.414213562373095
    """
    floor_at_zero=str2Bool(floor_at_zero)
    weights=np.array(weights, ndmin=2)

    if floor_at_zero:
        corrmatrix=copy(corrmatrix)
        corrmatrix[corrmatrix<0]=0.0
    
    return 1.0 / (
         float(
                np.dot(np.dot(weights, corrmatrix), weights.transpose()))
                  **.5)


def diversification_multiplier_from_list(correlation_list_object, weight_df_raw, ewma_span=125, **kwargs):
    """
    Given a CorrelationList object, and a dataframe of weights, work out the div multiplier

    :param correlation_list_object: CorrelationList to use for calculation
    :type correlation_list_object: CorrelationList 
    
    :param weight_df_raw: Weights of assets
    :type weight_df_raw: TxN pd.DataFrame

    :param ewma_span: Smoothing parameter to use on output (1= no smoothing)
    :type ewma_span: int

    :param **kwargs: Used for single period calculation 
    
    :returns: Tx1 pd.DataFrame 
    
    """
    ## align weights to corr list
    weight_df=weight_df_raw[correlation_list_object.columns]

    ref_periods=[fit_period.period_start for fit_period in correlation_list_object.fit_dates]
    
    ## here's where we stack up the answers
    div_mult_vector=[]
    
    for (corrmatrix, start_of_period) in zip(correlation_list_object.corr_list, ref_periods):
    
        weight_slice=weight_df[:start_of_period]
        if weight_slice.shape[0]==0:
            div_mult_vector.append(1.0)
            continue
        
        weights=list(weight_slice.iloc[-1,:].values)
        div_multiplier=diversification_mult_single_period(corrmatrix, weights, **kwargs)
        
        div_mult_vector.append(div_multiplier)
    
    div_mult_df=pd.DataFrame(div_mult_vector, columns=["DivMult"], index=ref_periods)
    div_mult_df=div_mult_df.reindex(weight_df.index, method="ffill")
    
    div_mult_df=pd.ewma(div_mult_df, span=125)
    
    return div_mult_df
    
if __name__ == '__main__':
    import doctest
    doctest.testmod()