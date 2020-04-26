##############################################################################################################
# This function runs a series of metrics for the specified versions of a given db and plots things out
# for comparisons.
#
# Humna Awan: humna.awan@rutgers.edu
#
##############################################################################################################
import os
import numpy as np
import healpy as hp

import lsst.sims.maf.maps as maps
import lsst.sims.maf.db as db
import lsst.sims.maf.metrics as metrics
import lsst.sims.maf.slicers as slicers
import lsst.sims.maf.metricBundles as metricBundles
from mafContrib.lssmetrics.egFootprintMetric import egFootprintMetric

import matplotlib.pyplot as plt
import matplotlib as mpl

fontsize = 18
rcparams = {}
rcparams['figure.figsize'] = (10, 6)
rcparams['axes.labelsize'] = fontsize
rcparams['legend.fontsize'] = fontsize-4
rcparams['axes.titlesize'] = fontsize
rcparams['axes.linewidth'] = 2
rcparams['axes.grid'] = True
for axis in ['x', 'y']:
    rcparams['%stick.labelsize'%axis] = fontsize-2
    rcparams['%stick.direction'%axis] = 'in'
    rcparams['%stick.major.size'%axis] = 5.5
    rcparams['%stick.minor.size'%axis] =  3.5
    rcparams['%stick.major.width'%axis] = 2
    rcparams['%stick.minor.width'%axis] = 1.5
rcparams['xtick.top'] = True
rcparams['ytick.right'] = True
for key in rcparams: mpl.rcParams[key] = rcparams[key]
##########################################################################

__all__ = ['compare_versions', 'plot_to_compare']

##########################################################################
def compare_versions(outdir, dbpath_dict, dbname, reference_version, order_of_versions,
                     nside=64, yr_cut=10, ilims=26.0, ebvlims=0.2, ):
    """

    This function runs a series of (simple) metrics to compare specified versions of a
    given database, and creates plots to compare things for all the bands.

    Required Inputs
    ---------------
    * outdir: str: path to the folder where outputs should be stored.
    * dbpath_dict: dict: dictionary with key=version-tags and values=full paths
                         to the respective dbs.
    * dbname: str: tag to identify the outputs.
    * reference_version: str: version_key with which to compare everything against
    * order_of_versions: list of str: order of version_keys. reference_version must be
                                      the first.

    Optional Inputs
    ---------------
    * nside: int: HEALpix resolution parameter. Default: 64
    * yr_cut: int/float: year cut to restrict analysis to. Default: 10
    * ilims: limiting i-band pt-source magnitude
             if float: will apply the same magcut to all.
             if dict: keys should be version-tags (as in dbpath_dict) and
                      values should be the respective ilim
             Default: 26.0
    * ebvlims: limiting ebv
             if float: will apply the same cut to all.
             if dict: keys should be version-tags (as in dbpath_dict) and
                      values should be the respective ebvlim
             Default: 0.2

    """
    versions = order_of_versions
    # check if ilims is ok
    lim_mag_i_dict = {}
    if isinstance(ilims, float):
        for version_key in versions:
            lim_mag_i_dict[version_key] = ilims
    elif isinstance(ilims, dict):
        for version_key in versions:
            if version_key not in ilims:
                raise ValueError('%s missing in input ilims dict.' % version_key)
        lim_mag_i_dict = ilims
    else:
        raise ValueError('somethings wrong. expect ilims to be either float or dict but have %s: %s' % (type(ilims), ilims))

    lim_ebv_dict = {}
    # check if ebvlims is ok
    if isinstance(ebvlims, float):
        for version_key in versions:
            lim_ebv_dict[version_key] = ebvlims
    elif isinstance(ebvlims, dict):
        for version_key in versions:
            if version_key not in ilims:
                raise ValueError('%s missing in input ilims dict.' % version_key)
        lim_ebv_dict = ebvlims
    else:
        raise ValueError('somethings wrong. expect ebvlims to be either float or dict but have %s: %s' % (type(ebvlims), ebvlims))

    # check if reference version is ok
    if reference_version != order_of_versions[0]:
        raise ValueError('reference_version must be the first in order_of_versions: input order_of_versions = %s' % order_of_versions)

    # okay inputs are fine.
    print('## running compare versions for %s' % versions)

    bands = ['u', 'g', 'r', 'i', 'z', 'y']

    # initiate all the dictionaries to contain the metric data
    five_sigma_bundle, seeing_bundle, airmass_bundle = {}, {}, {}
    nvisits_bundle, skybrightness_bundle, cloud_bundle = {}, {}, {}
    coadd_bundle, exgal_bundle = {}, {}
    for version_key in versions:
        five_sigma_bundle[version_key] = {}
        seeing_bundle[version_key] = {}
        airmass_bundle[version_key] = {}
        nvisits_bundle[version_key] = {}
        skybrightness_bundle[version_key] = {}
        cloud_bundle[version_key] = {}
        coadd_bundle[version_key] = {}
        exgal_bundle[version_key] = {}

    # create the dustmap; needed for exgal
    dustmap = maps.DustMap(nside=nside, interp=False)

    # loop over all the versions
    for version_key in dbpath_dict:
        # results db object
        resultsDb = db.ResultsDb(outDir=outdir)
        # loop over the paths
        for band in bands:
            # load the db
            opsdb = db.OpsimDatabase(dbpath_dict[version_key])
            # constraint to get the right visits
            sqlconstraint = 'night <= %s and filter=="%s"'%(yr_cut * 365.25, band)
            sqlconstraint += ' and note not like "DD%"'
            print(sqlconstraint)
            # slicer
            slicer = slicers.HealpixSlicer(lonCol='fieldRA', latCol='fieldDec',
                                          latLonDeg=opsdb.raDecInDeg, nside=nside, useCache=False)
            # metric for median seeing
            metric = metrics.MedianMetric(col='seeingFwhmEff')
            seeing_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for median 5sigma
            metric = metrics.MedianMetric(col='fiveSigmaDepth')
            five_sigma_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for median airmass
            metric = metrics.MedianMetric(col='airmass')
            airmass_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for nvisits
            metric = metrics.CountMetric('observationStartMJD', metricName='Nvisits')
            nvisits_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for median skybrightnes
            metric = metrics.MedianMetric(col='skyBrightness')
            skybrightness_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for median cloud
            metric = metrics.MedianMetric(col='cloud')
            cloud_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for coadded depth without dust
            metric = metrics.Coaddm5Metric()
            coadd_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint)
            # metric for coadded depth with dust
            metric = metrics.ExgalM5(lsstFilter=band)
            exgal_bundle[version_key][band] = metricBundles.MetricBundle(metric, slicer, sqlconstraint, mapsList=[dustmap],)

        agroup = metricBundles.MetricBundleGroup(seeing_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        agroup.runAll()

        bgroup = metricBundles.MetricBundleGroup(five_sigma_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        bgroup.runAll()

        cgroup = metricBundles.MetricBundleGroup(airmass_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        cgroup.runAll()

        dgroup = metricBundles.MetricBundleGroup(nvisits_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        dgroup.runAll()

        dgroup = metricBundles.MetricBundleGroup(skybrightness_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        dgroup.runAll()

        dgroup = metricBundles.MetricBundleGroup(cloud_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        dgroup.runAll()

        dgroup = metricBundles.MetricBundleGroup(coadd_bundle[version_key], opsdb, outDir=outdir,
                                                 resultsDb=resultsDb, saveEarly= False)
        dgroup.runAll()

        dgroup = metricBundles.MetricBundleGroup(exgal_bundle[version_key], opsdb, outDir=outdir, 
                                                 resultsDb=resultsDb, saveEarly= False)
        dgroup.runAll()

    # plot things out
    bundle_mapper = {'seeing': seeing_bundle, 'airmass': airmass_bundle,
                     'single-visit 5sigma depth': five_sigma_bundle, 'nvisits': nvisits_bundle,
                     'skybrightness': skybrightness_bundle, 'cloud': cloud_bundle,
                     'coadd 5sigma depth': coadd_bundle, 'dust-extincted coadd depth': exgal_bundle
                    }
    plot_to_compare(outdir=outdir, nside=nside, dbname=dbname, bundle_mapper=bundle_mapper,
                    reference_version=reference_version, order_of_versions=order_of_versions,
                    valid_pixels='default', eg_ind_dict=None)

    # ---------------------------------------------------------------------------------------------
    # now run the eg-footprint metric
    eg_ind = {}
    # loop over the vrsions
    for version_key in dbpath_dict:
        # db object
        resultsDb = db.ResultsDb(outDir=outdir)
        # load the db
        opsdb = db.OpsimDatabase(dbpath_dict[version_key])
        print('\n## running eg-metric for *%s* %s\n' % (version_key, dbname))

        sqlconstraint = 'night <= %s' % (yr_cut * 365.25)
        sqlconstraint += ' and note not like "DD%"'

        slicer = slicers.HealpixSlicer(lonCol='fieldRA', latCol='fieldDec',
                                       latLonDeg=opsdb.raDecInDeg, nside=nside, useCache=False)

        # set up the metric
        metric = egFootprintMetric(nfilters_needed=6, lim_mag_i=lim_mag_i_dict[version_key],
                                   lim_ebv=lim_ebv_dict[version_key], return_coadd_band='i')

        # setup the bundle
        bundle = metricBundles.MetricBundle(metric, slicer, sqlconstraint, mapsList=[dustmap])
        # set up the group.
        grp = metricBundles.MetricBundleGroup({0: bundle}, opsdb, outDir=outdir,
                                              resultsDb=resultsDb, saveEarly=False)
        grp.runAll()

        plt.clf()
        hp.mollview(bundle.metricValues, title='%s i-band 5sigma coadded depth with dust extinction; eg-footprint' % version_key)
        hp.graticule(dpar=20, dmer=20, verbose=False)
        filename = 'skymap-eg_%s_%s.png' % (dbname, version_key)
        plt.savefig('%s/%s' % (outdir, filename), format= 'png', bbox_inches='tight')
        print('saved %s' % filename)
        plt.close('all')

        eg_ind[version_key] = bundle.metricValues.mask == False

    # plot things out
    plot_to_compare(outdir=outdir, nside=nside, dbname=dbname, bundle_mapper=bundle_mapper,
                    reference_version=reference_version, order_of_versions=order_of_versions,
                    valid_pixels='eg', eg_ind_dict=eg_ind)

##########################################################################
def plot_to_compare(outdir, nside, dbname, bundle_mapper, reference_version, order_of_versions,
                    valid_pixels='default', eg_ind_dict=None):
    """

    This function plots histograms for all the data in the bundle_mapper.

    Required Inputs
    ---------------
    * outdir: str: path to the folder where outputs should be stored.
    * nside: int: HEALpix resolution parameter.
    * dbname: str: tag to identify the outputs.
    * bundle_mapper: dict: dictionary with key=metric-name and values=bundle_dicts
                           for the respective metric. bundle data would be accessed
                           as bundle_dicts[version_key][band]
    * reference_version: str: version_key with which to compare everything against
    * order_of_versions: list of str: order of version_keys. reference_version must be
                                      the first.

    Optional Inputs
    ---------------
    * valid_pixels: str: 'default' or 'eg'
    * eg_ind_dict: dict: keys=version_key, values=pixel numbers for eg-fooprint

    """
    if reference_version != order_of_versions[0]:
        raise ValueError('reference_version must be the first in order_of_versions: input order_of_versions = %s' % order_of_versions)
    if valid_pixels not in ['default', 'eg']:
        raise ValueError('valid_pixels must be either "default" or "eg". input %s' % valid_pixels)
    if valid_pixels == 'eg' and eg_ind_dict is None:
        raise ValueError('must input eg_ind_dict if valid_pixels = "eg"')

    colors = {'u':'mediumorchid', 'g':'b', 'r':'g', 'i':'goldenrod', 'z':'orangered', 'y':'maroon'}

    for metric_label in bundle_mapper:
        bundle_to_consider = bundle_mapper[metric_label]
        ############################################################
        # find the min, max lim
        min_all, max_all = 1000, -1000
        for version_key in bundle_to_consider:
            for band in bundle_to_consider[version_key]:
                ind = bundle_to_consider[version_key][band].metricValues.mask == False
                min_all = min(min_all, min(bundle_to_consider[version_key][band].metricValues.data[ind]))
                max_all = max(max_all, max(bundle_to_consider[version_key][band].metricValues.data[ind]))
        if metric_label.__contains__('dust'): min_all = 22
        # set up the bins
        if metric_label.__contains__('nvisits'):
            bins = np.arange(min_all - 5, max_all + 10 , 5)
        else:
            bins = np.arange(min_all - 0.01, max_all + 0.02 , 0.01)
        ############################################################

        plt.clf()
        nrows, ncols = 1, len(order_of_versions)
        fig, axes = plt.subplots(nrows=nrows, ncols=ncols)
        plt.subplots_adjust(wspace=0.1, hspace=0.3)

        for i, version_key in enumerate( order_of_versions ):
            if version_key == reference_version:
                # calculate median for the reference version and plot
                meds_1 = {}
                for band in bundle_to_consider[version_key]:
                    if valid_pixels == 'default':
                        ind = bundle_to_consider[version_key][band].metricValues.mask == False
                    else:
                        ind = eg_ind_dict[version_key]
                    # create legend
                    if metric_label.__contains__('nvisits'):
                        meds_1[band] = np.sum(bundle_to_consider[version_key][band].metricValues.data[ind])
                        llabel='%s: total %.f' % (band, meds_1[band]),
                    else:
                        meds_1[band] = np.median(bundle_to_consider[version_key][band].metricValues.data[ind])
                        llabel='%s: median %.3f' % (band, meds_1[band])
                    # plot
                    axes[i].hist(bundle_to_consider[version_key][band].metricValues.data[ind], color=colors[band],
                                 histtype='step', label=llabel,
                                 lw=2, bins=bins)
            else:
                # calculate the median for this version and compare with the reference
                meds_2 = {}
                for band in bundle_to_consider[version_key]:
                    if valid_pixels == 'default':
                        ind = bundle_to_consider[version_key][band].metricValues.mask == False
                    else:
                        ind = eg_ind_dict[version_key]
                    # construct the legend
                    if metric_label.__contains__('nvisits'):
                        meds_2[band] = np.sum(bundle_to_consider[version_key][band].metricValues.data[ind])
                        llabel='%s: total %.f (%s - [%.f]; %.2f%% )' % (band, meds_2[band],  reference_version,
                                                                         meds_1[band] - meds_2[band],
                                                                        ((meds_1[band] - meds_2[band])/meds_1[band]) * 100
                                                                       ),
                    else:
                        meds_2[band] = np.median(bundle_to_consider[version_key][band].metricValues.data[ind])
                        llabel='%s: median %.3f (%s - [%.3f] )' % (band, meds_2[band], reference_version, meds_1[band] - meds_2[band])
                    # plot
                    axes[i].hist(bundle_to_consider[version_key][band].metricValues.data[ind], color=colors[band],
                                 histtype='step', label=llabel,
                                 lw=2, bins=bins)
        # plot details
        for i in range(ncols):
            axes[i].legend(bbox_to_anchor=(0.9, -0.2))
            axes[i].set_yscale('log')
        # enforce same limits across the subplots
        ymin, ymax = 1e7, -1e7
        for i in range(ncols):
            ylims = axes[i].get_ylim()
            ymin = min( ymin, ylims[0] )
            ymax = max( ymax, ylims[1] )
        for i in range(ncols):
            axes[i].set_ylim(ymin, ymax)
            axes[i].set_title(list(bundle_to_consider.keys())[i])
            axes[i].set_xlabel(metric_label)
        axes[0].set_ylabel('counts')

        # plot size
        plt.gcf().set_size_inches(10 * ncols, 5)
        # setup to save figure
        if valid_pixels == 'default':
            plt.suptitle('%s: %s\n(in respective wfd-constraint)' % (dbname, metric_label), y=1.07, fontsize=20, fontweight='bold')
            filename = 'compare-hists_wfd_%s_%s_nside%s.png' % (dbname, metric_label.replace(' ', '-'), nside)
        else:
            plt.suptitle('%s: %s\n(in respective eg-footprint)' % (dbname, metric_label), y=1.07, fontsize=20, fontweight='bold')
            filename = 'compare-hists_eg_%s_%s_nside%s.png' % (dbname, metric_label.replace(' ', '-'), nside)
        # save figure
        plt.savefig('%s/%s' % (outdir, filename), format= 'png', bbox_inches='tight')
        print('saved %s' % filename)
        plt.close('all')
        #plt.show()