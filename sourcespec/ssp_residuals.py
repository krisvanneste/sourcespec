# -*- coding: utf8 -*-
# SPDX-License-Identifier: CECILL-2.1
"""
Spectral residual routine for sourcespec.

:copyright:
    2013-2014 Claudio Satriano <satriano@ipgp.fr>,
              Agnes Chounet <chounet@ipgp.fr>

    2015-2022 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement v2.1
    (http://www.cecill.info/licences.en.html)
"""
import os
import logging
import pickle
from obspy.core import Stream
from sourcespec.ssp_spectral_model import spectral_model
from sourcespec.ssp_util import mag_to_moment
logger = logging.getLogger(__name__.split('.')[-1])


def spectral_residuals(config, spec_st, sourcepar):
    """
    Compute spectral residuals with respect to an average spectral model.

    Saves a stream of residuals to disk using pickle.
    """
    # Use weighted means
    means = sourcepar.means_weight
    params_name = ('Mw', 'fc', 't_star')
    sourcepar_mean = dict(
        zip(params_name, [means['Mw'], means['fc'], means['t_star']]))
    residuals = Stream()
    for station in set(x.stats.station for x in spec_st.traces):
        spec_st_sel = spec_st.select(station=station)
        for spec in spec_st_sel.traces:
            if spec.stats.channel[-1] != 'H':
                continue

            xdata = spec.get_freq()
            synth_mean_mag = spectral_model(xdata, **sourcepar_mean)

            res = spec.copy()
            res.data_mag = spec.data_mag - synth_mean_mag
            res.data = mag_to_moment(res.data_mag)
            residuals.append(res)

    # Save residuals as pickle file
    evid = config.hypo.evid
    res_file = os.path.join(config.options.outdir, evid + '-residuals.pickle')
    logger.info('Spectral residuals saved to: %s' % res_file)
    with open(res_file, 'wb') as fp:
        pickle.dump(residuals, fp)
