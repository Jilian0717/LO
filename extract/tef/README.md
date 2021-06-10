# README for the tef code

### This is code to do TEF extractions and processing. The code also works on the segments between TEF sections, for example to make volume-integrated budgets of volume, salt and salinity variance.

#### WORKFLOW OVERVIEW

In order to get to where you can run `flux_salt_budget.py` you first need to go through two separate workflows because these prepare the independent information at (1) TEF sections, and (2) segments between the sections.

(1) TEF sections:
 - `extract_sections.py`
 - `process_sections.py`
 - `bulk_calc.py`

(2) Segments (the flux_ code):
 - `flux_get_vol.py`
 - `flux_get_s.py`
 - `flux_lowpass_s.py`

Then you can run `flux_salt_budget.py`

NOTES:
- All extraction transports are positive Eastward and Northward.
- We keep velocity and area of each cell, instead of just transport.
- We have the option to keep more variables (e.g. temp, oxygen, and NO3), by editing vn_list in `extract_sections.py`, but the subsequent processing is not yet carried through the other code.

---

`ptools/pgrid/tef_section_maker.py` is a tool to define sections, if needed.  This is a GUI where you define section endpoints (forced to be either perfectly E-W or N-S), name the section, and define which direction is "landward" (i.e. which way is positive transport).  You can define one or more sections in a session.  At the end, when you push DONE it produces screen output suitable for pasting into new or existing lists in `tef_fun.get_sect_df()`.

---

`tef_fun.py` is an important module for this code. Includes `tef_fun.get_sect_df()` which returns a DataFrame of all the section names and their lon,lat endpoints. The entries in this are pasted in by hand while using `tef_section_maker.py` as documented above. Then to control which sections will be processed by later programs (like to do extractions) you comment/uncomment lines in this function. This is not great coding - it might be better to have one function that returns the info for any section name, and then make specific lists for specific projects.

---

`extract_sections.py` creates a NetCDF file for each section with arrays of hourly transport and tracer values on the section, arranged as (t, z, x-or-y). Using command line arguments you can change the run and the day range. When you run the code you can decide at the command line to extract all the sections from the list, or just one. The main list is defined in `tef_fun.get_sect_df()`. Typically this will be done on a remote machine, like boiler, although the defaults are designed to work with model output I have saved on my mac.

Input: ROMS history files over some date range

Output: LO_output/extract/[gtagex]/tef/extractions_[\*]/[sect name].nc where:

- [\*] = 2017.01.01_2017.12.31 for example

Variables: ocean_time, salt, q, z0, DA0, lon, lat, h, zeta
- salt is hourly salinity in each cell (t, z, y-or-x)
- q is hourly transport in each cell (t, z, y-or-x)
- vel is velocity in each cell (t, z, y-or-x) positive to East or North
- DA is the area of each cell (t, z, y-or-x) hence: q = vel * DA
- z0 is the average depth of cell centers (assumes SSH=0)
- DA0 is the average cross-sectional area of each cell (assumes SSH=0)
- h is depth on the section (y-or-x) positive down
- zeta is SSH on the section (t, y-or-x) positive up
- ocean_time is a vector of time in seconds since (typically) 1/1/1970.

---

`process_sections.py` organizes all the transports at each time into salinity bins.

Input: the output NetCDF files from `extract_sections.py`

Output: LO_output/extract/[gtagex]/tef/processed_[\*]/[sect name].p

- a pickled dict with keys: ['tef_q','tef_vel','tef_da', 'tef_qs', 'sbins', 'ot', 'qnet', 'fnet', 'ssh']

These are defined as:

- tef_q transport in salinity bins, hourly, (m3/s)
-	tef_da area in salinity bins, hourly, (m2)
-	tef_qs salt transport in salinity bins, hourly, (g/kg m3/s)
-	tef_qs2 salinity-squared transport in salinity bins, hourly, (g2/kg2 m3/s)
-	sbins the salinity bin centers
-	ot ocean time (sec from 1/1/1970)
-	qnet section integrated transport (m3/s)
-	fnet section integrated tidal energy flux (Watts)
-	ssh section averaged ssh (m)

Packed in order (time, salinity bin).

NOTE: we create tef_vel as the flux-weighted velocity: tef_vel = tef_q/tef_da.

---

`bulk_calc.py` does the TEF bulk calculations, using the algorithm of Marvin Lorenz, allowing for multiple in- and outflowing layers

Input: LiveOcean_output/tef2/[*]/processed/[sect name].p

Output: LiveOcean_output/tef2/[*]/bulk/[sect name].p

These are pickled dicts with keys: ['QQ', 'SS', 'SS2', 'ot', 'qnet_lp', 'fnet_lp', 'ssh_lp']
where ot is a time vector (seconds since 1/1/1970 as usual), and QQ is a matrix of shape (362, 30) meaning that it is one per day, at Noon, after tidal-averaging, with nan-days on the ends cut off.  The 30 is the number of "bulk" bins, so many might be filled with nan's.  SS2 is salinity-squared, used later for variance budgets.

---

* bulk_plot_clean.py plots the results of bulk_calc.py, either as a single plot to the screen, or multiple plots to png's.  You need to edit the code to run for other years.

Input: LiveOcean_output/tef2/[*]/bulk/[sect name].p

Output: LiveOcean_output/tef2/[*]/bulk_plots_clean/[sect name].p

---

NOTE: The code with "flux_" at the start of its name is focused on the "efflux_reflux" concepts of Cokelet and Stewart (1985, and subsequent).  It picks up the TEF analysis from the point where we have done all the TEF sections, averaged into "bulk" inflows and outflows.  At that point we start working toward a super-simple numerical model in which the tracer concentation in "segments" (the volume in between two or more "sections") can be calculated as dynamically evolving functions of time.

---

`flux_fun.py` is a module used throughout this code.

A key piece is the dict flux_fun.segs where we set up the segment names and define (i) the sections on each direction NSEW, and (ii) the rivers flowing into each segment.  This is created by hand while looking at the plots created by flux_seg_map.py below.

A key item is the dict "segs" which whose keys are the segment names, and whose values are in turn dicts which define lists of sections surrounding a segment, and a list of rivers.

```
segs = {
        'J1':{'S':[], 'N':[], 'W':['jdf1'], 'E':['jdf2'], 'R':['sanjuan', 'hoko']},
        etc...
      }
```

Originally this was created by looking at the plot made by `plot_thalweg_mean.py`, but the same information is shown more clearly now in the plots made by `flux_seg_map.py` below.

Also has channel_dict, seg_dict, other things which associate lists of sections or segments with each of four "channels".

`flux_fun.make_dist(x,y)` makes vectors of distance along lon,lat vectors x,y

---

* flux_get_vol.py gets the volume (with SSH = 0) of each segment.  Uses a cute "mine sweeper" like algorithm to find all the unmasked rho-grid cells on the grid between the sections that define a segment.

Input: flux_fun.segs, the model grid (hard wired in the code to be cas6), and sect_df = tef_fun.get_sect_df().

Output: LiveOcean_output/tef2/volumes_cas6/...
	volumes.p a pickled DataFrame with segment names for the index and columns: ['volume m3', 'area m2', 'lon', 'lat']
	bathy_dict.p pickled dict of the grid bathy, for plotting
	ji_dict.p pickled dict (keys = segment names) of the ji indices of each segment area, also for plotting

---

* flux_get_s.py creates time series of hourly salinity and volume in segments, over a user specified (like a year) period.  Now includes files for the salinity-squared and the net "mixing" (variance destruction due to vertical and horizontal mixing).

Input: ROMS history files

Output: LiveOcean_output/tef2/[*]/flux/hourly_segment_[volume,salinity,mix,salinity2].p, pickled DataFrames where the index is hourly datetime and the columns are the segments.

NOTE: [*] = cas6_v3_lo8b_2017.01.01_2017.12.31, e.g., here and below.

---

* flux_lowpass_s.py creates time series of daily salinity, volume, and net salt in segments.

Input: LiveOcean_output/tef2/[*]/flux/hourly_segment_[volume,salinity,mix,salinity2].p

Output: LiveOcean_output/tef2/[*]/flux/daily_segment_[volume,salinity,net_salt,mix,salinity2,net_salt2].p

---

* flux_salt_budget.py makes complete volume, salt, salinty-squared, and S'^2 budgets for a user-specified set of segments.
These budgets are of the form:
	dSnet/dt = QSin + QSout, and
	dV/dt = Qin + Qout + Qr
    and so on...
They are useful for knowing that the budgets add up in each of the basins and years to reasonable accuracy.  The values plotted are DAILY (tidally averaged).

Input: LiveOcean_output/tef2/[*]/flux/hourly_segment_[volume,net_salt].p, also some river extractions in LiveOcean_output/river/.

Output: A screen plot of the budget vs. time, and a saved png such as:
LiveOcean_output/tef2/salt_budget_plots/salt_budget_2017_Salish_Sea.png, also related pickled DataFrames.  See the code for exact names.

---

To document:
 - profiles.py
 - profile_plot.py
 - flux_sill_dyn_all.py
 - flux_get_dye.py
 - flux_mixing_diagram.py