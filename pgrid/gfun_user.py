"""
User-specific code for pgrid.

You would edit the information to reflect whatever grid you are working on.
"""
import numpy as np
import pandas as pd
from lo_tools import zfun, Lfun

import sys
from pathlib import Path
pth = Path(__file__).absolute().parent.parent.parent / 'LO' / 'pgrid'
if str(pth) not in sys.path:
    sys.path.append(str(pth))
import gfun_utility as gfu
import gfun

# This is the name of the grid that you are working on.
gridname = 'test0'

# default s-coordinate info (could override below)
s_dict = {'THETA_S': 4, 'THETA_B': 2, 'TCLINE': 10, 'N': 30,
        'VTRANSFORM': 2, 'VSTRETCHING': 4}

def make_initial_info(gridname=gridname):
    # Add an elif section for your grid.

    if gridname == 'test0':
        # A large grid, used as a test.
        dch = gfun.default_choices()
        aa = [-130, -122, 42, 52]
        res = 1000 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['nudging_edges'] = ['north','south','west']
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'hc0':
        dch = gfun.default_choices()
        aa = [-123.2, -122.537, 47.3, 47.9]
        res = 100 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'psdem' / 'PS_27m.nc']
        dch['nudging_edges'] = ['north']
        dch['nudging_days'] = (0.1, 1.0)
        
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'ai0':
        dch = gfun.default_choices()
        aa = [-122.82, -122.36, 47.758, 48.18]
        res = 100 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'psdem_10m' / 'PS_30m.nc']
        dch['nudging_edges'] = ['north', 'south', 'east', 'west']
        dch['nudging_days'] = (0.1, 1.0)
        
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'so0':
        # South Sound
        dch = gfun.default_choices()
        dch['z_offset'] = -1.3 # NAVD88 is 1.3 m below MSL at Seattle
        dch['excluded_rivers'] = ['skokomish']
        aa = [-123.13, -122.76, 47, 47.42]
        res = 50 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'srtm15' / 'topo15.nc',
                    dch['t_dir'] / 'psdem_10m' / 'PS_30m.nc']
        dch['nudging_edges'] = ['east']
        dch['nudging_days'] = (0.1, 1.0)
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'so1':
        # South Sound, new version, 2023.04.12
        dch = gfun.default_choices()
        dch['z_offset'] = -1.3 # NAVD88 is 1.3 m below MSL at Seattle
        dch['excluded_rivers'] = ['skokomish']
        aa = [-123.13, -122.76, 47, 47.42]
        res = 100 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'srtm15' / 'topo15.nc',
                    dch['t_dir'] / 'psdem_10m' / 'PS_30m.nc']
        dch['nudging_edges'] = ['east']
        dch['nudging_days'] = (0.1, 1.0)
        
        # by setting a small min_depth were are planning to use
        # wetting and drying in ROMS, but maintaining positive depth
        # for all water cells
        dch['min_depth'] = 0.2 # meters (positive down)
        
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'wgh1':
        # Willapa Bay and Grays Harbor nest
        dch = gfun.default_choices()
        aa = [-124.4,-123.7,46.35,47.1]
        res = 200 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'nw_pacific' / 'nw_pacific.nc']
        dch['z_offset'] = -1
        # The docs for nw_pacific say the vertical datum is "sea level" so to match
        # this we would use z_offset = 0, but the intention here is to make the z=0
        # level be higher up, so that we catch more of the intertidal when using
        # WET_DRY. This must be matched by a similar intervention to zeta in ocnN.
        dch['nudging_edges'] = ['north', 'south', 'west']
        dch['nudging_days'] = (0.1, 1.0)
        
        # by setting a small min_depth were are planning to use
        # WET_DRY in ROMS, but maintaining positive depth
        # for all water cells
        dch['min_depth'] = 0.2 # meters (positive down)
        
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'cas2k':
        # cas6 domain but with 2 km resolution
        dch = gfun.default_choices()
        aa = [-130, -122, 42, 52]
        res = 2000 # target resolution (m)
        Lon_vec, Lat_vec = gfu.simple_grid(aa, res)
        dch['t_list'] = [dch['t_dir'] / 'srtm15' / 'topo15.nc',
                  dch['t_dir'] / 'cascadia' / 'cascadia_gridded.nc',
                 dch['t_dir'] / 'nw_pacific' / 'nw_pacific.nc']
        dch['nudging_edges'] = ['north', 'south', 'west']
        dch['nudging_days'] = (3.0, 60.0)
        # Make the rho grid.
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        
        # Initialize bathymetry
        dch['t_list'] = ['srtm15plus','cascadia','nw_pacific','psdem',
               'ttp_patch','grays_harbor','willapa_bay']
        z = gfu.combine_bathy_from_sources(lon, lat, dch)
                
        if dch['use_z_offset']:
            z = z + dch['z_offset']
            
    elif gridname == 'cas7':
        # based completely on cas6 except we carve out Agate Pass and
        # Swinomish Channel by hand.
        dch = gfun.default_choices()
        dch['nudging_edges'] = ['north', 'south', 'west']
        dch['nudging_days'] = (3.0, 60.0)
        Ldir = Lfun.Lstart()
        fn = Ldir['parent'] / 'LO_output' / 'pgrid' / 'cas6' / 'grid.nc'
        dch['maskfile_to_copy'] = fn
        dch['remove_islands'] = False
        dch['trim_grid'] = False

        import xarray as xr
        ds = xr.open_dataset(fn)
        z = -ds.h.values
        lon = ds.lon_rho.values
        lat = ds.lat_rho.values
        
        # The plan is to only run:
        # start_grid
        # make_mask
        # edit_mask
        # (don't run carve_rivers - just copy the file from cas6)
        # smooth_grid
        # make_extras
        # grid_to_LO
            
    elif gridname == 'ae0':
        # analytical model estuary
        dch = gfun.default_choices()
        lon_list = [-2, 0, 1, 2]
        x_res_list = [2500, 500, 500, 2500]
        lat_list = [43, 44.9, 45.1, 47]
        y_res_list = [2500, 500, 500, 2500]
        Lon_vec, Lat_vec = gfu.stretched_grid(lon_list, x_res_list,
                                            lat_list, y_res_list)
        lon, lat = np.meshgrid(Lon_vec, Lat_vec)
        dch['analytical'] = True
        dch['nudging_edges'] = ['north', 'south', 'west']
        dch['use_z_offset'] = False
        # tidy up dch
        dch['z_offset'] = 0.0
        dch['t_dir'] = 'BLANK'
        dch['t_list'] = ['BLANK']
        # make bathymetry by hand
        z = np.zeros(lon.shape)
        x, y = zfun.ll2xy(lon, lat, 0, 45)
        zshelf = x * 1e-3
        zestuary = -20 + 20*x/1e5 + 20/(1e4)*np.abs(y)
        z = zshelf
        mask = zestuary < z
        z[mask] = zestuary[mask]
        
        # create a river file by hand
        Ldir = Lfun.Lstart()
        dch['ctag'] = 'ae0_v0'
        ri_dir = Ldir['LOo'] / 'pre' / 'river1' / dch['ctag']
        Lfun.make_dir(ri_dir)
        gri_fn = ri_dir / 'river_info.csv'
        with open(gri_fn, 'w') as rf:
            rf.write('rname,usgs,ec,nws,ratio,depth,flow_units,temp_units\n')
            rf.write('creek0,,,,1.0,5.0,m3/s,degC\n')
        # and make a track for the river
        track_dir = ri_dir / 'tracks'
        Lfun.make_dir(track_dir)
        track_fn = track_dir / 'creek0.p'
        track_df = pd.DataFrame()
        NTR = 100
        if True:
            track_df['lon'] = np.linspace(0,4,NTR) # OK to go past edge of domain
            track_df['lat'] = 45*np.ones(NTR)
        else: # Debugging with N/S river channel
            track_df['lon'] = 0.25*np.ones(NTR)
            track_df['lat'] = np.linspace(45,44,NTR) # South to North river
        track_df.to_pickle(track_fn)
        # *** NOTE: TRACKS MUST GO FROM OCEAN TO LAND ***
        
    else:
        print('Error from make_initial_info: unsupported gridname')
        return
        
    if dch['trim_grid']:
        # check for odd size of grid and trim if needed
        NR, NC = lon.shape
        if np.mod(NR,2) != 0:
            print('- trimming row from grid')
            lon = lon[:-1,:]
            lat = lat[:-1,:]
            z = z[:-1,:]
        if np.mod(NC,2) != 0:
            print('- trimming column from grid')
            lon = lon[:,:-1]
            lat = lat[:,:-1]
            z = z[:,:-1]
            
    return lon, lat, z, dch
    

