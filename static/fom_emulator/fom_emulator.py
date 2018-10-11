"""
The goal of this script is to enable FoM emulation for WL+CL+LSS given a set of FoMs on a grid of
(area, depth).

Still to do:
- Get files from Tim.
- Check file read-in for consistency with area, depth.
- Inspect plots.
- Set up actual emulation.
- Look at outputs; plot along with grid values, output in more convenient format.
- Do the depth optimization.
"""
import numpy as np
import matplotlib.pyplot as plt
import glob
import os
cm = plt.cm.get_cmap('RdYlBu')

# Set some defaults.
year_vals = ['Y1']#, 'Y3', 'Y6', 'Y10']

areas = np.zeros((3,4)) # 3 grid values, 4 years
areas[:,0] = np.array([7.5, 13., 16.]) * 1000.0 # deg^2 for Y1
areas[:,1] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10
areas[:,2] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10
areas[:,3] = np.array([10., 15., 20.]) * 1000.0 # for Y3, Y6, Y10

depths = np.zeros((3,4)) # 3 grid values, 4 years
depths[:,0] = np.array([24.9, 25.2, 25.5])
depths[:,1] = np.array([25.5, 25.8, 26.1])
depths[:,2] = np.array([25.9, 26.1, 26.3])
depths[:,3] = np.array([26.3, 26.5, 26.7])

area_mid = areas[1,1] # arbitrary area for rescaling

def load_foms(dir='FoM', prior=False):
    """Script to load some FoM values on a 3x3 grid in (area, depth)."""

    # Get list of files in directory.
    file_list = glob.glob(os.path.join(dir, '*'))
    
    # Initialize FoM arrays.  The first dimension is area, second is depth, 3rd is year.
    fom_arr = np.zeros((3,3,len(year_vals)))

    # Find the ones with Y1, Y3, Y6, Y10.  For each, get the right types of FoMs in order.
    for year_str in year_vals:
        # Find the one that has that year string and no other, otherwise Y1 and Y10 are confused.
        my_file = None
        for file_name in file_list:
            # Find the one that has that year string.
            if year_str in file_name:
                # Then make sure none of the others is there.
                other_found = False
                for tmp_year_str in year_vals:
                    if tmp_year_str != year_str and not tmp_year_str in year_str:
                        if tmp_year_str in file_name:
                            other_found = True
                if not other_found:
                    if my_file is None:
                        my_file = file_name
                    else:
                        if my_file != file_name:
                            raise ValueError(
                                "Year %s found more than once in dir %s!"%\
                                (year_str, dir))
        if my_file is None:
            raise ValueError("Year %s not found in dir %s!"%(year_str, dir))
        print('Found file %s for year %s in dir %s'%(my_file, year_str, dir))

        # Now read in the relevant parts of the file.
        lines = [line.rstrip('\n') for line in open(my_file)]

        # Find the right lines based on whether they include/exclude the Stage III prior.
        if prior:
            grep_str = 'incl'
        else:
            grep_str = 'excl'


        n_found = 0
        for line in lines:
            if grep_str in line:
                tmp_fom = float(line.split('=')[1])
                fom_arr[n_found % 3, int(n_found / 3), year_vals.index(year_str)] = tmp_fom
                n_found += 1
        print('%s relevant lines found'%n_found)

    return fom_arr

def load_strategy_table(year_str = 'Y1'):
    infile = './strategy_table_%s.txt'%year_str
    if not os.path.exists(infile):
        raise ValueError("Cannot find file %s for year %s!"%(infile, year_str))

    # Read it in
    lines = [line.rstrip('\n') for line in open(infile)]

    strat_name = []
    area = []
    median_depth = []
    for line in lines:
        tmp_vals = line.split("|")
        strat_name.append(tmp_vals[1].strip())
        area.append(float(tmp_vals[3].strip()))
        median_depth.append(float(tmp_vals[4].strip()))
    print('Strategy table loaded: %d lines in %s for year %s!'%\
          (len(strat_name), infile, year_str))
    return strat_name, area, median_depth

def area_depth_func(x, a, b, c):
    """ a * (area / area_0)^b * (depth - depth_0)^c """
    areas = x[0,:]
    depths = x[1,:]
    area_renorm = areas / areas[4]
    depth_renorm = depths / depths[4]
    return (a + b*depth_renorm)*(area_renorm**c)   

def emulate_fom(area_vals, depth_vals, grid_area_vals, grid_depth_vals, grid_fom_vals, figpref=None):
    """Try various things here."""
    print('Starting emulator')
    from scipy import interpolate
    f = interpolate.interp2d(grid_area_vals, grid_depth_vals, grid_fom_vals, bounds_error=False)
    emulated_grid_fom_vals = f(grid_area_vals[:,0], grid_depth_vals[0,:])

    if figpref is not None:
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(grid_area_vals, grid_depth_vals, c=emulated_grid_fom_vals/grid_fom_vals-0.5,
                        cmap=cm, s=80, edgecolors='none')
        plt.colorbar(sc)
        plt.title('Emulator ratio - 0.5')
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/%s_ratio.pdf'%figpref)

        finer_area = np.linspace(np.min(area_vals), np.max(area_vals), 20)
        finer_depth = np.linspace(np.min(depth_vals), np.max(depth_vals), 20)
        finer_area_grid, finer_depth_grid = np.meshgrid(finer_area, finer_depth)
        test_emulator = f(finer_area, finer_depth)
        fig = plt.figure()
        ax = fig.add_subplot(111)
        sc = ax.scatter(finer_area_grid, finer_depth_grid, c=test_emulator/np.max(test_emulator),
                        cmap=cm, s=80, edgecolors='none')
        ax.scatter(area_vals, depth_vals, color='k', marker='x')
        plt.colorbar(sc)
        plt.title('Emulated FoM / max')
        plt.xlabel('Area [sq. deg.]')
        plt.ylabel('Median i-band depth')
        plt.savefig('figs/%s_finer.pdf'%figpref)
        
        
    fom_vals = []
    for ind in range(len(area_vals)):
        fom_vals.append(f(area_vals[ind], depth_vals[ind])[0])
    fom_vals = np.array(fom_vals)
    return fom_vals

# Get FoM values.  
foms_prior = load_foms(prior=True)
print(foms_prior[:,:,0])
foms_noprior = load_foms(prior=False)
print(foms_noprior[:,:,0])

# Make some basic plots:
# In each year, make a 2D color plot of the FoM vs. depth and area without and with prior, without
# and with removal of area scaling.
for year_ind in range(len(year_vals)):
    plot_areas = np.repeat(areas[:,year_ind],3).reshape(areas[:,year_ind].shape[0],3)
    plot_depths = np.repeat(depths[:,year_ind],3).reshape(depths[:,year_ind].shape[0],3).transpose()
    fom_max = max(np.max(foms_prior[:,:,year_ind]), np.max(foms_noprior[:,:,year_ind]))
    fom_max_rescale = max(np.max(foms_prior[:,:,year_ind]*area_mid/plot_areas),
                             np.max(foms_noprior[:,:,year_ind]*area_mid/plot_areas))
    max_val = max(fom_max, fom_max_rescale)

    # No prior, no area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths, c=foms_prior[:,:,year_ind]/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('FoM/%d (with Stage III prior)'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_prior.pdf'%year_vals[year_ind])

    # Prior, no area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths, c=foms_noprior[:,:,year_ind]/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('FoM/%d (no prior)'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_noprior.pdf'%year_vals[year_ind])

    # No prior, area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths,
                    c=foms_prior[:,:,year_ind]*area_mid/plot_areas/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('(Rescaled FoM with Stage III prior)/%d'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_prior_rescaled.pdf'%year_vals[year_ind])

    # Prior, area rescaling.
    fig = plt.figure()
    ax = fig.add_subplot(111)
    sc = ax.scatter(plot_areas, plot_depths,
                    c=foms_noprior[:,:,year_ind]*area_mid/plot_areas/max_val,
                    cmap=cm, s=80, edgecolors='none')
    plt.colorbar(sc)
    plt.title('(Rescaled FoM without prior)/%d'%max_val)
    plt.xlabel('Area [sq. deg.]')
    plt.ylabel('Median i-band depth')
    plt.savefig('figs/fom_emulator_%s_noprior_rescaled.pdf'%year_vals[year_ind])

    # Evaluate various strategies using emulator as needed.

    # Load strategy tables:
    tmp_strat, tmp_area, tmp_depth = load_strategy_table(year_vals[year_ind])
    emulated_fom_prior = emulate_fom(tmp_area, tmp_depth, plot_areas, plot_depths,
                                     foms_prior[:,:,year_ind],
                                     figpref='test_prior_%s'%year_vals[year_ind])
    emulated_fom_noprior = emulate_fom(tmp_area, tmp_depth, plot_areas, plot_depths,
                                       foms_noprior[:,:,year_ind],
                                       figpref='test_noprior_%s'%year_vals[year_ind])
    inds = emulated_fom_noprior.argsort()[::-1]
    print('')
    print('Emulated from best to worst in year %s'%year_vals[year_ind])
    print('Strategy, Area, median i-band depth, FoM without prior, FoM with prior')
    for ind in inds:
        print('%20s %d %.2f %d %d'%(tmp_strat[ind], tmp_area[ind], tmp_depth[ind], emulated_fom_noprior[ind], emulated_fom_prior[ind]))
    print('')

# Depth optimization.