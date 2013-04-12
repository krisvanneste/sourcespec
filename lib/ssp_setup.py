# -*- coding: utf-8 -*-
# ssp_setup.py
#
# Setup functions for source_spec
# (c) 2012 Claudio Satriano <satriano@ipgp.fr>
# (c) 2013 Claudio Satriano <satriano@ipgp.fr>,
#          Emanuela Matrullo <matrullo@geologie.ens.fr>
import sys
import os
import logging
from imp import load_source
from optparse import OptionParser
from datetime import datetime

if sys.stdout.isatty():
    try:
        # ipython >= 0.11
        from IPython.frontend.terminal.embed import InteractiveShellEmbed
        ipshell = InteractiveShellEmbed()
    except ImportError:
        try:
            # ipython < 0.11
            from IPython.Shell import IPShellEmbed
            ipshell = IPShellEmbed()
        except ImportError:
            # Give up!
            ipshell = None
else:
    ipshell = None

DEBUG=False
def dprint(string):
    if DEBUG:
        sys.stderr.write(string)
        sys.stderr.write('\n')

def __parse_args_source_spec():
    usage = 'usage: %prog [options] trace_file(s) | trace_dir'

    parser = OptionParser(usage=usage);
    parser.add_option('-c', '--configfile', dest='config_file', action='store', default='config.py',
            help='Load configuration from FILE (default: config.py)', metavar='DIR | FILE')
    parser.add_option('-H', '--hypocenter', dest='hypo_file', action='store', default=None,
            help='Get hypocenter information from FILE', metavar='FILE')
    parser.add_option('-p', '--pickfile', dest='pick_file', action='store', default=None,
            help='Get picks from FILE', metavar='FILE')
    parser.add_option('-e', '--evid', dest='evid', action='store', default=None,
            help='Get evid from catalog', metavar='EVID')
    parser.add_option('-o', '--outdir', dest='outdir', action='store', default='sspec_out',
            help='Save output to OUTDIR (default: sspec_out)', metavar='OUTDIR')

    (options, args) = parser.parse_args()
    if len(args) < 1:
        parser.print_usage(file=sys.stderr)
        sys.stderr.write("\tUse '-h' for help\n\n")
        sys.exit(1)

    return options, args

def __parse_args_source_model():
    usage = 'usage: %prog [options] trace_file(s) | trace_dir'

    parser = OptionParser(usage=usage);
    parser.add_option('-c', '--configfile', dest='config_file', action='store', default='config.py',
            help='Load configuration from FILE (default: config.py)', metavar='DIR | FILE')
    parser.add_option('-H', '--hypocenter', dest='hypo_file', action='store', default=None,
            help='Get hypocenter information from FILE', metavar='FILE')
    parser.add_option('-e', '--evid', dest='evid', action='store', default=None,
            help='Get evid from catalog', metavar='EVID')
    parser.add_option('-f', '--fmin', dest='fmin', action='store', default='0.01',
            help='Minimum frequency', metavar='FMIN')
    parser.add_option('-F', '--fmax', dest='fmax', action='store', default='50.0',
            help='Maximum frequency', metavar='FMAX')
    parser.add_option('-k', '--fc', dest='fc', action='store', default='10.0',
            help='Corner frequency', metavar='FC')
    parser.add_option('-m', '--mag', dest='mag', action='store', default='2.0',
            help='Moment magnitude', metavar='Mw')
    parser.add_option('-t', '--tstar', dest='t_star', action='store', default='0.0',
            help='T-star (attenuation)', metavar='T')

    (options, args) = parser.parse_args()
    if len(args) < 0:
        parser.print_usage(file=sys.stderr)
        sys.stderr.write("\tUse '-h' for help\n\n")
        sys.exit(1)

    options.fmin = float(options.fmin)
    options.fmax = float(options.fmax)
    options.fc = map(float, options.fc.rstrip(',').split(','))
    options.mag = map(float, options.mag.rstrip(',').split(','))
    options.t_star = map(float, options.t_star.rstrip(',').split(','))

    oplist = [options.fc, options.mag, options.t_star]
    # Add trailing "None" to shorter lists and zip:
    oplist = map(None, *oplist)
    # Unzip and convert tuple to lists:
    oplist = map(list, zip(*oplist))
    for l in oplist:
        for n, x in enumerate(l):
            if x == None:
                l[n] = l[n-1]
    options.fc, options.mag, options.t_star = oplist

    # Add unused options (required by source_spec):
    options.pick_file = None

    return options, args

def configure(progname='source_spec'):
    global DEBUG
    if progname == 'source_spec':
        options, args = __parse_args_source_spec()
    elif progname == 'source_model':
        options, args = __parse_args_source_model()
    else:
        sys.stderr.write('Wrong program name: %s\n' % progname)
        sys.exit(1)

    config_file = options.config_file
    try:
        config = load_source('config', config_file)
        DEBUG  = config.DEBUG
    except:
        sys.stderr.write('Unable to open file: %s\n' % config_file)
        sys.exit(1)

    # check if optional parameters are there:
    try:
        config.dataless
    except AttributeError:
        config.dataless = None
    try:
        config.paz
    except AttributeError:
        config.paz = None
    try:
        config.traceids
    except AttributeError:
        config.traceids = None
    try:
        config.pickle_catalog
    except AttributeError:
        config.pickle_catalog = None
    try:
        config.pickle_classpath
    except AttributeError:
        config.pickle_classpath = None


    #add options and args to config:
    config.__dict__['options'] = options
    config.__dict__['args'] = args

    # Remove the bytecoded version of the config file,
    # generated by "load_source"
    try: os.remove("%sc" % config_file)
    except: pass
    return config

oldlogfile=None
def setup_logging(config, basename=None):
    global oldlogfile
    # Create outdir 
    if not os.path.exists(config.options.outdir):
        os.makedirs(config.options.outdir)

    if basename:
        logfile = '%s/%s.ssp.log' % (config.options.outdir, basename)
    else:
        datestring = datetime.now().strftime('%Y%m%d_%H%M%S')
        logfile = '%s/%s.ssp.log' % (config.options.outdir, datestring)

    log=logging.getLogger()
    if oldlogfile:
        hdlrs = log.handlers[:]
        for hdlr in hdlrs:
            log.removeHandler(hdlr)
        os.rename(oldlogfile, logfile)
        filemode = 'a'
    else:
        filemode = 'w'
    oldlogfile = logfile

    #logging.basicConfig(
    #        level=logging.DEBUG,
    #        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
    #        filename=logfile,
    #        filemode='w'
    #        )

    # captureWarnings is not supported in old versions of python
    try: logging.captureWarnings(True)
    except: pass
    log.setLevel(logging.DEBUG)
    filehand = logging.FileHandler(filename=logfile, mode=filemode)
    filehand.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
    filehand.setFormatter(formatter)
    log.addHandler(filehand)

    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    log.addHandler(console)

    if not basename:
        logging.debug('source_spec START')
        # write running arguments
        logging.debug('Running arguments:')
        logging.debug(' '.join(sys.argv))

def ssp_exit(retval=0):
    logging.debug('source_spec END')
    logging.shutdown()
    sys.exit(retval)
