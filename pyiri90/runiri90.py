#!/usr/bin/env python
"""
Demo of using IRI reference ionosphere in Python
michael Hirsch
MIT license
"""
from __future__ import division, absolute_import, annotations
from typing import Tuple
import logging
from numpy import ndarray, array
from pandas import DataFrame
from os import chdir, getcwd
from datetime import datetime
import pytz
#
import pyiri90
import iri90  # fortran


def runiri(dt: datetime, z: float | ndarray, glat: float, glon: float, f107: float, f107a: float = None, ap: float = None, *, jmag: bool = False, JF: ndarray=array((1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0), bool))->Tuple[DataFrame, ndarray]:
    """Run the IRI model.

    Args:
        dt (datetime): Time of day. 
        z (float | ndarray): Altitude(s) in km.
        glat (float): Latitude point.
        glon (float): Longitude point.
        f107 (float): F10.7 index for the day.
        f107a (float, optional): 81-day average F10.7 index, unused. Present to maintain parity with GLOW calls. Defaults to None.
        ap (float, optional): Global ap index, unused. Present to maintain parity with GLOW calls. Defaults to None.
        jmag (bool, optional): Geographic (False) or magnetic (True) latitude, longitude. Defaults to False.
        JF (ndarray, optional): Flags for the model. Defaults to array((1, 1, 1, 1, 0, 1, 1, 1, 1, 1, 1, 0), bool) for IRI version found in Solomon (1993). Use (1,1,1) + (0,0,0) +(1,)*14 + (0,1,0,1,1,1,1,0,0,0,1,1,0,1,0,1,1,1) for 2013 version of IRI.

    Returns:
        Tuple[DataFrame, ndarray]: DataFrame containing density and temperature profiles, array containing additional info -> [nmF2 (m-3), hmF2 (km), nmF1 (m-3), hmF1 (km), nmE (m-3), hmE (km), nmD (m-3), hmD (km), hhalf (km), B0 (km), vally base, valley top, Te-peak (K), Te peak height (km), Te-Mod (300 km), Te-Mod (400 km), Te-Mod (600 km), Te-Mod (1400 km), Te-Mod (3000 km), Te-Mod (120 km) = Tn = Ti, Te-Mod (430 km), Z (where Te=Ti), SZA (deg), Sun decl (deg), dip, dip lat, modified dip lat]
    """
    jmag = int(jmag)  # 0:geographic 1: magnetic
    dt = dt.astimezone(pytz.utc)
    # JF = array((1,1,1,1,0,1,1,1,1,1,1,0),bool) #Solomon 1993 version of IRI
    # JF = (1,1,1) + (0,0,0) +(1,)*14 + (0,1,0,1,1,1,1,0,0,0,1,1,0,1,0,1,1,1) #for 2013 version of IRI
# %% call IRI
    cwd = getcwd()
    try:
        chdir(pyiri90.__path__[0])
        logging.debug(getcwd())
        outf, oarr = iri90.iri90(JF, jmag, glat, glon % 360., -f107,
                                 dt.strftime('%m%d'),
                                 dt.hour+dt.minute//60+dt.second//3600,
                                 z, 'data/')
    finally:
        chdir(cwd)
# %% arrange output
    iono = DataFrame(index=z,
                     columns=['ne', 'Tn', 'Ti', 'Te', 'nO+', 'nH+', 'nHe+', 'nO2+', 'nNO+',
                              'nClusterIons', 'nN+'])
    iono['ne'] = outf[0, :]  # ELECTRON DENSITY/M-3
    iono['Tn'] = outf[1, :]  # NEUTRAL TEMPERATURE/K

    iono['Ti'] = outf[2, :]  # ION TEMPERATURE/K
#    i=(iono['Ti']<iono['Tn']).values
#    iono.ix[i,'Ti'] = iono.ix[i,'Tn']

    iono['Te'] = outf[3, :]  # ELECTRON TEMPERATURE/K
#    i=(iono['Te']<iono['Tn']).values
#    iono.ix[i,'Te'] = iono.ix[i,'Tn']

#   iri90 outputs percentage of Ne
    iono['nO+'] = iono['ne'] * outf[4, :]/100.  # O+ ion density / M-3
    iono['nH+'] = iono['ne'] * outf[5, :]/100.  # H+ ion density / M-3
    iono['nHe+'] = iono['ne'] * outf[6, :]/100.  # He+ ion density / M-3
    iono['nO2+'] = iono['ne'] * outf[7, :]/100.  # O2+ "" "" ""
    iono['nNO+'] = iono['ne'] * outf[8, :]/100.  # NO+ "" "" ""
    iono['nClusterIons'] = iono['ne'] * outf[9, :]/100.
    iono['nN+'] = iono['ne'] * outf[10, :]/100.
    return iono, oarr
