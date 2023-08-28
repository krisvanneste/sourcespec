
# -*- coding: utf-8 -*-
# SPDX-License-Identifier: CECILL-2.1
"""
Table definitions for SourceSpec database.

:copyright:
    2013-2023 Claudio Satriano <satriano@ipgp.fr>
:license:
    CeCILL Free Software License Agreement v2.1
    (http://www.cecill.info/licences.en.html)
"""
# Current DB version
DB_VERSION = 2

# Table definitions
STATIONS_TABLE = {
    'stid': 'TEXT',
    'evid': 'TEXT',
    'runid': 'TEXT',
    'Mo': 'REAL',
    'Mo_err_minus': 'REAL',
    'Mo_err_plus': 'REAL',
    'Mo_is_outlier': 'INT',
    'Mw': 'REAL',
    'Mw_err_minus': 'REAL',
    'Mw_err_plus': 'REAL',
    'Mw_is_outlier': 'INT',
    'fc': 'REAL',
    'fc_err_minus': 'REAL',
    'fc_err_plus': 'REAL',
    'fc_is_outlier': 'INT',
    't_star': 'REAL',
    't_star_err_minus': 'REAL',
    't_star_err_plus': 'REAL',
    't_star_is_outlier': 'INT',
    'Qo': 'REAL',
    'Qo_err_minus': 'REAL',
    'Qo_err_plus': 'REAL',
    'Qo_is_outlier': 'INT',
    'bsd': 'REAL',
    'bsd_err_minus': 'REAL',
    'bsd_err_plus': 'REAL',
    'bsd_is_outlier': 'INT',
    'ra': 'REAL',
    'ra_err_minus': 'REAL',
    'ra_err_plus': 'REAL',
    'ra_is_outlier': 'INT',
    'Er': 'REAL',
    'Er_err_minus': 'REAL',
    'Er_err_plus': 'REAL',
    'Er_is_outlier': 'INT',
    'sigma_a': 'REAL',
    'sigma_a_err_minus': 'REAL',
    'sigma_a_err_plus': 'REAL',
    'sigma_a_is_outlier': 'INT',
    'dist': 'REAL',
    'azimuth': 'REAL',
}
STATIONS_PRIMARY_KEYS = ['stid', 'evid', 'runid']

EVENTS_TABLE = {
    'evid': 'TEXT',
    'runid': 'TEXT',
    'orig_time': 'REAL',
    'lon': 'REAL',
    'lat': 'REAL',
    'depth': 'REAL',
    'vp': 'REAL',
    'vs': 'REAL',
    'rho': 'REAL',
    'nobs': 'INTEGER',
    'nsigma': 'REAL',
    'mid_pct': 'REAL',
    'lower_pct': 'REAL',
    'upper_pct': 'REAL',
    'Mo_mean': 'REAL',
    'Mo_mean_err_minus': 'REAL',
    'Mo_mean_err_plus': 'REAL',
    'Mo_wmean': 'REAL',
    'Mo_wmean_err_minus': 'REAL',
    'Mo_wmean_err_plus': 'REAL',
    'Mo_pctl': 'REAL',
    'Mo_pctl_err_minus': 'REAL',
    'Mo_pctl_err_plus': 'REAL',
    'Mw_mean': 'REAL',
    'Mw_mean_err_minus': 'REAL',
    'Mw_mean_err_plus': 'REAL',
    'Mw_wmean': 'REAL',
    'Mw_wmean_err_minus': 'REAL',
    'Mw_wmean_err_plus': 'REAL',
    'Mw_pctl': 'REAL',
    'Mw_pctl_err_minus': 'REAL',
    'Mw_pctl_err_plus': 'REAL',
    'fc_mean': 'REAL',
    'fc_mean_err_minus': 'REAL',
    'fc_mean_err_plus': 'REAL',
    'fc_wmean': 'REAL',
    'fc_wmean_err_minus': 'REAL',
    'fc_wmean_err_plus': 'REAL',
    'fc_pctl': 'REAL',
    'fc_pctl_err_minus': 'REAL',
    'fc_pctl_err_plus': 'REAL',
    't_star_mean': 'REAL',
    't_star_mean_err_minus': 'REAL',
    't_star_mean_err_plus': 'REAL',
    't_star_wmean': 'REAL',
    't_star_wmean_err_minus': 'REAL',
    't_star_wmean_err_plus': 'REAL',
    't_star_pctl': 'REAL',
    't_star_pctl_err_minus': 'REAL',
    't_star_pctl_err_plus': 'REAL',
    'Qo_mean': 'REAL',
    'Qo_mean_err_minus': 'REAL',
    'Qo_mean_err_plus': 'REAL',
    'Qo_wmean': 'REAL',
    'Qo_wmean_err_minus': 'REAL',
    'Qo_wmean_err_plus': 'REAL',
    'Qo_pctl': 'REAL',
    'Qo_pctl_err_minus': 'REAL',
    'Qo_pctl_err_plus': 'REAL',
    'ra_mean': 'REAL',
    'ra_mean_err_minus': 'REAL',
    'ra_mean_err_plus': 'REAL',
    'ra_wmean': 'REAL',
    'ra_wmean_err_minus': 'REAL',
    'ra_wmean_err_plus': 'REAL',
    'ra_pctl': 'REAL',
    'ra_pctl_err_minus': 'REAL',
    'ra_pctl_err_plus': 'REAL',
    'bsd_mean': 'REAL',
    'bsd_mean_err_minus': 'REAL',
    'bsd_mean_err_plus': 'REAL',
    'bsd_wmean': 'REAL',
    'bsd_wmean_err_minus': 'REAL',
    'bsd_wmean_err_plus': 'REAL',
    'bsd_pctl': 'REAL',
    'bsd_pctl_err_minus': 'REAL',
    'bsd_pctl_err_plus': 'REAL',
    'Er_mean': 'REAL',
    'Er_mean_err_minus': 'REAL',
    'Er_mean_err_plus': 'REAL',
    'Er_wmean': 'REAL',
    'Er_wmean_err_minus': 'REAL',
    'Er_wmean_err_plus': 'REAL',
    'Er_pctl': 'REAL',
    'Er_pctl_err_minus': 'REAL',
    'Er_pctl_err_plus': 'REAL',
    'sigma_a_mean': 'REAL',
    'sigma_a_mean_err_minus': 'REAL',
    'sigma_a_mean_err_plus': 'REAL',
    'sigma_a_wmean': 'REAL',
    'sigma_a_wmean_err_minus': 'REAL',
    'sigma_a_wmean_err_plus': 'REAL',
    'sigma_a_pctl': 'REAL',
    'sigma_a_pctl_err_minus': 'REAL',
    'sigma_a_pctl_err_plus': 'REAL',
    'Ml_mean': 'REAL',
    'Ml_mean_err_minus': 'REAL',
    'Ml_mean_err_plus': 'REAL',
    'Ml_wmean': 'REAL',
    'Ml_wmean_err_minus': 'REAL',
    'Ml_wmean_err_plus': 'REAL',
    'Ml_pctl': 'REAL',
    'Ml_pctl_err_minus': 'REAL',
    'Ml_pctl_err_plus': 'REAL',
    'run_completed': 'TEXT',
    'sourcespec_version': 'TEXT',
    'author_name': 'TEXT',
    'author_email': 'TEXT',
    'agency_full_name': 'TEXT',
    'agency_short_name': 'TEXT',
    'agency_url': 'TEXT'
}
EVENTS_PRIMARY_KEYS = ['evid', 'runid']
