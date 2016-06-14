# -*- coding: utf-8 -*-
"""
Trace processing for sourcespec.

:copyright:
    2012 Claudio Satriano <satriano@ipgp.fr>

    2013-2014 Claudio Satriano <satriano@ipgp.fr>,
              Emanuela Matrullo <matrullo@geologie.ens.fr>

    2015-2016 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement, Version 2.1
    (http://www.cecill.info/index.en.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import logging
import numpy as np
from obspy.core import Stream
from sourcespec.ssp_setup import ssp_exit
from sourcespec.ssp_util import remove_instr_response, hypo_dist, wave_arrival


def filter_trace(config, trace):
    instrtype = trace.stats.instrtype
    if instrtype == 'acc':
        # band-pass frequencies:
        # TODO: calculate from sampling rate?
        bp_freqmin = config.bp_freqmin_acc
        bp_freqmax = config.bp_freqmax_acc
    elif instrtype == 'shortp':
        # band-pass frequencies:
        # TODO: calculate from sampling rate?
        bp_freqmin = config.bp_freqmin_shortp
        bp_freqmax = config.bp_freqmax_shortp
    elif instrtype == 'broadb':
        # band-pass frequencies:
        bp_freqmin = config.bp_freqmin_broadb
        bp_freqmax = config.bp_freqmax_broadb
    else:
        logging.warning('%s: Unknown instrument type: %s: '
                        'skipping trace' % (trace.id, instrtype))
        raise ValueError
    # remove the mean...
    trace.detrend(type='constant')
    # ...and the linear trend...
    trace.detrend(type='linear')
    nyquist = 1./(2. * trace.stats.delta)
    if bp_freqmax >= nyquist:
        bp_freqmax = nyquist * 0.999
        msg = '%s: maximum frequency for bandpass filtering ' % trace.id
        msg += 'is larger or equal to Nyquist. '
        msg += 'Setting it to %s Hz' % bp_freqmax
        logging.warning(msg)
    trace.filter(type='bandpass', freqmin=bp_freqmin, freqmax=bp_freqmax)


def _check_signal_level(config, trace):
    rms2 = np.power(trace.data, 2).sum()
    rms = np.sqrt(rms2)
    rms_min = config.rmsmin
    if rms <= rms_min:
        logging.warning('%s %s: Trace RMS smaller than %g: '
                        'skipping trace' % (trace.id, trace.stats.instrtype,
                                            rms_min))
        raise RuntimeError


def _check_clipping(config, trace):
    clip_tolerance = config.clip_tolerance
    clip_max = (1 - clip_tolerance/100.) * trace.data.max()
    clip_min = (1 - clip_tolerance/100.) * trace.data.min()
    nclips = (trace.data > clip_max).sum()
    nclips += (trace.data < clip_min).sum()
    clip_nmax = config.clip_nmax
    if float(nclips)/trace.stats.npts > clip_nmax/100.:
        logging.warning('%s %s: Trace is clipped for more than %.2f%% '
                        'with %.2f%% tolerance: skipping trace' %
                        (trace.id, trace.stats.instrtype, clip_nmax,
                         clip_tolerance))
        raise RuntimeError


def _check_sn_ratio(config, trace):
    # noise time window for s/n ratio
    trace_noise = trace.copy()
    # remove the mean...
    trace_noise.detrend(type='constant')
    # ...and the linear trend...
    trace_noise.detrend(type='linear')
    t1 = trace_noise.stats.arrivals['NN1'][1]
    t2 = trace_noise.stats.arrivals['NN2'][1]
    trace_noise.trim(starttime=t1, endtime=t2, pad=True, fill_value=0)

    # S window for s/n ratio
    trace_cutS = trace.copy()
    # remove the mean...
    trace_cutS.detrend(type='constant')
    # ...and the linear trend...
    trace_cutS.detrend(type='linear')
    t1 = trace_cutS.stats.arrivals['SN1'][1]
    t2 = trace_cutS.stats.arrivals['SN2'][1]
    trace_cutS.trim(starttime=t1, endtime=t2, pad=True, fill_value=0)

    rmsnoise2 = np.power(trace_noise.data, 2).sum()
    rmsnoise = np.sqrt(rmsnoise2)
    rmsS2 = np.power(trace_cutS.data, 2).sum()
    rmsS = np.sqrt(rmsS2)

    sn_ratio = rmsS/rmsnoise
    logging.info('%s %s: S/N: %.1f' % (trace.id, trace.stats.instrtype,
                                       sn_ratio))

    snratio_min = config.sn_min
    if sn_ratio < snratio_min:
        logging.warning('%s %s: S/N smaller than %g: skipping trace' %
                        (trace.id, trace.stats.instrtype, snratio_min))
        raise RuntimeError


def _process_trace(config, trace):
    # copy trace for manipulation
    trace_process = trace.copy()

    comp = trace_process.stats.channel
    instrtype = trace_process.stats.instrtype
    if config.ignore_vertical and comp[-1] in ['Z', '1']:
        raise RuntimeError

    # check if the trace has (significant) signal
    _check_signal_level(config, trace_process)

    # check if trace is clipped
    _check_clipping(config, trace_process)

    # Remove instrument response
    if remove_instr_response(trace_process,
                             config.correct_instrumental_response,
                             config.pre_filt) is None:
        logging.warning('%s %s: Unable to remove instrument response: '
                        'skipping trace' % (trace_process.id, instrtype))
        raise RuntimeError

    filter_trace(config, trace_process)

    # Check if the trace has significant signal to noise ratio
    _check_sn_ratio(config, trace_process)

    return trace_process


def _merge_stream(st):
    traceid = st[0].id
    # First, compute gap/overlap statistics for the whole trace.
    gaps_olaps = st.get_gaps()
    gaps = [g for g in gaps_olaps if g[6] >= 0]
    overlaps = [g for g in gaps_olaps if g[6] < 0]
    gap_duration = sum(g[6] for g in gaps)
    if gap_duration > 0:
        logging.info('%s: trace has %.3f seconds of gaps.' %
                     (traceid, gap_duration))
    overlap_duration = -1 * sum(g[6] for g in overlaps)
    if overlap_duration > 0:
        logging.info('%s: trace has %.3f seconds of overlaps.' %
                     (traceid, overlap_duration))
    # Then, compute the same statisics for the S-wave window.
    st_cut = st.copy()
    t1 = st[0].stats.arrivals['S1'][1]
    t2 = st[0].stats.arrivals['S2'][1]
    st_cut.trim(starttime=t1, endtime=t2)
    gaps_olaps = st_cut.get_gaps()
    gaps = [g for g in gaps_olaps if g[6] >= 0]
    overlaps = [g for g in gaps_olaps if g[6] < 0]
    duration = st_cut[-1].stats.endtime - st_cut[0].stats.starttime
    gap_duration = sum(g[6] for g in gaps)
    if gap_duration > duration/4:
        logging.warning('%s: Too many gaps for the selected cut '
                        'interval: skipping trace' % traceid)
        raise RuntimeError
    overlap_duration = -1 * sum(g[6] for g in overlaps)
    if overlap_duration > 0:
        logging.info('%s: S-wave window has %.3f seconds of overlaps.' %
                     (traceid, overlap_duration))
    # Finally, demean and remove gaps and overlaps.
    # Since the count value is generally huge, we need to demean twice
    # to take into account for the rounding error
    st.detrend(type='constant')
    st.detrend(type='constant')
    # Merge stream to remove gaps and overlaps
    return st.merge(fill_value=0)[0]


def _add_hypo_dist_and_arrivals(config, st):
    for trace in st:
        if hypo_dist(trace) is None:
            logging.warning('%s: Unable to compute hypocentral distance: '
                            'skipping trace' % trace.id)
            raise RuntimeError
        if config.max_epi_dist is not None and \
                trace.stats.epi_dist > config.max_epi_dist:
            logging.warning('%s: Epicentral distance (%.1f) '
                            'larger than max_epi_dist (%.1f): skipping trace' %
                            (trace.id, trace.stats.epi_dist,
                             config.max_epi_dist))
            raise RuntimeError

        p_arrival_time = wave_arrival(trace, 'P', config.p_arrival_tolerance,
                                      config.vp_tt)
        s_arrival_time = wave_arrival(trace, 'S', config.s_arrival_tolerance,
                                      config.vs_tt)
        if p_arrival_time is None or s_arrival_time is None:
            logging.warning('%s: Unable to get arrival times: '
                            'skipping trace' % trace.id)
            raise RuntimeError
        # Signal window for spectral analysis
        t1 = s_arrival_time - config.pre_s_time
        t2 = t1 + config.s_win_length
        trace.stats.arrivals['S1'] = ('S1', t1)
        trace.stats.arrivals['S2'] = ('S2', t2)
        # Noise window for spectral analysis
        t1 = p_arrival_time - config.pre_p_time
        t2 = t1 + config.s_win_length
        trace.stats.arrivals['N1'] = ('N1', t1)
        trace.stats.arrivals['N2'] = ('N2', t2)
        # Signal window for S/N ratio
        t1 = s_arrival_time - config.pre_s_time
        t2 = t1 + config.noise_win_length
        trace.stats.arrivals['SN1'] = ('SN1', t1)
        trace.stats.arrivals['SN2'] = ('SN2', t2)
        # Noise window for S/N ratio
        t1 = p_arrival_time - config.pre_p_time
        t2 = t1 + config.noise_win_length
        trace.stats.arrivals['NN1'] = ('NN1', t1)
        trace.stats.arrivals['NN2'] = ('NN2', t2)


def process_traces(config, st):
    """Remove mean, deconvolve and ignore unwanted components."""
    out_st = Stream()
    for id in set(tr.id for tr in st):
        # We still use a stream, since the trace can have
        # gaps or overlaps
        st_sel = st.select(id=id)
        try:
            _add_hypo_dist_and_arrivals(config, st_sel)
            trace = _merge_stream(st_sel)
            trace_process = _process_trace(config, trace)
            out_st.append(trace_process)
        except (ValueError, RuntimeError):
            continue

    if len(out_st) == 0:
        logging.error('No traces left! Exiting.')
        ssp_exit()

    return out_st
