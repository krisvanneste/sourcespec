# -*- coding: utf-8 -*-
"""
Earthquake source parameters from inversion of S-wave spectra.

:copyright:
    2012 Claudio Satriano <satriano@ipgp.fr>

    2013-2014 Claudio Satriano <satriano@ipgp.fr>,
              Emanuela Matrullo <matrullo@geologie.ens.fr>,
              Agnes Chounet <chounet@ipgp.fr>

    2015-2016 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement, Version 2.1
    (http://www.cecill.info/index.en.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

from sourcespec.ssp_setup import (configure, setup_logging, save_config,
                                  init_plotting, ssp_exit)
from sourcespec.ssp_read_traces import read_traces
from sourcespec.ssp_process_traces import process_traces
from sourcespec.ssp_build_spectra import build_spectra
from sourcespec.ssp_local_magnitude import local_magnitude
from sourcespec.ssp_inversion import spectral_inversion
from sourcespec.ssp_output import write_output
from sourcespec.ssp_residuals import spectral_residuals
from sourcespec.ssp_plot_spectra import plot_spectra
from sourcespec.ssp_plot_traces import plot_traces


def main():
    # Setup stage
    config = configure()
    setup_logging(config)

    st = read_traces(config)

    # Now that we (hopefully) have the evid
    # we rename the logfile to use the evid
    #TODO: improve this:
    evid = st.traces[0].stats.hypo.evid
    setup_logging(config, evid)

    # Save config to out dir
    save_config(config, evid)

    # Deconvolve, filter, cut traces:
    proc_st = process_traces(config, st)

    # Build spectra (amplitude in magnitude units)
    spec_st, specnoise_st, weight_st =\
        build_spectra(config, proc_st, noise_weight=True)

    plotter = init_plotting()
    plot_traces(config, proc_st, ncols=2, async_plotter=plotter)

    Ml = local_magnitude(config, st, deconvolve=True)

    # Spectral inversion
    sourcepar = spectral_inversion(config, spec_st, weight_st, Ml)

    # Save output
    sourcepar_mean = write_output(config, evid, sourcepar)

    # Save residuals
    spectral_residuals(config, spec_st, evid, sourcepar_mean)

    # Plotting
    plot_spectra(config, spec_st, specnoise_st, plottype='regular',
                 async_plotter=plotter)
    plot_spectra(config, specnoise_st, plottype='noise',
                 async_plotter=plotter)
    plot_spectra(config, weight_st, plottype='weight',
                 async_plotter=plotter)

    ssp_exit()


if __name__ == '__main__':
    main()
