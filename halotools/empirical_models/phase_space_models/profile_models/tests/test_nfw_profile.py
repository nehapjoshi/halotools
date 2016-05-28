""" Module providing unit-testing for `~halotools.empirical_models.NFWProfile` class
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import numpy as np

from unittest import TestCase
import pytest

from astropy.cosmology import WMAP9

from ..nfw_profile import NFWProfile

from .....utils.array_utils import array_is_monotonic


__all__ = (
    ['TestNFWProfile',
    'analytic_nfw_density_outer_shell_normalization',
    'monte_carlo_density_outer_shell_normalization']
    )

def analytic_nfw_density_outer_shell_normalization(radii, conc):
    """ Density of an NFW profile normalized by the density evaluated at the outermost value of the input ``radii`` array.

    For an NFW profile we have the following analytical relation:

    :math:`\\rho(r_{2})/\\rho(r_{1}) = \\frac{r_{1}(1+cr_{1})^{2}}{r_{2}(1+cr_{2})^{2}}`.

    The `TestNFWProfile.test_mc_generate_nfw_radial_positions` test demonstrates that Monte Carlo realizations
    of `~halotools.empirical_models.NFWProfile` generated by the
    `~halotools.empirical_models.NFWProfile.mc_generate_nfw_radial_positions`
    method respect this relation.

    Parameters
    ------------
    radii : array_like
        Array of halo-centric distances in an NFW profile.

    conc : float
        Concentration of the halo for which this relation is being tested.

    Returns
    --------
    result : array_like
        Ratio of the NFW density scaled by the density value at the outermost value of the input ``radii``.

    """
    outer_radius = radii[-1]
    numerator = outer_radius*(1 + conc*outer_radius)**2
    denominator = radii*(1 + conc*radii)**2
    return numerator/denominator

def monte_carlo_density_outer_shell_normalization(rbins, radial_positions):
    """ Density of a Monte Carlo realization of a spherically symmetric profile normalized by the density evaluated at the midpoint of the outermost bin of the input ``rbins`` array.

    Parameters
    ------------
    rbins : array_like
        Array defining how the input ``radial_positions`` will be binned.

    radial_positions : array_like
        Array storing the Monte Carlo realization of the profile.

    Returns
    --------
    rbin_midpoints : array_like
        Midpoints of the input ``rbins``.

    result : array_like
        Ratio of the profile number density scaled by the number density at the midpoint of the outermost bin of the input ``rbins`` array.

    """
    rbin_midpoints = 0.5*(rbins[:-1] + rbins[1:])
    counts = np.histogram(radial_positions, bins = rbins)[0].astype(np.float64)
    outer_radius = rbin_midpoints[-1]
    outer_counts = counts[-1]
    return rbin_midpoints, (counts/rbin_midpoints**2)/(outer_counts/outer_radius**2)



class TestNFWProfile(TestCase):
    """ Tests of `~halotools.empirical_models.NFWProfile`.

    """

    def setup_class(self):
        """ Pre-load various arrays into memory for use by all tests.
        """
        self.default_nfw = NFWProfile()
        self.wmap9_nfw = NFWProfile(cosmology = WMAP9)
        self.m200_nfw = NFWProfile(mdef = '200m')

        self.model_list = [self.default_nfw, self.wmap9_nfw, self.m200_nfw]

    def test_instance_attrs(self):
        """ Require that all model variants have ``cosmology``, ``redshift`` and ``mdef`` attributes.
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
        """ Require the returned value of the `~halotools.empirical_models.NFWProfile.mass_density` function to be self-consistent with the returned value of the `~halotools.empirical_models.NFWProfile.dimensionless_mass_density` function.
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
        """ Require the `~halotools.empirical_models.NFWProfile.cumulative_mass_PDF` method in all model variants to respect a number of consistency conditions.

        1. Returned value is a strictly monotonically increasing array between 0 and 1.

        2. Returned value is consistent with the following expression,

        :math:`P_{\\rm NFW}(<\\tilde{r}) = 4\\pi\\int_{0}^{\\tilde{r}}d\\tilde{r}\\tilde{r}'^{2}\\tilde{\\rho}_{NFW}(\\tilde{r}),`

        In the test suite implementation of the above equation,
        the LHS is computed by the analytical expression given in
        `~halotools.empirical_models.NFWProfile.cumulative_mass_PDF`,
        :math:`P_{\\rm NFW}(<\\tilde{r}) = g(c\\tilde{r})/g(\\tilde{r})`, where the function
        :math:`g(x) \\equiv \\int_{0}^{x}dy\\frac{y}{(1+y)^{2}} = \\log(1+x) - x / (1+x)`
        is computed using the
        `~halotools.empirical_models.NFWProfile.g` method of the
        `~halotools.empirical_models.NFWProfile` class.

        The RHS of the consistency equation is computed by performing a direct numerical integral of

        :math:`\\tilde{\\rho}_{\\rm NFW}(\\tilde{r}) \equiv \\rho_{\\rm NFW}(\\tilde{r})/\\rho_{\\rm thresh} = \\frac{c^{3}}{3g(c)}\\times\\frac{1}{c\\tilde{r}(1 + c\\tilde{r})^{2}}.`
        where in the test suite implementation :math:`\\tilde{\\rho}_{\\rm NFW}(\\tilde{r})` is computed
        using the `~halotools.empirical_models.NFWProfile.dimensionless_mass_density`
        method of the `~halotools.empirical_models.NFWProfile` class.

        3. :math:`M_{\\Delta}(<r) = M_{\\Delta}\\times P_{\\rm NFW}(<r)`.

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

    def test_vmax(self):
        """ Require that the analytic approximation used to estimate the NFW :math:`V_{\\rm max}`
        by the `~halotools.empirical_models.NFWProfile.vmax` method
        agrees with the maximum value of :math:`V_{\\rm circ}(r)` computed over the entire profile
        of the halo computed using the super-class method
        `~halotools.empirical_models.profile_model_template.AnalyticDensityProf.dimensionless_circular_velocity` method.
        """
        npts = 1000
        total_mass = np.zeros(npts) + 1e12
        conc_list = [5, 10, 25]
        radius_array = np.logspace(-2, 0, npts)

        for model in self.model_list:
            for conc in conc_list:
                analytic_vmax = model.vmax(total_mass, conc)
                derived_vmax = model.circular_velocity(radius_array, total_mass, conc).max()
                assert np.allclose(analytic_vmax, derived_vmax, rtol = 0.01)

    @pytest.mark.slow
    def test_mc_generate_nfw_radial_positions(self):
        """ Require that the points returned by the `~halotools.empirical_models.NFWProfile.mc_generate_nfw_radial_positions` function do indeed trace an NFW profile.

        The basic idea is as follows. By the method of transformation of random variates,
        we can generate a Monte Carlo realization of an NFW profile provided that we have the mapping
        :math:`P^{-1}_{\\rm NFW}(<\\tilde{r})`. The method
        `~halotools.empirical_models.NFWProfile.mc_generate_nfw_radial_positions`
        obtains this mapping by first computing :math:`P_{\\rm NFW}(<\\tilde{r})` at a set of abscissa,
        and then using `~scipy.interpolate.InterpolatedUnivariateSpline` to tabulate the inverse mapping.
        In the Halotools implementation, the code calling the inverse mapping is
        `~halotools.empirical_models.custom_spline`, which is just a convenience wrapper
        around `~scipy.interpolate.InterpolatedUnivariateSpline` that handles edge cases a bit more intuitively.

        For volume elements evenly spaced in :math:`\\tilde{r}`, any NFW profile must respect the following relation:

        :math:`\\rho(r_{2})/\\rho(r_{1}) = \\frac{r_{1}(1+cr_{1})^{2}}{r_{2}(1+cr_{2})^{2}}`,

        The `test_mc_generate_nfw_radial_positions` function enforces that this relation holds using
        :math:`\\tilde{r}_{1} \\approx 1`.
        After generating a set of radial positions, the
        `analytic_nfw_density_outer_shell_normalization` returns the analytical result for
        :math:`\\rho(r_{2})/\\rho(r_{1})` for the given ``rbins``, and the
        `monte_carlo_density_outer_shell_normalization` method computes this ratio for the
        Monte Carlo realization. As shown in the source code, these two quantities agree with each other
        to better than 2% when using 20 bins linearly-spaced between 0.05 and 1 and
        2e6 Monte Carlo-generated points, for NFW concentrations of 5, 10, and 25.

        """
        halo_radius = 0.5
        num_pts = int(2e6)
        num_rbins = 20
        rbins = np.linspace(0.05, 1, num_rbins)

        conc_to_test = [5, 10, 25]

        for model in self.model_list:

            for conc in conc_to_test:
                radial_positions = model.mc_generate_nfw_radial_positions(
                    halo_radius = halo_radius, conc = conc, num_pts = num_pts,
                    seed = 43)

                radial_positions /= halo_radius

                rbin_midpoints, monte_carlo_ratio = (
                    monte_carlo_density_outer_shell_normalization(rbins, radial_positions))

                analytical_ratio = (
                    analytic_nfw_density_outer_shell_normalization(rbin_midpoints, conc))

                assert np.allclose(monte_carlo_ratio, analytical_ratio, 0.02)
