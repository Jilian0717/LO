"""
Functions for writing saved fields to ROMS NetCDF.

This version works, but is deprecated in LO because it relies
on the netCDF4 module.

"""

import os
import netCDF4 as nc
import numpy as np
from lo_tools import Lfun

# set to True for compression
zchoice = True

def make_clm_file(nc_dir, data_dict, N, NR, NC):
    # name output file
    clm_fn = nc_dir / 'ocean_clm.nc'
    clm_fn.unlink(missing_ok=True)
    foo = nc.Dataset(clm_fn, 'w')
    # create dimensions
    for vn in ['salt', 'temp', 'v3d', 'v2d', 'zeta', 'ocean']:
        foo.createDimension(vn+'_time', len(data_dict['ocean_time']))
    foo.createDimension('s_rho', N)
    foo.createDimension('eta_rho', NR)
    foo.createDimension('xi_rho', NC)
    foo.createDimension('eta_u', NR)
    foo.createDimension('xi_u', NC-1)
    foo.createDimension('eta_v', NR-1)
    foo.createDimension('xi_v', NC)
    # add time data
    for vn in ['salt', 'temp', 'v3d', 'v2d', 'zeta', 'ocean']:
        vv = foo.createVariable(vn+'_time', float, (vn+'_time',), zlib=zchoice)
        vv.units = Lfun.roms_time_units #'seconds since 1970.01.01 UTC'
        vv[:] = data_dict['ocean_time']

    def make_ma(vn):
        f = data_dict[vn]
        ff = np.ma.masked_where(np.isnan(f), f)
        return ff
        
    # add 2d field data
    vv = foo.createVariable('zeta', float, ('zeta_time', 'eta_rho', 'xi_rho'), zlib=zchoice)
    vv.long_name = 'sea surface height climatology'
    vv.units = 'meter'
    vv[:] = make_ma('zeta')
    
    vv = foo.createVariable('ubar', float, ('v2d_time', 'eta_u', 'xi_u'), zlib=zchoice)
    vv.long_name = 'vertically averaged u-momentum climatology'
    vv.units = 'meter second-1'
    vv[:] = make_ma('ubar')
    
    vv = foo.createVariable('vbar', float, ('v2d_time', 'eta_v', 'xi_v'), zlib=zchoice)
    vv.long_name = 'vertically averaged v-momentum climatology'
    vv.units = 'meter second-1'
    vv[:] = make_ma('vbar')
    
    # add 3d field data
    vv = foo.createVariable('u', float, ('v3d_time', 's_rho', 'eta_u', 'xi_u'), zlib=zchoice)
    vv.long_name = 'u-momentum component climatology'
    vv.units = 'meter second-1'
    vv[:] = make_ma('u')
    
    vv = foo.createVariable('v', float, ('v3d_time', 's_rho', 'eta_v', 'xi_v'), zlib=zchoice)
    vv.long_name = 'v-momentum component climatology'
    vv.units = 'meter second-1'
    vv[:] = make_ma('v')
    
    vv = foo.createVariable('salt', float, ('salt_time', 's_rho', 'eta_rho', 'xi_rho'), zlib=zchoice)
    vv.long_name = 'salinity climatology'
    vv.units = 'PSU'
    vv[:] = make_ma('salt')
    
    vv = foo.createVariable('temp', float, ('temp_time', 's_rho', 'eta_rho', 'xi_rho'), zlib=zchoice)
    vv.long_name = 'potential temperature climatology'
    vv.units = 'Celsius'
    vv[:] = make_ma('temp')
    
    foo.close()
    print('-Writing ocean_clm.nc')
        
def make_ini_file(nc_dir):
    # Initial condition, copied from first time of ocean_clm.nc
    ds1 = nc.Dataset(nc_dir / 'ocean_clm.nc', mode='r')
    # name output file
    ini_fn = nc_dir / 'ocean_ini.nc'
    ini_fn.unlink(missing_ok=True)
    ds2 = nc.Dataset(ini_fn, 'w')
    # Copy dimensions
    for dname, the_dim in ds1.dimensions.items():
        if 'time' in dname:
            ds2.createDimension(dname, 1)
        else:
            ds2.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)
    # Copy variables
    for v_name, varin in ds1.variables.items():
        outVar = ds2.createVariable(v_name, varin.datatype, varin.dimensions, zlib=zchoice)
        # Copy variable attributes, {} is a dict comprehension, cool!
        outVar.setncatts({k: varin.getncattr(k).replace('climatology','').strip()
                for k in varin.ncattrs()})
        if varin.ndim > 1:
            outVar[:] = varin[0,:]
        else:
            outVar[:] = varin[0]
    ds1.close()
    ds2.close()
    print('-Writing ocean_ini.nc')

def make_bry_file(nc_dir):
    # Boundary conditions, copied from edges of ocean_clm.nc
    ds1 = nc.Dataset(nc_dir / 'ocean_clm.nc', mode='r')
    # name output file
    bry_fn = nc_dir / 'ocean_bry.nc'
    bry_fn.unlink(missing_ok=True)
    ds2 = nc.Dataset(bry_fn, 'w')
    # Copy dimensions
    for dname, the_dim in ds1.dimensions.items():
        ds2.createDimension(dname, len(the_dim) if not the_dim.isunlimited() else None)
    # Copy parts of variables
    for v_name, varin in ds1.variables.items():
        if varin.ndim in [3,4]: 
            for bname in ['north', 'south', 'east', 'west']:
                # hacks to get the right boundary names for a few BGC variables
                # (really this should be regularized in the ROMS NPZD code)
                if v_name == 'phytoplankton':
                    v_name = 'phyt'
                if v_name == 'zooplankton':
                    v_name = 'zoop'
                if v_name == 'alkalinity':
                    v_name = 'Talk'
                outname = v_name + '_' + bname
                if bname in ['north', 'south']:
                    outdims = tuple([item for item in varin.dimensions if item[:3] != 'eta'])
                elif bname in ['west', 'east']:
                    outdims = tuple([item for item in varin.dimensions if item[:2] != 'xi'])
                outVar = ds2.createVariable(outname, varin.datatype, outdims)    
                outVar.setncatts({k: varin.getncattr(k).replace('climatology','').strip()
                        for k in varin.ncattrs()})
                if varin.ndim == 4:
                    if bname == 'north':
                        outVar[:] = varin[:,:,-1,:]
                    elif bname == 'south':
                        outVar[:] = varin[:,:,0,:]
                    elif bname == 'east':
                        outVar[:] = varin[:,:,:,-1]
                    elif bname == 'west':
                        outVar[:] = varin[:,:,:,0]
                elif varin.ndim == 3:
                    if bname == 'north':
                        outVar[:] = varin[:,-1,:]
                    elif bname == 'south':
                        outVar[:] = varin[:,0,:]
                    elif bname == 'east':
                        outVar[:] = varin[:,:,-1]
                    elif bname == 'west':
                        outVar[:] = varin[:,:,0]
        else:
            outname = v_name
            outdims = tuple([item for item in varin.dimensions])
            outVar = ds2.createVariable(outname, varin.datatype, outdims)    
            outVar.setncatts({k: varin.getncattr(k).replace('climatology','').strip()
                    for k in varin.ncattrs()})
            outVar[:] = varin[:]    
    ds1.close()
    ds2.close()
    print('-Writing ocean_bry.nc')
