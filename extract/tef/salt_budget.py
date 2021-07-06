"""
Do volume and salt budgets for user-specified volumes.
This is a fairly complicated task because it involves coordinating
the net salt and volume time series from flux_[get,lowpass]_s.py,
the TEF transports through any open sections of the volume,
and all the rivers flowing into the volume.

Run with a command like:
run salt_budget -test True
and then it runs for all volumes in vol_list

"""

import os; import sys
sys.path.append(os.path.abspath('../alpha'))


import Lfun
import tef_fun
import flux_fun

import matplotlib.pyplot as plt
import numpy as np
import pickle
import pandas as pd
from datetime import datetime, timedelta
import argparse

# debugging imports
import netCDF4 as nc
from time import time
import zfun

parser = argparse.ArgumentParser()
parser.add_argument('-g', '--gridname', type=str, default='cas6')
parser.add_argument('-t', '--tag', type=str, default='v3')
parser.add_argument('-x', '--ex_name', type=str, default='lo8b')
parser.add_argument('-test', '--testing', type=zfun.boolean_string, default=False)
args = parser.parse_args()
testing = args.testing

old_dt = False

# Get Ldir
Ldir = Lfun.Lstart(args.gridname, args.tag)
gtagex = args.gridname + '_' + args.tag + '_' + args.ex_name

if testing:
    year_list = [2018]
    vol_list = ['Puget Sound']
    save_figs = False
else:
    year_list = [2018]
    vol_list = ['Salish Sea', 'Puget Sound', 'Hood Canal']
    save_figs = True

# make DataFrames to hold error statistics
err_df_vol = pd.DataFrame(index=year_list, columns=vol_list)
err_df_salt = pd.DataFrame(index=year_list, columns=vol_list)

plt.close('all')
for which_vol in vol_list:

    for year in year_list:
        year_str = str(year)
    
        # select input/output location
        run_name = gtagex+'_'+year_str+'.01.01_'+year_str+'.12.31'
        indir00 = Ldir['LOo'] + 'tef2/'
        indir0 = indir00 + run_name + '/'

        outdir = indir00 + 'salt_budget_plots/'
        Lfun.make_dir(outdir)

        # load low passed segment volume, net salt, and other DataFrames
        v_lp_df = pd.read_pickle(indir0 + 'flux/daily_segment_volume.p')
        sv_lp_df = pd.read_pickle(indir0 + 'flux/daily_segment_net_salt.p')
        
        # new
        vt_lp_df = pd.read_pickle(indir0 + 'flux/daily_segment_vt.p')
        svt_lp_df = pd.read_pickle(indir0 + 'flux/daily_segment_svt.p')

        # Info specific to each volume
        # The sign for each section indicates which direction is INTO the volume.
        if which_vol == 'Salish Sea':
            seg_list = list(v_lp_df.columns)
            sect_sign_dict = {'jdf1':1, 'sog5':-1}
        elif which_vol == 'Puget Sound':
            seg_list = (flux_fun.ssA + flux_fun.ssM + flux_fun.ssT
                + flux_fun.ssS + flux_fun.ssW + flux_fun.ssH)
            sect_sign_dict = {'ai1':1, 'dp':1}
        elif which_vol == 'Hood Canal':
            seg_list = flux_fun.ssH
            sect_sign_dict = {'hc1':-1}

        v_lp_df = v_lp_df[seg_list]
        sv_lp_df = sv_lp_df[seg_list]
        
        vt_lp_df = vt_lp_df[seg_list]
        svt_lp_df = svt_lp_df[seg_list]
            
        sect_df = tef_fun.get_sect_df()

        river_list = []
        for seg_name in seg_list:
            seg = flux_fun.segs[seg_name]
            river_list = river_list + seg['R']
        riv_df = pd.read_pickle(Ldir['LOo'] + 'river/'
            + Ldir['gtag'] + '_'+year_str+'.01.01_'+year_str+'.12.31.p')
        riv_df.index += timedelta(days=0.5)
        riv_df = riv_df[river_list]
    
        tef_df_dict = {}
        for sn in sect_sign_dict.keys():
            sect_sign = sect_sign_dict[sn]
            tef_df_dict[sn], in_sign = flux_fun.get_fluxes(indir0, sn)
            if in_sign != sect_sign:
                print('WARNING: potential sign error!!')
                
        # BUDGETS
        indall = sv_lp_df.index
        
        # miscellaneous stuff that doesn't go in budget
        misc_df = pd.DataFrame(0,index=indall, columns = ['Qprism','Ftide'])
        # we initialize only columns where we sum over TEF sections
        for sect_name in tef_df_dict.keys():
            df = tef_df_dict[sect_name]
            misc_df['Qprism'] = misc_df['Qprism'] + df['Qtide']/2 # [m3/s]
            misc_df['Ftide'] = misc_df['Ftide'] + df['Ftide'] # [Watts]
        v = v_lp_df.sum(axis=1).to_numpy()
        vt = vt_lp_df.sum(axis=1).to_numpy()
        svt = svt_lp_df.sum(axis=1).to_numpy()
        misc_df['V'] = v # [m3]
        
        # also create, from the hourly files, <s> 
        vh_df = pd.read_pickle(indir0 + 'flux/hourly_segment_volume.p')
        sh_df = pd.read_pickle(indir0 + 'flux/hourly_segment_salinity.p')
        vh_df = vh_df[seg_list]
        sh_df = sh_df[seg_list]
        svh_df = sh_df * vh_df # net salt in each segment (hourly)
        smeanh = svh_df.sum(axis=1).to_numpy() / vh_df.sum(axis=1).to_numpy()
        
        if old_dt:
            misc_df['Smean'] = sv_lp_df.sum(axis=1)/misc_df['V']
        else:
            smeanh_lp = zfun.filt_godin(smeanh)
            smean_lp = smeanh_lp[pad:-(pad+1):24]
            misc_df['Smean'] = smean_lp
        
        # volume budget
        vol_df = pd.DataFrame(0, index=indall, columns=['Qin','Qout'])
        for sect_name in tef_df_dict.keys():
            df = tef_df_dict[sect_name]
            vol_df['Qin'] = vol_df['Qin'] + df['Qin']
            vol_df['Qout'] = vol_df['Qout'] + df['Qout']
        vol_df['Qr'] = riv_df.sum(axis=1)
        if old_dt:
            vol_df.loc[1:-1, 'dV_dt'] = (v[2:] - v[:-2]) / (2*86400)
        else:
            vol_df.loc[:, 'dV_dt'] = vt
            
        vol_df['Error'] = vol_df['dV_dt'] - vol_df.loc[:,'Qin'] - vol_df.loc[:,'Qout'] - vol_df.loc[:,'Qr']
        vol_rel_err = vol_df['Error'].mean()/vol_df['Qr'].mean()

        # salt budget
        salt_df = pd.DataFrame(0, index=indall, columns=['QSin','QSout'])
        for sect_name in tef_df_dict.keys():
            df = tef_df_dict[sect_name]
            salt_df['QSin'] = salt_df['QSin'] + df['QSin']
            salt_df['QSout'] = salt_df['QSout'] + df['QSout']
        sn = sv_lp_df[seg_list].sum(axis=1).values
        if old_dt:
            salt_df.loc[1:-1, 'dSnet_dt'] = (sn[2:] - sn[:-2]) / (2*86400)
        else:
            salt_df.loc[:, 'dSnet_dt'] = svt
            
        salt_df['Error'] = salt_df['dSnet_dt'] - salt_df['QSin'] - salt_df['QSout']
        salt_rel_err = salt_df['Error'].mean()/salt_df['QSin'].mean()
        
        misc_df['Sin'] = salt_df['QSin']/vol_df['Qin']
        misc_df['Sout'] = salt_df['QSout']/vol_df['Qout']
        Socn = misc_df['Sin'].max() # used in mixedness budget
        
        # re-express the salt budget using Qe notation
        salt_qe_df = pd.DataFrame(index=indall)
        salt_qe_df['dSnet_dt'] = salt_df['dSnet_dt']
        
        misc_df['Qe'] = (vol_df['Qin'] - vol_df['Qout'])/2
        misc_df['Qnet'] = -(vol_df['Qout'] + vol_df['Qin']) # like Qr, but accounting for dV/dt
        misc_df['DS'] = misc_df['Sin'] - misc_df['Sout']
        misc_df['Sbar'] = (misc_df['Sin'] + misc_df['Sout'])/2
        # NOTE: Sbar is bad notation here, need to coordinate with Variance Budget usage of Smean.
        
        salt_qe_df['QeDS'] = misc_df['Qe']*misc_df['DS']
        salt_qe_df['-QrSbar'] = -misc_df['Qnet']*misc_df['Sbar']
        salt_qe_df['Error'] = salt_qe_df['dSnet_dt'] - salt_qe_df['QeDS'] - salt_qe_df['-QrSbar']
        salt_qe_rel_err_qe = salt_qe_df['Error'].mean()/salt_qe_df['QeDS'].mean()    
            
        # make sure everything is numeric
        for cn in misc_df.columns:
            misc_df[cn] = pd.to_numeric(misc_df[cn])
        for cn in vol_df.columns:
            vol_df[cn] = pd.to_numeric(vol_df[cn])
        for cn in salt_df.columns:
            salt_df[cn] = pd.to_numeric(salt_df[cn])
        for cn in salt_qe_df.columns:
            salt_qe_df[cn] = pd.to_numeric(salt_qe_df[cn])
            
        # save DataFrames to pickle files
        misc_df.to_pickle(outdir + 'misc_df_' + year_str + '_' + which_vol.replace(' ','_') + '.p')
        vol_df.to_pickle(outdir + 'vol_df_' + year_str + '_' + which_vol.replace(' ','_') + '.p')
        salt_df.to_pickle(outdir + 'salt_df_' + year_str + '_' + which_vol.replace(' ','_') + '.p')
            
        # accumulate error statistics (all %)
        err_df_vol.loc[year, which_vol] = vol_rel_err*100
        err_df_salt.loc[year, which_vol] = salt_rel_err*100
            
        # debugging: get net salt and salt-squared flux as a check
        if False:
            salt_df['QSnet'] = 0
            salt2_df['QS2net'] = 0
            tt0 = time()
            for sect_name in sect_sign_dict.keys():
                print('Debugging - processing ' + sect_name)
                sys.stdout.flush()
                sect_sign = sect_sign_dict[sect_name]
                ext_fn = indir0 + 'extractions/' + sect_name + '.nc'
                ext = nc.Dataset(ext_fn)
                ext_q = sect_sign * ext['q'][:]
                ext_salt = ext['salt'][:]
                xqs = ((ext_q * ext_salt).sum(axis=2)).sum(axis=1)
                xqs2 = ((ext_q * ext_salt * ext_salt).sum(axis=2)).sum(axis=1)
                xqs_lp = zfun.filt_godin(xqs)
                xqs2_lp = zfun.filt_godin(xqs2)
                pad = 36
                xqs_lp = xqs_lp[pad:-(pad+1):24]
                xqs2_lp = xqs2_lp[pad:-(pad+1):24]
                salt_df['QSnet'] += xqs_lp
                salt2_df['QS2net'] += xqs2_lp
                print('  -- took %0.2f sec' % (time()-tt0))
                sys.stdout.flush()
            salt_df['Error_alt'] = salt_df['dSnet_dt'] - salt_df['QSnet']
            salt2_df['Mix_numerical_alt'] = salt2_df['dS2net_dt'] - salt2_df['QS2net'] - salt2_df['Mix_resolved']
            
        # --------------- Volume and Salt Budgets --------------------------------------
        fig1 = plt.figure(figsize=(16,7))
        
        ax = fig1.add_subplot(121)
        vol_df[['dV_dt','Qin','Qout', 'Qr','Error']].plot(ax=ax, grid=True).legend(loc='upper right')
        ax.set_title('Volume Budget (m3/s)')
        ax.text(.05,.9, 'Mean Error / Mean Qr = %0.2f%%' % (vol_rel_err*100), transform=ax.transAxes, fontsize=14)

        ax = fig1.add_subplot(122)
        #salt_df[['dSnet_dt','QSin','QSout','Error']].plot(ax=ax, grid=True).legend(loc='upper right')
        salt_df.plot(ax=ax, grid=True).legend(loc='upper right')
        ax.set_title(year_str + ' ' + which_vol + ' Salt Budget (g/kg m3/s)')
        ax.text(.05,.9, 'Mean Error / Mean QSin = %0.2f%%' % (salt_rel_err*100), transform=ax.transAxes, fontsize=14)
        
        if save_figs:
            outname1 = outdir + 'vol_salt_budget_' + year_str + '_' + which_vol.replace(' ','_')
            fig1.savefig(outname1 + '.png')
        

        
plt.show()

