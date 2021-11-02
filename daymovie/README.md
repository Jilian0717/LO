# README for daymovies

### This is highly specialized plotting code designed to make the daily forecast movies that are pushed to the LiveOcean website.  It replaces the plot5 folder from LiveOcean.

---

`dm_plot.py` is the main program for making a plot/movie. It is designed to be run completely using command line arguments, because its main role is to be called repeatedly by `post/daymovies/post_main.py` (which itself is called by `driver/post_driver.py`).

Many of the command line arguments end up encoded in the resulting filename, which is structured as:

- [plot name]\_[domain]\_[variable name]\_[top or bottom] = (*)

If you just make a snapshot the output is a plot on your screen, but if you are making a movie (the standard use case) then the output goes to:

- LO_output/daymovie/[gtagex]/(*)/movie.mp4

along with all the png's that went into it.  Question: should I include a date string in the path?

---

`plots.py` specifies the (very few) plot types that are called by `dm_plot.py`.

Each plot is some sort of map field, maybe some particle tracks, with a time series of tide height below it and a little wind vector.

---

`dm_pfun.py` is a module of specialized functions used by the plotting code, such as creating a time series of SSH and wind, doing a particle tracking run, calculating aragonite saturation state, etc.

One important method is `get_ax_limits()` which is where that spatial extend of each "domain" is defined.

---

`pinfo.py` is a module that defines several dicts with things like scaling factors, colormaps, long names, and colormap limits.