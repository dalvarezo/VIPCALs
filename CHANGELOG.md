## [0.3.6] - 2025-10-14
### Added

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