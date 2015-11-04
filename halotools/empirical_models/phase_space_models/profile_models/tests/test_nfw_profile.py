#!/usr/bin/env python
from __future__ import (absolute_import, division, print_function, 
    unicode_literals)

import numpy as np 

from unittest import TestCase
import pytest 

from astropy.cosmology import WMAP9, Planck13
from astropy import units as u

from ..profile_helpers import *
from ..nfw_profile import NFWProfile

from .....custom_exceptions import HalotoolsError
from .....utils.array_utils import array_is_monotonic


__all__ = ['TestNFWProfile']

class TestNFWProfile(TestCase):
    """ Tests of `~halotools.empirical_models.phase_space_models.profile_models.NFWProfile`. 

    Basic summary of tests:

        * Default settings for lookup table arrays all have reasonable values and ranges. 

        * Discretization of NFW Profile with lookup table attains better than 0.1 percent accuracy for all relevant radii and concentrations

        * Lookup table recomputes properly when manually passed alternate discretizations 
    """

    def setup_class(self):
        self.default_nfw = NFWProfile()
        self.wmap9_nfw = NFWProfile(cosmology = WMAP9)
        self.m200_nfw = NFWProfile(mdef = '200m')

        self.model_list = [self.default_nfw, self.wmap9_nfw, self.m200_nfw]

    def test_instance_attrs(self):
        """
        """
        assert hasattr(self.default_nfw, 'cosmology')
        assert hasattr(self.wmap9_nfw, 'cosmology')
        assert hasattr(self.m200_nfw, 'cosmology')

        assert hasattr(self.default_nfw, 'redshift')
        assert hasattr(self.wmap9_nfw, 'redshift')
        assert hasattr(self.m200_nfw, 'redshift')

        assert hasattr(self.default_nfw, 'mdef')
        assert hasattr(self.wmap9_nfw, 'mdef')
        assert hasattr(self.m200_nfw, 'mdef')

    def test_mass_density(self):
        """ Require the returned value of the 
        `~halotools.empirical_models.phase_space_models.profile_models.NFWProfile.mass_density` 
        function to be self-consistent with the 
        returned value of the 
        `~halotools.empirical_models.phase_space_models.profile_models.NFWProfile.dimensionless_mass_density` 
        function. 
        """
        Npts = 100
        radius = np.logspace(-2, -1, Npts)
        mass = np.zeros(Npts) + 1e12
        conc = 5

        for model in self.model_list:
            result = model.mass_density(radius, mass, conc)

            halo_radius = model.halo_mass_to_halo_radius(mass)
            scaled_radius = radius/halo_radius
            derived_result = (
                model.density_threshold * 
                model.dimensionless_mass_density(scaled_radius, conc)
                )
            assert np.allclose(derived_result, result, rtol = 1e-4)


    def test_cumulative_mass_PDF(self):
        """
        """
        Npts = 100
        total_mass = np.zeros(Npts) + 1e12
        scaled_radius = np.logspace(-2, -0.01, Npts)
        conc = 5

        for model in self.model_list:
            result = model.cumulative_mass_PDF(scaled_radius, conc)

            # Verify that the result is monotonically increasing between (0, 1)
            assert np.all(result > 0)
            assert np.all(result < 1)
            assert array_is_monotonic(result, strict=True) == 1

            # Enforce self-consistency between the analytic expression for cumulative_mass_PDF 
            ### and the direct numerical integral of the analytical expression for 
            ### dimensionless_mass_density
            super_class_result = super(NFWProfile, model).cumulative_mass_PDF(
                scaled_radius, conc)
            assert np.allclose(super_class_result, result, rtol = 1e-4)

            # Verify that we get a self-consistent result between 
            ### enclosed_mass and cumulative_mass_PDF
            halo_radius = model.halo_mass_to_halo_radius(total_mass)
            radius = scaled_radius*halo_radius
            enclosed_mass = model.enclosed_mass(radius, total_mass, conc)
            derived_enclosed_mass = result*total_mass
            assert np.allclose(enclosed_mass, derived_enclosed_mass, rtol = 1e-4)















