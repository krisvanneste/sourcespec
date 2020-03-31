# -*- coding: utf-8 -*-
"""
Spectral plotting routine.

:copyright:
    2012 Claudio Satriano <satriano@ipgp.fr>

    2013-2014 Claudio Satriano <satriano@ipgp.fr>,
              Emanuela Matrullo <matrullo@geologie.ens.fr>

    2015-2019 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement, Version 2.1
    (http://www.cecill.info/index.en.html)
"""
from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import os
import math
import logging
from sourcespec.ssp_util import spec_minmax, moment_to_mag, mag_to_moment
from sourcespec.ssp_version import get_git_version
logger = logging.getLogger(__name__.split('.')[-1])

synth_colors = [
    '#201F1F',
    '#94F75B',
    '#3EC2AA',
    '#FECC38',
    '#FC4384',
]


def _import_mpl(config):
    import matplotlib
    matplotlib.rcParams['pdf.fonttype'] = 42  # to edit text in Illustrator
    # Reduce logging level for Matplotlib to avoid DEBUG messages
    mpl_logger = logging.getLogger('matplotlib')
    mpl_logger.setLevel(logging.WARNING)
    global plt
    import matplotlib.pyplot as plt
    if not config.PLOT_SHOW:
        plt.switch_backend('Agg')
    global PdfPages
    from matplotlib.backends.backend_pdf import PdfPages
    global transforms
    global patches
    global PathEffects
    import matplotlib.transforms as transforms
    import matplotlib.patches as patches
    import matplotlib.patheffects as PathEffects


def _nplots(spec_st, specnoise_st, maxlines, ncols, plottype):
    # Determine the number of plots and axes min and max:
    nplots = 0
    moment_minmax = None
    freq_minmax = None
    for station in set(x.stats.station for x in spec_st.traces):
        spec_st_sel = spec_st.select(station=station)
        if specnoise_st:
            specnoise_sel = specnoise_st.select(station=station)
            spec_st_sel += specnoise_sel
        for spec in spec_st_sel.traces:
            moment_minmax, freq_minmax =\
                spec_minmax(spec.data, spec.get_freq(),
                            moment_minmax, freq_minmax)
        # 'code' is band+instrument code
        for code in set(x.stats.channel[0:2] for x in spec_st_sel):
            nplots += 1
    nlines = int(math.ceil(nplots/ncols))
    if nlines > maxlines:
        nlines = maxlines
    if plottype != 'weight':
        moment_minmax[1] *= 10
        mag_minmax = moment_to_mag(moment_minmax)
    else:
        mag_minmax = None
    return nlines, ncols, freq_minmax, moment_minmax, mag_minmax


def _make_fig(config, nlines, ncols, freq_minmax, moment_minmax, mag_minmax,
              stack_plots, plottype):
    if nlines <= 3 or stack_plots:
        figsize = (16, 9)
    else:
        figsize = (16, 18)
    fig = plt.figure(figsize=figsize)
    # Create an invisible axis and use it for title and footer
    ax0 = fig.add_subplot(111, label='ax0')
    ax0.set_axis_off()
    # Add event information as a title
    hypo = config.hypo
    textstr = 'evid: {} lon: {:.3f} lat: {:.3f} depth: {:.1f} km ' +\
              'time: {}'
    textstr = textstr.format(
        hypo.evid, hypo.longitude, hypo.latitude, hypo.depth,
        hypo.origin_time.format_iris_web_service())
    ax0.text(0., 1.06, textstr, fontsize=12,
             ha='left', va='top', transform=ax0.transAxes)
    if config.options.evname is not None:
        textstr = config.options.evname
        ax0.text(0., 1.1, textstr, fontsize=14,
                 ha='left', va='top', transform=ax0.transAxes)
    # Add code information at the figure bottom
    textstr = 'SourceSpec v{} '.format(get_git_version())
    if not stack_plots:
        textstr += '– {} {}\n'.format(
            config.end_of_run.strftime('%Y-%m-%d %H:%M:%S'),
            config.end_of_run_tz)
    ax0.text(1., -0.1, textstr, fontsize=10,
             ha='right', va='top', transform=ax0.transAxes)
    axes = []
    for n in range(nlines*ncols):
        plotn = n+1
        # ax1 has moment units (or weight)
        if plotn == 1:
            if stack_plots:
                ax = fig.add_subplot(1, 1, 1, label='ax')
            else:
                ax = fig.add_subplot(nlines, ncols, plotn)
        else:
            if not stack_plots:
                ax = fig.add_subplot(nlines, ncols, plotn,
                                     sharex=axes[0][0], sharey=axes[0][0])
        ax.set_xlim(freq_minmax)
        ax.set_ylim(moment_minmax)
        ax.grid(True, which='both', linestyle='solid', color='#DDDDDD',
                zorder=0)
        ax.set_axisbelow(True)
        [t.set_visible(False) for t in ax.get_xticklabels()]
        [t.set_visible(False) for t in ax.get_yticklabels()]
        ax.tick_params(width=2)  # FIXME: ticks are below grid lines!
        # ax2 has magnitude units
        if plottype != 'weight':
            if ((stack_plots and plotn == 1) or not stack_plots):
                ax2 = ax.twinx()
                ax2.set_ylim(mag_minmax)
                [t.set_visible(False) for t in ax2.get_xticklabels()]
                for tick in ax2.yaxis.get_major_ticks():
                    tick.set_pad(-2)
                    tick.label2.set_horizontalalignment('right')
                ax2.yaxis.set_tick_params(width=0)
        else:
            ax2 = None
        axes.append((ax, ax2))
    fig.subplots_adjust(hspace=.025, wspace=.03)
    return fig, axes, ax0


def _savefig(config, plottype, figures, async_plotter):
    evid = config.hypo.evid
    if plottype == 'regular':
        suffix = '.ssp.'
        message = 'Spectral'
    elif plottype == 'weight':
        suffix = '.sspweight.'
        message = 'Weight'
    figfile_base = os.path.join(config.options.outdir, evid + suffix)
    fmt = config.PLOT_SAVE_FORMAT
    if fmt == 'pdf_multipage':
        figfile = figfile_base + 'pdf'
        with PdfPages(figfile) as pdf:
            for fig in figures:
                pdf.savefig(fig)
            # Temporary commented out (see below)
            # if not config.PLOT_SHOW:
            #     fig.clf()
        logger.info(message + ' plots saved to: ' + figfile)
        return
    for n, fig in enumerate(figures):
        if len(figures) == 1:
            figfile = figfile_base + fmt
        else:
            figfile = figfile_base + '{:02d}.{}'.format(n, fmt)
        if config.PLOT_SHOW or (async_plotter is None):
            fig.savefig(figfile, bbox_inches='tight')
        else:
            async_plotter.save(fig.canvas, figfile, bbox_inches='tight')
        logger.info(message + ' plots saved to: ' + figfile)
        # Commenting this out, since it throws a warning on recent versions
        # of Matplotlib (https://github.com/matplotlib/matplotlib/issues/9970)
        # By the way, do we really need to call clf()?
        # if not config.PLOT_SHOW:
        #     fig.clf()


def _add_labels(axes, plotn, ncols, plottype):
    # Show the x-labels only for the last "ncols" plots
    n0 = plotn-ncols if plotn-ncols > 0 else 0
    for ax, ax2 in axes[n0:plotn]:
        [t.set_visible(True) for t in ax.get_xticklabels()]
        ax.set_xlabel('Frequency (Hz)')
    # Show the y-labels only for the first column
    for i in range(0, len(axes)+ncols, ncols):
        try:
            ax = axes[i][0]
        except IndexError:
            continue
        try:
            # for ax2 we take the last column
            ax2 = axes[i-1][1]
        except IndexError:
            continue
        [t.set_visible(True) for t in ax.get_yticklabels()]
        ax.set_ylabel('Weight')
        if plottype != 'weight':
            ax.set_ylabel('Seismic moment (Nm)')
            if ax2:
                [t.set_visible(True) for t in ax2.get_yticklabels()]
                ax2.set_ylabel('Magnitude')
    # still some work to do on the last plot
    ax, ax2 = axes[plotn-1]
    if ax2:
        [t.set_visible(True) for t in ax2.get_yticklabels()]
        ax2.set_ylabel('Magnitude')


def _color_lines(config, orientation, plotn, stack_plots):
    if orientation in config.vertical_channel_codes:
        color = 'purple'
        linestyle = 'solid'
        linewidth = 1
    if orientation in config.horizontal_channel_codes_1:
        color = 'green'
        linestyle = 'solid'
        linewidth = 1
    if orientation in config.horizontal_channel_codes_2:
        color = 'blue'
        linestyle = 'solid'
        linewidth = 1
    if orientation == 'H':
        color = 'red'
        linestyle = 'solid'
        linewidth = 1
    if orientation == 'S':
        if stack_plots:
            color = synth_colors[(plotn-1) % len(synth_colors)]
        else:
            color = 'black'
        linestyle = 'solid'
        linewidth = 2
    if orientation == 's':
        color = 'gray'
        linestyle = 'solid'
        linewidth = 1
    if orientation == 't':
        color = 'gray'
        linestyle = 'dashed'
        linewidth = 1
    return color, linestyle, linewidth


def _add_legend(config, ax0, spec_st, specnoise_st, stack_plots, plottype):
    # check the available channel codes
    channel_codes = set(s.stats.channel[-1] for s in spec_st)
    # Set ax limit, so that the fake plot lines are hidden below
    # the spectral plots
    ax0.set_xlim(-10, 10000)
    ax0.set_ylim(-10, 10000)
    ncol0 = 0
    handles0 = []
    if 'H' in channel_codes:
        ncol0 += 1
        orientation = 'H'
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        if plottype == 'weight':
            label = 'Weight'
        else:
            label = 'Root sum of squares'
        _h, = ax0.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles0.append(_h)
    Z_codes = sorted(
        c for c in channel_codes if c in config.vertical_channel_codes)
    if Z_codes:
        ncol0 += 1
        orientation = Z_codes[0]
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = ', '.join(Z_codes)
        _h, = ax0.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles0.append(_h)
    H1_codes = sorted(
        c for c in channel_codes if c in config.horizontal_channel_codes_1)
    if H1_codes:
        ncol0 += 1
        orientation = H1_codes[0]
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = ', '.join(H1_codes)
        _h, = ax0.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles0.append(_h)
    H2_codes = sorted(
        c for c in channel_codes if c in config.horizontal_channel_codes_2)
    if H2_codes:
        ncol0 += 1
        orientation = H2_codes[0]
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = ', '.join(H2_codes)
        _h, = ax0.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles0.append(_h)
    if specnoise_st:
        ncol0 += 1
        linewidth = 2
        color = 'gray'
        linestyle = ':'
        label = 'Noise'
        _h, = ax0.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles0.append(_h)
    # Create a second axis for a second legend
    ax1 = ax0.get_figure().add_subplot(111, label='ax1', zorder=-1)
    ax1.set_axis_off()
    # Set ax limit, so that the fake plot lines are hidden below
    # the spectral plots
    ax1.set_xlim(-10, 10000)
    ax1.set_ylim(-10, 10000)
    ncol1 = 0
    handles1 = []
    if 'S' in channel_codes:
        ncol1 += 1
        orientation = 'S'
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = 'Brune fit'
        _h, = ax1.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles1.append(_h)
    if 's' in channel_codes:
        ncol1 += 1
        orientation = 's'
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = 'Brune fit no att.'
        _h, = ax1.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles1.append(_h)
    if 't' in channel_codes:
        ncol1 += 1
        orientation = 't'
        color, linestyle, linewidth =\
            _color_lines(config, orientation, 0, stack_plots)
        linewidth = 2
        label = 'Brune fit no fc'
        _h, = ax1.plot(range(2), linestyle=linestyle, linewidth=linewidth,
                       color=color, label=label)
        handles1.append(_h)
    # Put the two legends on the two axes
    legend0_y = legend1_y = -0.127
    if handles0 and handles1:
        legend0_y = -0.111
        legend1_y = -0.147
    if handles0:
        ax0.legend(handles=handles0, bbox_to_anchor=(0, legend0_y),
                   loc='lower left', borderaxespad=0, ncol=ncol0)
    if handles1:
        ax1.legend(handles=handles1, bbox_to_anchor=(0, legend1_y),
                   loc='lower left', borderaxespad=0, ncol=ncol1)


def plot_spectra(config, spec_st, specnoise_st=None, ncols=4,
                 stack_plots=False, plottype='regular', async_plotter=None):
    """
    Plot spectra for signal and noise.

    Display to screen and/or save to file.
    """
    # Check config, if we need to plot at all
    if not config.PLOT_SHOW and not config.PLOT_SAVE:
        return
    _import_mpl(config)

    nlines, ncols, freq_minmax, moment_minmax, mag_minmax =\
        _nplots(spec_st, specnoise_st,
                config.plot_spectra_maxrows, ncols, plottype)
    figures = []
    fig, axes, ax0 = _make_fig(
        config, nlines, ncols, freq_minmax, moment_minmax, mag_minmax,
        stack_plots, plottype)
    figures.append(fig)

    # Path effect to contour text in white
    path_effects = [PathEffects.withStroke(linewidth=3, foreground="white")]

    # Plot!
    plotn = 0
    stalist = sorted(set(
        (t.stats.hypo_dist, t.stats.station, t.stats.channel[0:2])
        for t in spec_st))
    for t in stalist:
        plotn += 1
        # 'code' is band+instrument code
        _, station, code = t
        spec_st_sel = spec_st.select(station=station)
        if plotn > nlines*ncols:
            # Add lables and legend before making a new figure
            _add_labels(axes, plotn-1, ncols, plottype)
            _add_legend(
                config, ax0, spec_st, specnoise_st, stack_plots, plottype)
            fig, axes, ax0 = _make_fig(
                config, nlines, ncols,
                freq_minmax, moment_minmax, mag_minmax,
                stack_plots, plottype)
            figures.append(fig)
            plotn = 1
        ax_text = False
        ax, ax2 = axes[plotn-1]
        for spec in spec_st_sel.traces:
            if spec.stats.channel[0:2] != code:
                continue
            orientation = spec.stats.channel[2]
            color, linestyle, linewidth =\
                _color_lines(config, orientation, plotn, stack_plots)
            if plottype == 'regular':
                ax.loglog(spec.get_freq(), spec.data, color=color,
                          linestyle=linestyle, linewidth=linewidth,
                          zorder=20)
                if orientation == 'S':
                    fc = spec.stats.par['fc']
                    if 'par_err' in spec.stats.keys():
                        fc_err = spec.stats.par_err['fc']
                        fc_min = fc-fc_err
                        if fc_min < 0:
                            fc_min = 0.01
                        ax.axvspan(fc_min, fc+fc_err, color='#bbbbbb',
                                   alpha=0.3, zorder=1)
                    ax.axvline(fc, color='#999999',
                               linewidth=2., zorder=1)
                    Mw = spec.stats.par['Mw']
                    if 'par_err' in spec.stats.keys():
                        Mw_err = spec.stats.par_err['Mw']
                        ax2.axhspan(Mw-Mw_err, Mw+Mw_err, color='#bbbbbb',
                                    alpha=0.3, zorder=1)
            elif plottype == 'weight':
                ax.semilogx(spec.get_freq(), spec.data, color=color,
                            zorder=20)
            else:
                raise ValueError('Unknown plot type: %s' % plottype)
            # leg = ax.legend(('N', 'E', 'H'), 'lower right')

            if specnoise_st:
                if spec.stats.channel[2] != 'S':
                    specid = spec.get_id()
                    try:
                        sp_noise = specnoise_st.select(id=specid)[0]
                    except IndexError:
                        continue
                    orientation = sp_noise.stats.channel[2]
                    ax.loglog(sp_noise.get_freq(), sp_noise.data,
                              linestyle=':', linewidth=linewidth,
                              color=color, zorder=20)

            if not ax_text:
                ax_text = '%s %s' % (spec.id[0:-1], spec.stats.instrtype)
                if stack_plots:
                    text_y = 0.05 + (plotn-1) * 0.05
                else:
                    text_y = 0.15
                    color = 'black'
                    ax_text += '\n%.1f km (%.1f km)' % (
                                                    spec.stats.hypo_dist,
                                                    spec.stats.epi_dist)
                ax.text(0.05, text_y, ax_text,
                        horizontalalignment='left',
                        verticalalignment='bottom',
                        color=color,
                        transform=ax.transAxes,
                        zorder=50,
                        path_effects=path_effects)
                ax_text = True

            if orientation == 'S':
                if stack_plots:
                    text_y2 = text_y - 0.02
                else:
                    text_y2 = 0.03
                    color = 'black'
                fc = spec.stats.par['fc']
                Mw = spec.stats.par['Mw']
                Mo = mag_to_moment(Mw)
                t_star = spec.stats.par['t_star']
                if 'par_err' in spec.stats.keys():
                    fc_err = spec.stats.par_err['fc']
                    Mw_err = spec.stats.par_err['Mw']
                    t_star_err = spec.stats.par_err['t_star']
                else:
                    fc_err = Mw_err = t_star_err = 0.
                ax.text(0.05, text_y2,
                        'Mo: %.2g Mw: %.2f±%.2f\n'
                        'fc: %.2f±%.2f Hz t*: %.2f±%.2fs' %
                        (Mo, Mw, Mw_err, fc, fc_err, t_star, t_star_err),
                        horizontalalignment='left',
                        verticalalignment='bottom',
                        color=color,
                        fontsize=9,
                        transform=ax.transAxes,
                        zorder=50,
                        path_effects=path_effects)

    # Add lables and legend for the last figure
    _add_labels(axes, plotn, ncols, plottype)
    _add_legend(config, ax0, spec_st, specnoise_st, stack_plots, plottype)
    # Turn off the unused axes
    for ax, ax2 in axes[plotn:]:
        ax.set_axis_off()
        if ax2:
            ax2.set_axis_off()

    if config.PLOT_SHOW:
        plt.show()
    if config.PLOT_SAVE:
        _savefig(config, plottype, figures, async_plotter)
