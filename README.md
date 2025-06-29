# VIPCALs

VLBI Pipeline for automated data Calibration using AIPS (in the SMILE
framework)

<div class="contents" data-depth="2" data-local="">

Contents

</div>

## Overview

VIPCALs is a fully automated calibration pipeline for Very Long Baseline
Interferometry (VLBI) data. It was developed as part of the SMILE
(Search for Milli-Lenses) project to process thousands of datasets
without human intervention.

Built on **ParselTongue** (a Python interface to AIPS), the pipeline
offers a minimalistic interface and produces fully calibrated datasets.

<div class="note">

<div class="title">

Note

</div>

The current version supports **continuum calibration of VLBA data**.
Support for other arrays is in development.

</div>

-----

## Requirements

**Manual installation:**

  - AIPS 31DEC24
  - conda

**Docker installation:**

  - docker
  - sudo privileges

**Singularity installation:**

  - singularity

-----

## Installation

### Manual Installation

1.  Clone the repository:
    
    ``` bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2.  Create the conda environment:
    
    ``` bash
    cd vipcals
    conda env create -f vipcalsenv.yml
    ```

3.  Activate the conda environment and install with:
    
    ``` bash
    conda activate pyside62
    pip install .
    ```

You can now launch VIPCALs with:

> 
> 
> ``` bash
> vipcals
> ```

### Docker Installation

1.  Clone the repository:
    
    ``` bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2.  Build the Docker container:
    
    ``` bash
    sudo docker build -t vipcals ./vipcals/dockerfiles/
    ```

3.  Run it:
    
    ``` bash
    sudo docker run -it --rm --net=host \
      --env DISPLAY=$DISPLAY \
      --env QT_X11_NO_MITSHM=1 \
      --volume /tmp/.X11-unix:/tmp/.X11-unix \
      -v /your_directory/:/usr/local/user vipcals
    ```
    
    where <span class="title-ref">/your\_directory/</span> has to be
    replaced with the local directory containing your data.

### Singularity Installation

1.  Clone the repository:
    
    ``` bash
    git clone https://gitlab.ia.forth.gr/smile/vipcals.git
    ```

2.  Build the Singularity image:
    
    ``` bash
    cd vipcals/dockerfiles
    singularity build vipcals.sif ./Singularity.def
    ```

3.  Run the image:
    
    ``` bash
    singularity run --overlay /tmp/ vipcals.sif
    ```

The singularity image *vipcals.sif* can be also moved/copied into any
other directory.

-----

## Usage

Upon opening the pipeline, you will be presented with two modes:

### Manual Input

This mode allows calibration of a single observation (which may include
multiple files) and lets you inspect the results via interactive plots.

**Minimum Required Inputs**

  - *User number*: AIPS user number *(manual installation only)*
  - *Disk number*: AIPS disk number *(manual installation only)*
  - *Filepath*: file(s) to calibrate
  - *Output directory*: directory for output products
  - *Target*: name(s) of science target(s) to calibrate

**Additional Options**

  - **Calibration Options**
    
      - *Calibrate all*: calibrate all sources (default: only science
        target(s))
      - *Phase ref calibrator*: define specific source(s) to use as
        phase reference calibrator(s)

  - **Loading Options**
    
      - *Load all sources*: load all sources (default: only science
        target(s) + 3 tentative calibrators)
      - *Time average threshold*: minimum integration time in seconds.
        If the data have a shorter time sampling, it will be averaged in
        time up to this value (0 to disable)
      - *Freq. average threshold*: minimum channel width in kHz. If the
        data have narrower channels, they will be averaged in frequency
        up to this value (0 to disable)
      - *Phase center shift*: give coordinates to shift the phase center
        of each target if more accurate positions are available. Format:
        <span class="title-ref">"175.858625 18.577322"</span> or
        <span class="title-ref">"11h43m26.07s +18d34m38.36s"</span>

  - **Reference Antenna Options**
    
      - *Reference antenna*: fixed reference antenna (e.g.,
        <span class="title-ref">"LA"</span>)
      - *Piority antennas*: list of preferred antennas to be used as
        reference antenna (e.g., <span class="title-ref">“LA”</span>,
        <span class="title-ref">“FD”</span>,
        <span class="title-ref">“EB”</span>)
      - *Search central antennas*: prioritize central array antennas
        (VLBA only)
      - *Maximum scans*: maximum number of scans per source to use in
        the automatic reference antenna search *(default: 10)*

  - **Fringe Fit Options**
    
      - *Fixed solution interval*: fixed solution interval in minutes
      - *Minimum solution interval*: minimum allowed interval (in
        minutes) when searching for the optimal solution interval
      - *Maximum solution interval*: maximum allowed interval (in
        minutes) when searching for the optimal solution interval

  - **Export Options**
    
      - *Channel out*:
        
          - \`SINGLE\`: before exporting, average in frequency to 1
            channel per IF
          - \`MULTI\`: export all channels
    
      - *Edge flagging*: when exporting:
        
        If \< 1: flag that fraction of edge channels at the
        beginning/end of each IF
        
        If ≥ 1 and integer: flag that number of edge channels at the
        beginning/end of each IF

  - **Plotting Options**
    
    \- *Interactive plots*: enable GUI plots (manual mode only) ..
    warning:: Generating these plots can consume lots of time and
    storage. It is advised to disable them for large datasets. Static
    <span class="title-ref">.ps</span> and
    <span class="title-ref">.pdf</span> plots are always saved in the
    output directory.

### JSON Input

For batch processing, inputs can be supplied via a JSON file. All
parameters mirror the manual input described above.

**Minimum JSON Fields**

| Key               | Type        |
| ----------------- | ----------- |
| userno            | int         |
| disk              | int         |
| paths             | list of str |
| targets           | list of str |
| output\_directory | str         |

**Optional JSON Fields**

| Key                       | Type                      |
| ------------------------- | ------------------------- |
| calib\_all                | bool                      |
| phase\_ref                | list of str               |
| load\_all                 | bool                      |
| time\_aver                | float                     |
| freq\_aver                | float                     |
| shifts                    | list of str               |
| refant                    | str                       |
| refant\_list              | list of str               |
| search\_central           | bool                      |
| max\_scan\_refant\_search | float                     |
| solint                    | float                     |
| min\_solint               | float                     |
| max\_solint               | float                     |
| channel\_out              | str ("SINGLE" or "MULTI") |
| flag\_Edge                | float                     |

**Examples**

``` json
{
  "userno": 4,
  "disk": 9,
  "paths": [
    "/data/pipeline_test_sample/diego/BR235/BR235M/VLBA_BR235M_br235m_BIN0_SRC0_0_210726T164755.idifits"
  ],
  "targets": ["1611+179", "1428+254", "1443+188"],
  "output_directory": "/home/dalvarez/vipcals/vipcals/101_200",
  "refant_list": ["LA", "FD"]
}

{
  "userno": 4,
  "disk": 9,
  "paths": [
    "/data/pipeline_test_sample/felix/BR235/BR235O/VLBA_BR235O_br235o_BIN0_SRC0_0_210217T213934.idifits"
  ],
  "targets": ["0912+237"],
  "output_directory": "/home/dalvarez/vipcals/vipcals/101_200",
  "shifts": ["138.72500917 23.53151889"]
}
```

Note that sources and coordinates in the *"phase\_ref"* and *"shifts"*
fields have to be given in the same order as the sources in the
*"targets"* field. If there is any source where those options should not
apply, then it can be skipped by giving a null value:

``` json
{
  "userno": 4,
  "disk": 9,
  "paths": [
    "/data/pipeline_test_sample/felix/BR235/BR235O/VLBA_BR235O_br235o_BIN0_SRC0_0_210217T213934.idifits"
  ],
  "targets": ["0737+171", "0912+237"],
  "phase_ref": ["0740+155", null]
  "output_directory": "/home/dalvarez/vipcals/vipcals/101_200",
  "shifts": [null, "138.72500917 23.53151889"]
}
```

-----

## Outputs

Below is a representative structure of the output directory produced by
the pipeline:

``` text
EA075/
├── J1159+2914_EA075_22G_2024-03-13/
│   ├── PLOTS/
│   │   ├ 1159+2914_EA075_22G_2024-03-13_CL1_POSSM.ps
│   │   ├ 1159+2914_EA075_22G_2024-03-13_CL9_POSSM.ps
│   │   ├ 1159+2914_EA075_22G_2024-03-13_UVPLT.ps
│   │   ├ 1159+2914_EA075_22G_2024-03-13_VPLOT.ps
│   │   ├ 1159+2914_EA075_22G_2024-03-13_RADPLOT.pdf
│   │
│   ├── TABLES/
│   │   ├ flags.vlba
│   │   ├ gaincurves.vlba
│   │   ├ tsys.vlba
│   │   ├ 1159+2914_EA075_22G_2024-03-13.caltab.uvfits
│   │
│   ├ 1159+2914_EA075_22G_2024-03-13.stats.csv
│   ├ 1159+2914_EA075_22G_2024-03-13.uvfits
│   ├ 1159+2914_EA075_22G_2024-03-13_AIPSlog.txt
│   ├ 1159+2914_EA075_22G_2024-03-13_scansum.txt
│   ├ 1159+2914_EA075_22G_2024-03-13_VIPCALslog.txt
│
│
├── J1143+1834_EA075_22G_2024-03-13/
│   ├── 
:   :
:   :
```

For each calibrated source, there is a directory that contains:

>   - *\*.stats.csv*: metadata on the observation and the calibration
>     process in csv format
>   - *\*.uvfits*: calibrated fits file
>   - *\*\_AIPSlog.txt*: output produced by AIPS after each step
>   - *\*\_scansum.txt*: summary of the observation including scan list
>     and frequency setup
>   - *\*\_VIPCALslog.txt*: human-readable summary of the calibration
>     produced by VIPCALs

The pipeline also generates the following plots inside the */PLOTS/*
folder:

>   - *\*\_CL1\_POSSM.ps*: uncalibrated visibilities vs frequency
>   - *\*\_CL9\_POSSM.ps*: calibrated visibilities vs frequency
>   - *\*UVPLT.ps*: UV coverage of the calibrated observation
>   - *\*VPLOT.ps*: calibrated visibilities vs time
>   - *\*RADPLOT.pdf*: calibrated visibilities vs uv-distance

and the following tables in the */TABLES/* folder:

>   - *flags.vlba*: initial flags of the observation (if not included in
>     the file)
>   - *gaincurves.vlba*: gain curves of each antenna (if not included in
>     the file)
>   - *tsys.vlba*: antenna system temperatures (if not included in the
>     file)
>   - *\*.caltab.uvfits*: AIPS tables used during the calibration

-----

## Acknowledgements

This work is supported by the European Research Council (ERC) under the
Horizon ERC Grants 2021 programme under grant agreement No. 101040021.