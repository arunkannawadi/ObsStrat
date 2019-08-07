The goal here to construct a modified WFD footprint that is optimized for extragalactic science (by avoiding high-extinction areas) and for LSS (wider area coverage). We start with using the wider-coverage OpSim output, `pontus_2002`.

#### Code Details
`bash_calc_coadd.sh` is the script that loads the right sims stacks and runs `calc_coadd_depth.py` that calculates the 5$\sigma$ coadded depth for 1yr and 10yr surveys (using the code from [mafContrib](https://github.com/LSST-nonproject/sims_maf_contrib ); the latest code still needs to be merged with the master branch but the latest versions are in [my fork](https://github.com/humnaawan/sims_maf_contrib )).

`WFD_footprint_ebv_cut.ipynb` runs `implement_ebv_cut_only.py` to implement an EBV>0.2 cut on the database and saves the fieldIDs and healpix pixel numbers for the EBV<0.2 region. Please see the notebook for more details.

`WFD_extragalactic_footprint_optimized.ipynb` then takes the EBV<0.2 area and implements a declination cut such that we only have about 18,000 deg2 in the proposed WFD region (and then removes two small patches for continuity).

`check_WFD_footprint_from_undithfieldID.ipynb` re-creates the WFD footprint based on the undithered fieldIDs and compare the result from the HEALPix-pixels based footprint.

`modified_wfd_mollwiede.ipynb` re-creates the WFD footprint from the saved healpix pixels using the matplotlib `mollweide` project (to get ra, dec lines).

`modified_wfd_overlaps.ipynb` calculates the overlap between the new WFD footprint and DESI/4MOST.

`check_airmass_seeing.ipynb` looks at median statistics for some quantities (airmass, seeing, fiveSigmaDepth) at some declinations to get a sense of how things change as we observe at high declinations.

#### Outputs
All the outputs are in `/global/homes/a/awan/desc/wfd_footprint/`, including:
- `WFDfootprint_nside256_HEALPixels.csv` with the HEALPix pixels that constitute the proposed WFD.
- `WFDfootprint_nside256_undithered_fieldIDs.csv` with the undithered fieldIDs for that observe in the proposed region.
- Plots from `WFD_extragalactic_footprint_optimized.ipynb`:
    1. `WFDfootprint_nside256_intermediates_RandomDitherPerNight.png` shows the various intermediates steps (from EBV-limited region to the final footprint).
    2. `WFDfootprint_nside256.png` shows the mask based on the HEALPix pixel list.
- Plots from `modified_wfd_mollwiede.pynb`:
    1. `WFDfootprint_proposed_vs_kraken_2026_nside256_matplotlib.png`: overplots proposed footprint with the baseline
    2. `WFDfootprint_kraken_2026_nside256_matplotlib.png` and `WFDfootprint_proposed_nside256_matplotlib.png`: show footprint in 1. separately.
    3. `WFDfootprint_proposed_vs_kraken_2026_vs_4MOST+DESI_nside256_matplotlib.png`: overplots proposed footprint with the baseline, DESI, and 4MOST/TiDES fotoprints.
    (older versions of the notebook produced `WFDfootprint_nside256_matplotlib.png`,  `WFDfootprint_proposed_vs_baseline2018a_nside256_matplotlib.png`, and ` WFDfootprint_proposed_vs_4MOST-TiDES+DESI_nside256_matplotlib.png`)
- Numbers from `modified_wfd_overlaps.ipynb`:

    |  | New WFD | 4MOST-TiDES | DESI |
    | --- | --- | --- | --- |
    | Total area (deg2) |  18074.29 | 15845.86 | 15011.87 |

    | dbname | LSST+4MOST-TiDES (deg2) | LSST+DESI (deg2) | LSST+4MOST-TiDES/DESI (deg2) | LSST+4MOST-TiDES+DESI (deg2) |
    | --- | --- | --- | --- | --- |
    | New WFD |  13763.58 | 5932.23 | 16407.61 | 3288.20 |