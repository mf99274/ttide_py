# Autogenerated with SMOP version 0.23
# main.py ../t_tide1.3/t_predic.m -o ../t_tide_py/t_predic.py
from __future__ import division
import numpy as np
from scipy.io import loadmat,savemat
import os

def t_predic(*varargin):
    """T_PREDIC Tidal prediction
     YOUT=T_PREDIC(TIM,NAMES,FREQ,TIDECON) makes a tidal prediction
     using the output of T_TIDE at the specified times TIM in decimal 
     days (from DATENUM). Optional arguments can be specified using
     property/value pairs: 

           YOUT=T_PREDIC(...,TIDECON,property,value,...)

     Available properties are:

        In the simplest case, the tidal analysis was done without nodal
        corrections, and thus neither will the prediction. If nodal 
        corrections were used in the analysis, then it is likely we will
        want to use them in the prediction too and these are computed 
        using the latitude, if given.

         'latitude'        decimal degrees (+north) (default: none)

        If the original analysis was >18.6 years satellites are
        not included and we force that here:

         'anallength'      'nodal' (default)
                           'full'  For >18.6 years.

        The tidal prediction may be restricted to only some of the 
        available constituents:

         'synthesis'    0 - Use all selected constituents.  (default)
                        scalar>0 - Use only those constituents with a SNR
                                   greater than that given (1 or 2 are
                                   good choices).


      It is possible to call t_predic without using property names, in
      which case the assumed calling sequence is

        YOUT=T_PREDIC(TIM,NAMES,FREQ,TIDECON,LATITUDE,SYNTHESIS);

      T_PREDIC can be called using the tidal structure available as an 
      optional output from T_TIDE

        YOUT=T_PREDIC(TIM,TIDESTRUC,...)

      This is in fact the recommended calling procedure (and required
      when the analysis results are from series>18.6 years in length)
     R. Pawlowicz 11/8/99
     Version 1.0
     8/2/03 - Added block processing to generate prediction (to
              avoid memory overflows for long time series).
     29/9/04 - small bug with undefined ltype fixed
    """
    nargin = len(varargin)
    if nargin > 0:
        tim = varargin[0]
    if nargin > 1:
        varargin = varargin[1]
    if nargin < 2:
        # Not enough
        error('Not enough input arguments')
    longseries = 0
    ltype = 'nodal'
    if isstruct(varargin[0]):
        names = varargin[0].name
        freq = varargin[0].freq
        tidecon = varargin[0].tidecon
        if hasattr(varargin[0], 'ltype') & varargin[0].ltyp(range(1, 4)) == 'ful':
            longseries = 1
        varargin[0] = np.array([])
    else:
        if max(varargin.shape) < 3:
            error('Not enough input arguments')
        names = varargin[0]
        freq = varargin[1]
        tidecon = varargin[2]
        varargin[0:3] = np.array([])
    lat = np.array([])
    synth = 0
    k = 1
    while max(varargin.shape) > 0:

        if ischar(varargin[0]):
            if 'lat' == lower(varargin[-2](range(1, 4))):
                lat = varargin[1]
            else:
                if 'syn' == lower(varargin[-2](range(1, 4))):
                    synth = varargin[1]
                else:
                    if 'ana' == lower(varargin[-2](range(1, 4))):
                        if isstr(varargin[1]):
                            ltype = varargin[1]
                            if varargin[1](range(1, 4)) == 'ful':
                                longseries = 1
                    else:
                        error("Can't understand property:" + varargin[0])
            varargin[(np.array([1, 2]).reshape(1, -1) -1)] = np.array([])
        else:
            if 1 == k:
                lat = varargin[0]
            else:
                if 2 == k:
                    synth = varargin[0]
                else:
                    error('Too many input parameters')
            varargin[0] = np.array([])
        k = k + 1

    # Do the synthesis.        
    snr = (tidecon[:, 0] / tidecon[:, 1]) ** 2
    # signal to noise ratio
    if synth > 0:
        I = snr > synth
        if not  any(I):
            warning('No predictions with this SNR')
            yout = NaN + np.zeros(shape=(tim.shape, tim.shape), dtype='float64')
            return yout
        tidecon = tidecon[(I -1), :]
        names = names[(I -1), :]
        freq = freq[(I -1)]
    if tidecon.shape[1] == 4:
        # Real time series
        ap = np.dot(tidecon[:, 0] / 2.0, exp(np.dot(np.dot(- i, tidecon[:, 2]), pi) / 180))
        am = conj(ap)
    else:
        ap = np.dot((tidecon[:, 0] + tidecon[:, 2]) / 2.0, exp(np.dot(np.dot(i, pi) / 180, (tidecon[:, 4] - tidecon[:, 6]))))
        am = np.dot((tidecon[:, 0] - tidecon[:, 2]) / 2.0, exp(np.dot(np.dot(i, pi) / 180, (tidecon[:, 4] + tidecon[:, 6]))))
    # Mean at central point (get rid of one point at end to take mean of
    # odd number of points if necessary).
    jdmid = mean(tim[0:np.dot(2, fix((max(tim.shape) - 1) / 2)) + 1])
    if longseries:
        const = t_get18consts
        ju = np.zeros(shape=(freq.shape, freq.shape), dtype='float64')
        for k in range(1, (names.shape[0] +1)):
            inam = strmatch(names[(k -1), :], const.name)
            if max(inam.shape) == 1:
                ju[(k -1)] = inam
            else:
                if max(inam.shape) > 1:
                    minf, iminf = np.min(abs(freq[(k -1)] - const.freq(inam))) # nargout=2
                    ju[(k -1)] = inam[(iminf -1)]
    else:
        const = t_getconsts
        ju = np.zeros(shape=(freq.shape, freq.shape), dtype='float64')
        # Check to make sure names and frequencies match expected values.
        for k in range(1, (names.shape[0] +1)):
            ju[(k -1)] = strmatch(names[(k -1), :], const.name)
        #if any(freq~=const.freq(ju)),
        #  error('Frequencies do not match names in input');
        #end;
    # Get the astronical argument with or without nodal corrections.  
    if not  (0 in lat.shape) & abs(jdmid) > 1:
        v, u, f = t_vuf(ltype, jdmid, ju, lat) # nargout=3
    else:
        if abs(jdmid) > 1:
            # a real date				  
            v, u, f = t_vuf(ltype, jdmid, ju) # nargout=3
        else:
            v = np.zeros(shape=(max(ju.shape), 1), dtype='float64')
            u = v
            f = np.ones(shape=(max(ju.shape), 1), dtype='float64')
    ap = ap * f * exp(np.dot(np.dot(np.dot(+ i, 2), pi), (u + v)))
    am = am * f * exp(np.dot(np.dot(np.dot(- i, 2), pi), (u + v)))
    tim = tim - jdmid
    n, m = tim.shape # nargout=2
    tim = tim[:].T
    ntim = max(tim.shape)
    nsub = 10000
    # longer than one year hourly.
    for j1 in range(1, (ntim +1), nsub):
        j2 = np.min(j1 + nsub - 1, ntim)
        yout[(j1 -1):j2] = np.sum(exp(np.dot(np.dot(np.dot(np.dot(np.dot(i, 2), pi), freq), tim[(j1 -1):j2]), 24)) * ap[:, (np.ones(shape=(1, j2 - j1 + 1), dtype='float64') -1)], 1) + np.sum(exp(np.dot(np.dot(np.dot(np.dot(np.dot(- i, 2), pi), freq), tim[(j1 -1):j2]), 24)) * am[:, (np.ones(shape=(1, j2 - j1 + 1), dtype='float64') -1)], 1)
    yout = reshape(yout, n, m)
    return yout
