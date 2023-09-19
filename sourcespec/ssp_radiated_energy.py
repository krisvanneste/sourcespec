# -*- coding: utf8 -*-
# SPDX-License-Identifier: CECILL-2.1
"""
Compute radiated energy from spectral integration.

:copyright:
    2012 Claudio Satriano <satriano@ipgp.fr>

    2013-2014 Claudio Satriano <satriano@ipgp.fr>,
              Emanuela Matrullo <matrullo@geologie.ens.fr>,
              Agnes Chounet <chounet@ipgp.fr>

    2015-2023 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement v2.1
    (http://www.cecill.info/licences.en.html)
"""
import logging
import numpy as np
from sourcespec.ssp_data_types import SpectralParameter
logger = logging.getLogger(__name__.rsplit('.', maxsplit=1)[-1])


def _spectral_integral(spec, t_star, fmax):
    """Compute spectral integral in eq. (3) from Lancieri et al. (2012)."""
    # Note: eq. (3) from Lancieri et al. (2012) is the same as
    # eq. (1) in Boatwright et al. (2002), but expressed in frequency,
    # instead of angular frequency (2pi factor).
    deltaf = spec.stats.delta
    freq = spec.get_freq()
    # Data is in moment units. By dividing by coeff, we get the units of the
    # Fourier transform of the ground displacement (m * s) multiplied by the
    # units of the geometrical spreading correction (m).
    # The result is threfore in units of m^2*s
    data = spec.data / spec.coeff
    # Then a derivative with respect to time is performed (to go from
    # displacement to velocity) through multiplication by 2*pi*freq.
    # The result is in units of m^2.
    data *= (2 * np.pi * freq)
    # Correct data for attenuation:
    data *= np.exp(np.pi * t_star * freq)
    # Compute the energy integral, up to fmax:
    if fmax is not None:
        data[freq > fmax] = 0.
    # Returned value has units of (m^2)^2 * Hz = m^4/s
    return np.sum(data**2) * deltaf


def _radiated_energy_coefficient(rho, vel):
    """Compute coefficient in eq. (3) from Lancieri et al. (2012)."""
    # Note: eq. (3) from Lancieri et al. (2012) is the same as
    # eq. (1) in Boatwright et al. (2002), but expressed in frequency,
    # instead of angular frequency (2pi factor).
    # In the original eq. (3) from Lancieri et al. (2012), eq. (3),
    # the correction term is:
    #       8 * pi * r**2 * C**2 * rho * vs
    # We do not multiply by r**2, since data is already distance-corrected.
    # From Boatwright et al. (2002), eq. (2), C = <Fs>/(Fs * S),
    # where <Fs> is the average radiation pattern in the focal sphere
    # and Fs is the radiation pattern for the given angle between source
    # and receiver. Here we put <Fs>/Fs = 1, meaning that we rely on the
    # averaging between measurements at different stations, instead of
    # precise measurements at a single station.
    # S is the free-surface amplification factor, which we put = 2
    # This coefficient has units of kg/m^3 * m/s = kg/(m^2 * s)
    return 8 * np.pi * (1. / 2.)**2 * rho * vel


def _finite_bandwidth_correction(spec, fc, fmax):
    """
    Compute finite bandwidth correction.

    Expressed as the ratio R between the estimated energy
    and the true energy (Di Bona & Rovelli 1988)
    """
    if fmax is None:
        fmax = spec.get_freq()[-1]
    return (
        2. / np.pi *
        (np.arctan2(fmax, fc) - (fmax / fc) / (1 + (fmax / fc)**2.))
    )


def radiated_energy_and_apparent_stress(
        config, spec_st, specnoise_st, sspec_output):
    """
    Compute radiated energy (in N.m) and apparent stress (in MPa).

    :param config: Config object
    :param config type: :class:`sourcespec.config.Config`
    :param spec_st: Stream of spectra
    :param spec_st type: :class:`obspy.core.stream.Stream`
    :param specnoise_st: Stream of noise spectra
    :param specnoise_st type: :class:`obspy.core.stream.Stream`
    :param sspec_output: Output of spectral inversion
    :param sspec_output type:
        :class:`sourcespec.ssp_data_types.SourceSpecOutput`
    """
    logger.info('Computing radiated energy and apparent stress...')
    fmax = config.max_freq_Er
    rho = config.event.hypocenter.rho
    vs_hypo = config.event.hypocenter.vs * 1e3
    mu = rho * vs_hypo**2
    logger.info(
        'Rigidity value close to the source (mu_h) for apparent stress: '
        f'{mu:.3e} Pa')
    # Select specids with channel code: '??H'
    spec_ids = [spec.id for spec in spec_st if spec.id[-1] == 'H']
    for spec_id in spec_ids:
        spec = spec_st.select(id=spec_id)[0]
        specnoise = specnoise_st.select(id=spec_id)[0]

        try:
            station_pars = sspec_output.station_parameters[spec_id]
        except KeyError:
            continue
        t_star = station_pars.t_star.value
        fc = station_pars.fc.value
        # Make sure that the param_Er and param_sigma_a objects are always
        # defined, even when Er and/or sigma_a are not computed
        # (i.e., "continue" below)
        try:
            param_Er = station_pars.Er
        except KeyError:
            param_Er = SpectralParameter(
                param_id='Er', value=np.nan, format_spec='{:.3e}')
            station_pars.Er = param_Er
        try:
            param_sigma_a = station_pars.sigma_a
        except KeyError:
            param_sigma_a = SpectralParameter(
                param_id='sigma_a', value=np.nan, format_spec='{:.3e}')
            station_pars.sigma_a = param_sigma_a

        # Compute signal and noise integrals and subtract noise from signal,
        # under the hypothesis that energy is additive and noise is stationary
        signal_integral = _spectral_integral(spec, t_star, fmax)
        noise_integral = _spectral_integral(specnoise, t_star, fmax)
        rho = spec.stats.rho_station
        vel = spec.stats.v_station * 1e3
        coeff = _radiated_energy_coefficient(rho, vel)
        # Total radiated energy is the sum of Er_p and Er_s, and Er_s/Er_p=15.6
        # (Boatwright & Choy, 1986, eq. 8 & 15)
        if config.wave_type == 'P':
            coeff *= (1 + 15.6)
        else:
            coeff *= (1 + 1. / 15.6)
        # Coefficient has units of kg/(m^2 * s)
        # Signal and noise integrals have units of m^4 / s
        # Er has therefore units of kg * m^2 / s^2 = kg * m/s^2 * m = N * m
        Er = coeff * (signal_integral - noise_integral)
        if Er < 0:
            logger.warning(
                f'{spec_id} {spec.stats.instrtype}: noise energy is larger '
                'than signal energy: skipping spectrum.')
            continue

        R = _finite_bandwidth_correction(spec, fc, fmax)
        Er /= R
        # Store the Er value into the StationParameter() object
        param_Er.value = Er
        # Store the Er value in the spec_synth stats
        spec_synth = spec_st.select(id=f'{spec_id[:-1]}S')[0]
        spec_synth.stats.par['Er'] = Er

        # Now compute apparent stress sigma_a
        # (eq. (5) from Lancieri et al. 2012)
        Mo = station_pars.Mo.value
        Mo_min = Mo - station_pars.Mo.lower_uncertainty
        Mo_max = Mo + station_pars.Mo.upper_uncertainty
        sigma_a = mu * Er / Mo / 1e6  # in MPa
        sigma_a_min = mu * Er / Mo_max / 1e6  # in MPa
        sigma_a_max = mu * Er / Mo_min / 1e6  # in MPa
        param_sigma_a.value = sigma_a
        param_sigma_a.lower_uncertainty = sigma_a - sigma_a_min
        param_sigma_a.upper_uncertainty = sigma_a + sigma_a_max
        param_sigma_a.confidence_level = station_pars.Mo.confidence_level

    logger.info('Computing radiated energy and apparent stress: done')
    logger.info('---------------------------------------------------')
