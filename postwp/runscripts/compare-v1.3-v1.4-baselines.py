##############################################################################################################
# This script runs compare_versions to compare baseline between v1.3 and v1.4.
#
# Humna Awan: humna.awan@rutgers.edu
#
##############################################################################################################
import time
import os

from helper_compare_versions_misc_metrics import compare_versions

# set up
start_time = time.time()
nside = 64 # not the most high resolution but its faster..

yr_cut = 10
outdir = '/global/homes/a/awan/LSST/lsstRepos/ObsStrat/postwp/results-plots+/compare-baseline_v1.3-v1.4/'
os.makedirs(outdir, exist_ok=True)

dbpath_dict = {}
dbpath_dict['v1.4'] = '/global/cscratch1/sd/awan/dbs_post_wp_v3/baseline_v1.4_10yrs.db' #footprint_big_sky_dustv1.4_10yrs.db'
dbpath_dict['v1.3'] = '/global/cscratch1/sd/awan/dbs_post_wp_v2/baseline_v1.3_10yrs.db' #big_sky_dust_v1.3_10yrs.db'

dbname = 'baseline'

reference_version = 'v1.3'
order_of_versions = ['v1.3', 'v1.4']

ilims = {'v1.3': 26.0,  'v1.4': 25.9}

ebvlims = 0.2

# run the code
compare_versions(outdir=outdir, dbpath_dict=dbpath_dict, dbname=dbname,
                 reference_version=reference_version, order_of_versions=order_of_versions,
                 nside=nside, yr_cut=yr_cut, ilims=ilims, ebvlims=ebvlims)

print('## time taken: %.f min' % ((time.time() - start_time) / 60.))