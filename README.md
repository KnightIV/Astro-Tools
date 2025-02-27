# Astro-Tools
Collection of utility scripts made during my master's thesis at the UANL.

## Contact binary q-search (`cbs-q-search.py`)

Run a q-search algorithm for a given contact binary system using PHOEBE. Tests a grid of `q` values for the specified fixed orbital inclination values, finding the best fit by adjusting the system's *fillout factor* and *effective temperature ratio* using a Nelder-Mead Simplex optimizer. Outputs all individual solutions obtained from the optimization.

### Requirements

* `python>=3` (tested as is with Python 3.12.2)
* `phoebe`
* `tqdm`

## Align FITS images (`align-images.py`)

Aligns scientific FITS images such that targets overlap in pixel-space. Uses the FITS [**World Coordinate System**](https://www.atnf.csiro.au/computing/software/wcs/) (**WCS**) to project all images in a single directory onto the first image encountered. This facilitates aperture photometry using tools (eg. IRAF) that rely on pixel coordinates.

This script makes the following assumptions:
* All of the FITS images in the directory can be projected onto each other. I used this on a per-night basis, never mixing across multiple nights of observations.
* If an image cannot be plate-solved it must be unusable and not included in the final results.
* No calibration (bias, dark, or flat) is applied at any stage in the process.

### Requirements:

* `python>=3` (tested as is with Python 3.12.2)
* `tqdm`

#### Astrometry
This script also makes use of [**Astrometry**](https://nova.astrometry.net) for the plate-solve routine. In particular you must install the `solve-field` command from the `astrometry` package.

Ubuntu:
```sh
sudo apt install astrometry
```

Fedora:
```sh
sudo dnf install astrometry
```

In order to plate-solve the fields obtained with the 0.5m CDK telescope at the *Observatorio Astronómico Universitario - Iturbide* I needed a total of ~10GB for the required data files. These can be downloaded using the [`download-astrometry-data.sh`](https://github.com/KnightIV/Observation-Tools/blob/main/bash-scripts/download-astrometry-data.sh) script, which will place these data files in the proper directory for `solve-field` to find.