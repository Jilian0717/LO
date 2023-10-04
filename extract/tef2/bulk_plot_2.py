"""
An alternate version of bulk_plot.py, with the capability to combine two or more sections.

Unfortunately, because this job requires the hand inspection of the sections to decide
a consistent sign for all of them, it has a hard-coded "sect_list" to work from, and this
will be different for each user and for each section collection and grid. This is the kind of
code you would want to copy, modify, and keep in your own repo. Likely you would do
this in budget_functions.py.

To test on mac:
run bulk_plot_2 -gtx cas6_v00_uu0m -ctag c0 -0 2022.01.01 -1 2022.12.31 -test True


"""
import sys
import matplotlib.pyplot as plt
import numpy as np
import pickle
from time import time
import pandas as pd
import xarray as xr

from lo_tools import Lfun, zfun
from lo_tools import plotting_functions as pfun
import tef_fun

from lo_tools import extract_argfun as exfun
Ldir = exfun.intro() # this handles the argument passing

gctag = Ldir['gridname'] + '_' + Ldir['collection_tag']
tef2_dir = Ldir['LOo'] / 'extract' / 'tef2'

sect_df_fn = tef2_dir / ('sect_df_' + gctag + '.p')
sect_df = pd.read_pickle(sect_df_fn)

out_dir0 = Ldir['LOo'] / 'extract' / Ldir['gtagex'] / 'tef2'
in_dir = out_dir0 / ('bulk_' + Ldir['ds0'] + '_' + Ldir['ds1'])
if not Ldir['testing']:
    out_dir = out_dir0 / ('bulk_plots_2_' + Ldir['ds0'] + '_' + Ldir['ds1'])
    Lfun.make_dir(out_dir, clean=True)

if Ldir['testing']:
    # sect_list = [(('ai4',-1),('ai3',-1))]
    # sect_list = [(('mb9',1),('mb10',1))]
    # sect_list = [(('ss4',-1),('ss2',-1),('ss7',-1))]
    sect_list = [(('sji1',1),('sji2',1),('sji3',1))]
else:
    # NOTE: since this code is really only for working with combined sections
    # the default is a user specified list of tuples. If you want to look at
    # all the individual sections, use bulk_ploty.
    sect_list = [(('ai4',-1),('ai3',-1)),
        (('mb9',1),('mb10',1)),
        (('ss4',-1),('ss2',-1),('ss7',-1)),
        (('sji1',1),('sji2',1),('sji3',1))]
    
# NOTE: We handle combining sections by putting them in a tuple, and
# then each section is in its own tuple with a 1 or -1 to indicate the sign.
# The reason for the sign is that otherwise we have no way of knowing
# how to combine the two.
    
# grid info
g = xr.open_dataset(Ldir['grid'] / 'grid.nc')
h = g.h.values
h[g.mask_rho.values==0] = np.nan
xrho = g.lon_rho.values
yrho = g.lat_rho.values
xp, yp = pfun.get_plon_plat(xrho,yrho)
xu = g.lon_u.values
yu = g.lat_u.values
xv = g.lon_v.values
yv = g.lat_v.values

# PLOTTING
fs = 12
plt.close('all')
pfun.start_plot(fs=fs, figsize=(21,10))

for sect_name in sect_list:
    
    out_name = '_'.join([item[0] for item in sect_name])
    sign_dict = dict()
    tef_df_dict = dict()
    vn_list = ['salt'] # NOTE: this will need to be generalized to more tracers!
    for sn_tup in sect_name:
        sn = sn_tup[0]
        sign_dict[sn] = sn_tup[1]
        tef_df_dict[sn] = tef_fun.get_two_layer(in_dir, sn)
    ii = 1
    nsect = len(sect_name)
    for sn in tef_df_dict.keys():
        sgn = sign_dict[sn]
        if ii == 1:
            tef_df = tef_df_dict[sn].copy()
            tef_df[pd.isnull(tef_df)] = 0
            tef_df1 = tef_df.copy()
            for vn in vn_list:
                if sgn == 1:
                    tef_df[vn+'_q_p'] = tef_df1['q_p'] * tef_df1[vn+'_p']
                    tef_df[vn+'_q_m'] = tef_df1['q_m'] * tef_df1[vn+'_m']
                elif sgn == -1:
                    tef_df['q_p'] = -tef_df1['q_m']
                    tef_df['q_m'] = -tef_df1['q_p']
                    tef_df[vn+'_q_p'] = -tef_df1['q_m'] * tef_df1[vn+'_m']
                    tef_df[vn+'_q_m'] = -tef_df1['q_p'] * tef_df1[vn+'_p']
            tef_df['ssh'] *= 1/nsect
        else:
            tef_df1 = tef_df_dict[sn].copy()
            tef_df1[pd.isnull(tef_df1)] = 0
            for vn in vn_list:
                if sgn == 1:
                    tef_df['q_p'] += tef_df1['q_p']
                    tef_df['q_m'] += tef_df1['q_m']
                    tef_df[vn+'_q_p'] += tef_df1['q_p'] * tef_df1[vn+'_p']
                    tef_df[vn+'_q_m'] += tef_df1['q_m'] * tef_df1[vn+'_m']
                elif sgn == -1:
                    tef_df['q_p'] += -tef_df1['q_m']
                    tef_df['q_m'] += -tef_df1['q_p']
                    tef_df[vn+'_q_p'] += -tef_df1['q_m'] * tef_df1[vn+'_m']
                    tef_df[vn+'_q_m'] += -tef_df1['q_p'] * tef_df1[vn+'_p']
            for vn in ['qprism', 'qnet', 'fnet']:
                tef_df[vn] += sgn * tef_df1[vn]
            tef_df['ssh'] += tef_df1['ssh']/nsect
        ii+= 1
    for vn in vn_list:
        tef_df[vn+'_p'] = tef_df[vn+'_q_p'] / tef_df['q_p']
        tef_df[vn+'_m'] = tef_df[vn+'_q_m'] / tef_df['q_m']
            
    # adjust units
    tef_df['Q_p'] = tef_df['q_p']/1000
    tef_df['Q_m'] = tef_df['q_m']/1000
                    
    # labels and colors
    ylab_dict = {'Q': r'Transport $[10^{3}\ m^{3}s^{-1}]$',
                'salt': r'Salinity $[g\ kg^{-1}]$'}
    p_color = 'r'
    m_color = 'b'
    lw = 2
        
    fig = plt.figure()
    
    ax1 = plt.subplot2grid((2,3), (0,0), colspan=2) # Qin, Qout
    ax2 = plt.subplot2grid((2,3), (1,0), colspan=2) # Sin, Sout
    ax3 = plt.subplot2grid((1,3), (0,2)) # map
    
    ot = tef_df.index.to_numpy()
    
    ax1.plot(ot,tef_df['Q_p'].to_numpy(), color=p_color, linewidth=lw)
    ax1.plot(ot,tef_df['Q_m'].to_numpy(), color=m_color, linewidth=lw)
    ax1.grid(True)    
    ax1.set_ylabel(ylab_dict['Q'])
    ax1.set_xlim(ot[0],ot[-1])
    
    ax2.plot(ot,tef_df['salt_p'].to_numpy(), color=p_color, linewidth=lw)
    ax2.plot(ot,tef_df['salt_m'].to_numpy(), color=m_color, linewidth=lw)
    ax2.grid(True)
    ax2.set_ylabel(ylab_dict['salt'])
    ax1.set_xlim(ot[0],ot[-1])
    
    # map
    pfun.add_coast(ax3)
    pfun.dar(ax3)
    ax3.pcolormesh(xp, yp, -h, vmin=-100, vmax=100,
        cmap='jet', alpha=.4)
    
    if isinstance(sect_name,tuple):
        ii = 1
        nsect = len(sect_name)
        for sn_tup in sect_name:
            sn = sn_tup[0]
            sgn = sn_tup[1]
            sinfo = sect_df.loc[sect_df.sn==sn,:]
            i0 = sinfo.iloc[0,:].i
            j0 = sinfo.iloc[0,:].j
            uv0 = sinfo.iloc[0,:].uv
            i1 = sinfo.iloc[-1,:].i
            j1 = sinfo.iloc[-1,:].j
            uv1 = sinfo.iloc[-1,:].uv
            if uv0=='u':
                x0 = xu[j0,i0]
                y0 = yu[j0,i0]
            elif uv0=='v':
                x0 = xv[j0,i0]
                y0 = yv[j0,i0]
            if uv1=='u':
                x1 = xu[j1,i1]
                y1 = yu[j1,i1]
            elif uv1=='v':
                x1 = xv[j1,i1]
                y1 = yv[j1,i1]
            ax3.plot([x0,x1],[y0,y1],'-c', lw=3)
            ax3.plot(x0,y0,'og', ms=10)
            
            dx = x1-x0; dy = y1-y0
            print('%s dx=%0.3f dy=%0.3f' % (sn,dx,dy))
            print(sgn)
            xmid = (x0+x1)/2; ymid = (y0+y1)/2
            ax3.plot([xmid,xmid - sgn*dy/2],
                [ymid,ymid + (sgn*np.cos(np.pi*ymid/180)*dx/2)], '-+r')
                
            # accumulate limits
            if ii == 1:
                xmin=min((x0,x1))
                xmax=max((x0,x1))
                ymin=min((y0,y1))
                ymax=max((y0,y1))
            else:
                xmin=min((xmin,min((x0,x1))))
                xmax=max((xmax,max((x0,x1))))
                ymin=min((ymin,min((y0,y1))))
                ymax=max((ymax,max((y0,y1))))
            if ii == len(sect_name):
                pad = .1
                ax3.axis([xmin-pad,xmax+pad,ymin-pad,ymax+pad])
                ax3.set_xlabel('Longitude [deg]')
                ax3.set_ylabel('Latitude [deg]')
                ax3.set_title(str(sect_name))
                
            ii += 1
            
    else:
        sn = sect_name
        sinfo = sect_df.loc[sect_df.sn==sn,:]
        i0 = sinfo.iloc[0,:].i
        j0 = sinfo.iloc[0,:].j
        uv0 = sinfo.iloc[0,:].uv
        i1 = sinfo.iloc[-1,:].i
        j1 = sinfo.iloc[-1,:].j
        uv1 = sinfo.iloc[-1,:].uv
        if uv0=='u':
            x0 = xu[j0,i0]
            y0 = yu[j0,i0]
        elif uv0=='v':
            x0 = xv[j0,i0]
            y0 = yv[j0,i0]
        if uv1=='u':
            x1 = xu[j1,i1]
            y1 = yu[j1,i1]
        elif uv1=='v':
            x1 = xv[j1,i1]
            y1 = yv[j1,i1]
        ax3.plot([x0,x1],[y0,y1],'-c', lw=3)
        ax3.plot(x0,y0,'og', ms=10)
        
        dx = x1-x0; dy = y1-y0
        xmid = x0 + dx/2; ymid = y0 + dy/2
        pad = np.max((np.sqrt(dx**2 + dy**2)*2,.1))
        ax3.axis([x0-pad, x1+pad, y0-pad, y1+pad])
        ax3.set_xlabel('Longitude [deg]')
        ax3.set_ylabel('Latitude [deg]')
        ax3.set_title(str(sect_name))
        ax3.plot([xmid,xmid - dy/2],
            [ymid,ymid + np.cos(np.pi*ymid/180)*dx/2], '-+r')
                
    # fig.tight_layout()
    
    if Ldir['testing']:
        plt.show()
    else:
        plt.savefig(out_dir / (out_name + '.png'))
        plt.close()

pfun.end_plot()
