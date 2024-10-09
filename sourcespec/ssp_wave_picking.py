# -*- coding: utf-8 -*-
# SPDX-License-Identifier: CECILL-2.1
"""
Wave arrival time picking for sourcespec.

:copyright:
    2012-2024 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement v2.1
    (http://www.cecill.info/licences.en.html)
"""
import logging
import numpy as np
from sourcespec.ssp_util import smooth
logger = logging.getLogger(__name__.rsplit('.', maxsplit=1)[-1])


def _refine_theo_pick_time(
        trace, phase, theo_pick_time, s_minus_p, freqmin, debug=False):
    """
    Refine theoretical pick time through the analysis of the smoothed envelope
    of the trace.
    """
    tr = trace.copy()
    # demean, highpass, normalize
    tr.detrend('demean')
    tr.filter('highpass', freq=freqmin, corners=2)
    tr.normalize()
    # smoothed envelope
    tr_smooth = tr.copy()
    tr_smooth.data = np.abs(tr_smooth.data)
    if phase == 'P':
        # Less smoothing for P phases
        npts = int(0.02*s_minus_p/tr.stats.delta)
    else:
        # More smoothing for S phases
        npts = int(0.1*s_minus_p/tr.stats.delta)
    for _ in range(10):
        tr_smooth.data = smooth(tr_smooth.data, npts)
    tr_smooth.normalize()
    # Cut the trace around the theoretical pick time
    tr_cut = tr_smooth.copy()
    cut_t0 = theo_pick_time - 0.7*s_minus_p
    cut_t1 = theo_pick_time + 0.3*s_minus_p
    tr_cut.trim(cut_t0, cut_t1)
    # cut shift is used for debug plots
    cut_shift = tr_smooth.stats.starttime - tr_cut.stats.starttime
    # cut again up to the maximum amplitude
    max_time = tr_cut.stats.starttime + tr_cut.times()[np.argmax(tr_cut.data)]
    tr_cut.trim(
        starttime=tr_cut.stats.starttime,
        endtime=max_time)
    # Remove a linear function defined by first/last sample of the trace
    tr_cut_detrend = tr_cut.copy()
    tr_cut_detrend.detrend('simple')
    refined_theo_pick_time =\
        tr_cut_detrend.stats.starttime +\
        tr_cut_detrend.times()[np.argmin(tr_cut_detrend.data)]
    # Debug plot of the trace and the refined theoretical pick time
    if debug:
        # pylint: disable=import-outside-toplevel
        import matplotlib
        mpl_backends = (
            'macosx', 'qt5agg', 'qt4agg', 'gtk3agg', 'tkagg', 'wxagg'
        )
        # Force the use of an interactive backend
        for backend in mpl_backends:
            try:
                matplotlib.use(backend, force=True)
                # pylint: disable=unused-import
                from matplotlib import pyplot  # noqa
                break
            except Exception:
                continue
        import matplotlib.pyplot as plt
        _fig, ax = plt.subplots(figsize=(10, 5))
        ax.set_ylim(-1.1, 1.1)
        ax.plot(tr.times(), tr.data, 'k', lw=0.5)
        ax.plot(tr.times(), tr_smooth.data, 'r')
        ax.plot(tr_cut.times()-cut_shift, tr_cut.data, 'b', lw=2)
        ax.plot(
            tr_cut_detrend.times()-cut_shift, tr_cut_detrend.data, 'g', lw=4)
        pick_secs = theo_pick_time - trace.stats.starttime
        refined_pick_secs = refined_theo_pick_time - trace.stats.starttime
        ax.axvline(pick_secs, color='r', linestyle='--')
        text_bbox = {'facecolor': 'white', 'edgecolor': 'none', 'alpha': 0.8}
        ax.text(
            pick_secs, 1., f'{phase}theo',
            color='r', horizontalalignment='left',
            bbox=text_bbox
        )
        ax.axvline(refined_pick_secs, color='b', linestyle='--')
        ax.text(
            refined_pick_secs, 0.7, f'{phase}auto',
            color='b', horizontalalignment='left',
            bbox=text_bbox
        )
        ax.set_title(f'{trace.id}: {phase} picking')
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Amplitude')
        plt.show()
    return refined_theo_pick_time


def refine_trace_picks(trace, freqmin, debug=False):
    """
    Refine theoretical pick times through the analysis of the smoothed
    envelope of the trace.
    """
    p_arrival_phase = trace.stats.arrivals['P'][0]
    p_arrival_time = trace.stats.arrivals['P'][1]
    s_arrival_phase = trace.stats.arrivals['S'][0]
    s_arrival_time = trace.stats.arrivals['S'][1]
    s_minus_p = s_arrival_time - p_arrival_time
    if 'theo' in p_arrival_phase:
        ref_time = _refine_theo_pick_time(
            trace, 'P', p_arrival_time, s_minus_p, freqmin,
            debug
        )
        trace.stats.arrivals['P'] = ('Pauto', ref_time)
    if 'theo' in s_arrival_phase:
        ref_time = _refine_theo_pick_time(
            trace, 'S', s_arrival_time, s_minus_p, freqmin,
            debug
        )
        trace.stats.arrivals['S'] = ('Sauto', ref_time)
