# VIPCALs

**VLBI Pipeline for automated data Calibration using AIPS (in the SMILE framework)**

## Overview

VIPCALs is a fully automated calibration pipeline for Very Long Baseline Interferometry (VLBI) data.  
It was developed as part of the SMILE (Search for Milli-Lenses) project to process thousands of datasets without human intervention.

Built on **ParselTongue** (a Python interface to AIPS), the pipeline offers a minimalistic interface and produces fully calibrated datasets.

> **Note**  
> The current version supports **continuum calibration of VLBA data**. Support for other arrays is in development.

---

## Requirements

### Manual installation

- AIPS 31DEC24  
- conda

### Docker installation

- docker  
- sudo privileges

### Singularity installation

- singularity

---

## Installation

### Manual Installation

1. Clone the repository:

    ```bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2. Create the conda environment:

    ```bash
    cd vipcals
    conda env create -f vipcalsenv.yml
    ```

3. Activate the conda environment and install with:

    ```bash
    conda activate pyside62
    pip install .
    ```

You can now launch VIPCALs with:

```bash
vipcals
```

### Docker Installation

1. Clone the repository:

    ```bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2. Build the Docker container:

    ```bash
    sudo docker build -t vipcals ./vipcals/dockerfiles/
    ```

3. Run it:

    ```bash
    sudo docker run -it --rm --net=host \
        --env DISPLAY=$DISPLAY \
        --env QT_X11_NO_MITSHM=1 \
        --volume /tmp/.X11-unix:/tmp/.X11-unix \
        -v /your_directory/:/usr/local/user vipcals
    ```

Replace `/your_directory/` with your local data directory.

### Singularity Installation

1. Clone the repository:

    ```bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2. Build the Singularity image:

    ```bash
    cd vipcals/dockerfiles
    singularity build vipcals.sif ./Singularity.def
    ```

3. Run the image:

    ```bash
    singularity run --overlay /tmp/ vipcals.sif
    ```

The image `vipcals.sif` can be moved or copied to any other directory.

---

## Usage

Upon starting the pipeline, two modes are available: manual and JSON input.

### Manual Input

This mode allows calibration of a single observation and offers interactive plotting.

#### Minimum Inputs

- **User number**: AIPS user number
- **Disk number**: AIPS disk number
- **Filepath**: file(s) to calibrate
- **Output directory**: directory for output products
- **Target**: science target(s) to calibrate

#### Additional Options

**Calibration Options**

- Calibrate all sources
- Use specific phase reference calibrators

**Loading Options**

- Load all sources
- Time average threshold
- Frequency average threshold
- Phase center shift (e.g., `"175.858625 18.577322"` or `"11h43m26.07s +18d34m38.36s"`)

**Reference Antenna Options**

- Fixed or preferred reference antennas
- Search central antennas (VLBA only)
- Max scans to use for reference antenna detection

**Fringe Fit Options**

- Fixed, min, and max solution interval in minutes

**Export Options**

- Channel output: `SINGLE` or `MULTI`
- Edge flagging: fractional or integer edge channels to flag

**Plotting Options**

- Enable GUI plots (⚠️ time- and space-consuming for large datasets)

### JSON Input

Useful for batch processing. All manual parameters are mirrored.

#### Required Fields

```json
{
  "userno": 4,
  "disk": 9,
  "paths": ["<input_file>"],
  "targets": ["<target>"],
  "output_directory": "<output_dir>"
}
```

#### Optional Fields

Include `calib_all`, `phase_ref`, `load_all`, `time_aver`, `freq_aver`, `shifts`, `refant`, `refant_list`, `search_central`, `max_scan_refant_search`, `solint`, `min_solint`, `max_solint`, `channel_out`, `flag_Edge`.

#### Examples

```json
{
  "userno": 4,
  "disk": 9,
  "paths": ["<file1>"],
  "targets": ["source1", "source2"],
  "output_directory": "/some/path",
  "refant_list": ["LA", "FD"]
}
```

```json
{
  "userno": 4,
  "disk": 9,
  "paths": ["<file2>"],
  "targets": ["0737+171", "0912+237"],
  "phase_ref": ["0740+155", null],
  "shifts": [null, "138.72500917 23.53151889"]
}
```

---

## Outputs

Example structure:

```
EA075/
├── J1159+2914_EA075_22G_YYYY-MM-DD/
│   ├── PLOTS/
│   ├── TABLES/
│   ├── *.stats.csv
│   ├── *.uvfits
│   ├── *_AIPSlog.txt
│   ├── *_scansum.txt
│   ├── *_VIPCALslog.txt
```

### Output types

- **CSV**: Calibration metadata
- **UVFITS**: Calibrated data
- **Logs**: AIPS log, scan summary, VIPCALs summary
- **Plots**: POSSM, UVPLT, VPLOT, RADPLOT
- **Tables**: flags, gaincurves, tsys, AIPS calibration tables

---

## Acknowledgements

This work is supported by the European Research Council (ERC) under the Horizon ERC Grants 2021 programme under grant agreement No. 101040021.