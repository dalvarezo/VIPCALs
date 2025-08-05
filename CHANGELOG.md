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