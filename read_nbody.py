# -*- coding: utf-8 -*-
"""
Methods to load halo catalogs into memory.
Not even close to the needed level of generality.
Currently is only useful at loading in a pre-processed halo catalog.
Adequate only while basic functionality of mock-making code is being developed.

.. module : read_nbody 
    :synopsis: Modules to read and parse ASCII data of ROCKSTAR halo and merger tree catalogs.

.. moduleauthor: Andrew Hearin <andrew.hearin@yale.edu>


"""

from astropy.io import ascii
import pyfits
import defaults

def read_barebones_ascii_halo_catalog_for_initial_mock_development(filename):
    """ Read filename and return an astropy structured table called 'halos'. Currently a basically useless method.

    Args:
        filename (str): Name of file containing ASCII data

    Returns:
        halos : A record array containing halo catalog information.

    """
    
    column_names = ('id','mvir','x','y','z','vx','vy','vz')
#    types = ('long','float','float','float','float','float','float','float')
    halos = ascii.read(filename, delimiter='\s', names=column_names, data_start=0)

    print 'number of host halos read in:', len(halos)
    return halos

def load_bolshoi_host_halos_fits(simulation_dict=None):
    """Placeholder method using pyfits to load a pre-processed .fits file containing host halo information.

    Args:
        simulation_dict : dictionary

    Contains keys for the filename, as well as simulation attributes such as 
    box size, resolution, and scale factor of snapshot.

    Returns:
        simulation : dictionary

    Halos key is a structured table containing halo catalog information.
    simulation_dict key is the input dictionary.

    Default is Rockstar V1.5 Bolshoi halos at a=1.0003.

    """

    if simulation_dict == None:
        simulation_dict = defaults.default_simulation_dict

    halos = pyfits.getdata(simulation_dict['catalog_filename'],0)
    # should be using astropy units!
    simulation = {'halos':halos,'simulation_dict':simulation_dict}
    return simulation

