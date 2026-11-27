## [0.4.0] - 2026-11-27

### Added
- External flag tables in AIPS UVFLG format can now be given as an input. Their flags are added to the initial flag table and a copy is saved in the /TABLES folder.
- Datasets with any number of frequency bands are now supported, and the IFs of a band no longer need to be consecutive in the file. Bands are split wherever there is a gap larger than 500 MHz between IFs.
- The log now shows the percentage of remaining visibilities after each calibration step.
- For EVN datasets without initial flags, the flag file is now also retrieved from the EVN archive.
- Instructions to run the pipeline from the command line have been added to the documentation.

### Changed
- IMPORTANT: The conda environment is now called vipcalsenv (previously pyside62). Manual installations need to create the new environment and reinstall the pipeline.
- System temperatures retrieved online are now matched to the loaded IFs by frequency.
- The online search for VLBA calibration tables is now faster, and EVN antab files are also searched in their uncompressed and numbered versions.
- Edge channel flagging is now also applied in the target fringe fit and in the POSSM and VPLOT plots.
- The CLCAL interpolation cutoff when fringe fitting on the science target is now the longest solution interval, so solutions are not applied to neighbouring scans.
- Earth orientation parameter corrections are skipped for EVN datasets and for incompatible CT tables.
- Visibilities vs uv-distance plots now shows Stokes I with the Difmap phase convention. Before, only RR was plotted.
- Visibilities vs time plots now apply the bandpass correction.
- Updated the documentation.

### Fixed
- Fixed bug that would cause the pipeline to crash when the number of edge channels was given as an integer.
- Fixed bug where, with "Calibrate all" and multiple frequency bands, the sources of one band were used as targets of the next one.
- Fixed bug where AIPS names longer than 12 characters were not shortened for single-band datasets.
- Fixed error when some entries of the phase-reference calibrator list were empty.
- Fixed errors with paths containing special characters such as & or spaces.
- Fixed bug that would cause the pipeline to fail when none of the sources was included in the VLBA calibrator list.
- Fixed package incompabilities in the conda environment.

## [0.3.7] - 2026-03-13

### Changed
- All plots produced within AIPS are now converted from .ps to .pdf. This requires a new package in the pyside62 conda environment, that needs to be reinstalled in the manual installation.
- When multiple files are available, the date used in the naming of the folders and files corresponds to the earliest of the observing dates. Before, it was the date of the first file loaded into the pipeline.

### Fixed
- Fixed error that would cause the pipeline to crash at the plotting step if more than 9 phase center shifts were requested.
- Fixed error that would cause the pipeline to crash when calibrating multiple sources from non-DiFX-correlated datasets.
- Fixed minor bug that would cause the reference antenna algorithm to fail when there were consecutive empty scans. 
- Fixed minor bug that would make the GUI display only the name of the last calibration table retrieved online, even when multiple tables were used. 
- Fixed minor bug that would cause the names of the antennas in the calibrator search to appear duplicated in the logs.
- Fixed minor bug that would cause the .txt log to be incomplete under very specific circunstances.

## [0.3.6] - 2025-10-14

### Changed
- Crossmatch for potential calibrators in the VLBA calibrator list is now done in a 1 arcsecond radius, from previous 5 arcseconds. Given the accuracy of the coordinates, this value is more realistic.
- Small improvements in the GUI

### Fixed
- Fixed error in CLCAL where the interpolation was not being done as intended.

## [0.3.5] - 2025-09-18
### Added
- Visibilities per antenna across the different calibration steps are now included as .pdf plot in the /PLOTS directory.

### Changed
- Interactive visibilities vs time plots now show the timestamps in DD/HH:MM:SS since the beginning of the observation.
- Interactive visibilities vs frequency plots now render much faster, especially when iterating over baselines.
- Default solution interval for ACCOR and ACSCL (normalization of autocorrelations) changed from 3 to 10 minutes, seems to be more stable for lower frequencies.

### Fixed
- Fixed bug that was causing the pipeline to not merge redundant tables, causing problems when concatenating multiple files.
- Now flagged channels are correctly displayed in the interactive visibilities vs frequency plots.
- Fixed bug when generating plots of targets with very long names.

## [0.3.4] - 2025-08-19
### Added
- Now the pipeline will raise an error when the dataset does not contain autocorrelation data, which makes amplitude calibration not possible.

### Changed
- Text color in the GUI changed from white to light gray, making it easier to copy-paste into a text editor. 

### Fixed
- Fixed bug that would cause the pipeline to stop when output directory names were longer than allowed by AIPS tasks. Now any name length should be allowed.
- Fixed bug in the Docker version which would prevent error messages to be displayed.

## [0.3.3] - 2025-08-17
### Added
- EVN datasets can now be loaded and calibrated by VIPCALs. This is still under active development, and calibration might not be optimal in some cases.
- Antenna system temperatures as a function of time, both original and smoothed, are now also printed in PS format into the /PLOTS folder. 

### Changed
- Optimized the size of the interactive plots generated for the GUI, now they are ~90% smaller.
- The log now clearly states when an antenna has been flagged due to all their system temperature values being off the limits (0K - 1500K)

### Fixed
- Fixed major bug that prevented the pipeline from reading input fits files while in docker mode. How to run instructions have been updated to reflect the changes. 
- Fixed bug where the reference antenna search would always give priority to the central VLBA antennas, even when that option was disabled.
- Added a sanity check for the "Edge flagging" option, in previous versions the pipeline would crash when given a non-valid value. 

## [0.3.2] - 2025-08-10
### Changed
- Updated installation instructions in README.md. Docker installation should now work on MacOS with DockerDesktop and XQuartz installed.
- Removed Singularity installation. 

### Fixed
- Fixed bug where the phase-reference calibration would not work as intended.

## [0.3.1] - 2025-08-05
### Changed
- Improvements in the log: now the antennas available in the dataset are written alongside the basic information of the dataset. 
- Improvements in the log: the "Reference antenna search" step is more verbose now, specifying explicitly which antennas are not taken into account during the selection.
- Improvements in the log: now antenna numbers are always shown alongside the antenna name.
- If multiple frequency IDs are available, VIPCALs will now check if the selected science targets have been observed at each frequency. If not, it will print a message on the screen and skip that frequency.

### Fixed
- Fixed bug where the pipeline would crash if trying to concatenate multiple files with only 1 IF.
- Fixed bug where some data were lost when trying to load files with both multiple frequency IDs and multiple bands in consecutive IFs.
- Fixed other minor bugs.

## [0.3.0] - 2025-07-27
### Added
- Added CHANGELOG.md
- TY and GC tables in ANTAB format can now be manually loaded instead of being searched for automatically by the pipeline.
- The signal-to-noise threshold for the fringe fit on the science target (or the phase-reference calibrator) can now be given as an input.
- Added sanity checks when loading multiple files simultaneously: the pipeline will not continue if the number of channels, the number of IFs, the number of Stokes parameters, the reference channel, and the frequency of each IF are not exactly equal across files.
- Now a small message with a summary of the fringe fit results is printed on the GUI at the end of the pipeline.

### Changed
- The fringe fit used during the instrumental phase correction now takes full advantage of FRING search parameter, effectively using all antennas and reducing failed solutions.
- Now the time average is only produced if there are at least two visibilities per averaging bin, e.g. average in 2 seconds only happens if the time sampling is <= 1 second. 
- Now full paths are printed into the GUI and the log, instead of relative paths.
- Minor appearance improvements on the GUI.

### Fixed
- Fixed bug when generating outputs of targets with very long names.
- Fixed bug where polarizations were not interpreted properly when loading TY tables.
- Fixed bug where manually input solutions interval were not being read properly.
- Modified order of packages in the conda environment instructions, that should fix some installation issues.
- Fixed other minor bugs.

## [0.2.0] - 2025-06-30
### Added
- Initial release.