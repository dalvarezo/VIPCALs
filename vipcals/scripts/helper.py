import numpy as np

from AIPS import AIPS
from AIPSTask import AIPSTask

################################################
####                Exceptions               ####
################################################

class NoTablesError(Exception):
    """Raised when no VLBA calibration tables are found."""
    pass

class NoScansError(Exception):
    """Raised when no suitable scans for calibration are found."""
    pass

################################################
####                Classes               ####
################################################

class Antenna():
    """Antennas within an observation"""
    def __init__(self):
        self.name = None
        self.id = None
        self.sources_obs = []
        self.coords = None
        self.dist = None
        self.scans_obs = []
        self.median_SNR = 0
        self.max_scans = 0

class FFTarget():
    """Helper class to simplify the fringe fit workflow."""
    def __init__(self):
        self.name = None
        self.phaseref = 'NONE'
        self.solint = None
        self.log = None

class GC_entry():
    """Entries from the master gain curve (vlba_gains.key)"""
    def __init__(self):
        self.initime = None
        self.finaltime = None
        self.band = None
        self.antenna = None
        self.entry = None

class Scan():
    """Scans within an observation.""" ## SHOULD BE MERGED WITH THE Scan() CLASS
    def __init__(self):
        self.id = None
        self.source_id = None
        self.source_name = None
        self.snr = []
        self.time = None
        self.time_interval = None
        self.antennas = []
        self.calib_antennas = []
        self.calib_snr = []
    def get_antennas(self, time_to_antennas):
        half_interval = self.time_interval / 2
        time_min = self.time - half_interval
        time_max = self.time + half_interval

        antennas = set()
        for t in time_to_antennas:
            if time_min < t < time_max:
                antennas.update(time_to_antennas[t])

        self.antennas = list(antennas)

class Source():
    """Sources within a fits file."""
    def __init__(self):
        self.name = None
        self.id = None
        self.inlist = None
        self.restfreq = None
        self.band = None
        self.band_flux = np.NaN
        self.coord = None
        self.ra = None
        self.dec = None
        
    def set_band(self):
        """Set band name depending on rest frequency."""
        if self.restfreq < 1e9:
            self.band = 'P'
        elif self.restfreq < 2e9:
            self.band = 'L'
        elif self.restfreq < 3e9:
            self.band = 'S'
        elif self.restfreq < 7e9:
            self.band = 'C'
        elif self.restfreq < 1e10:
            self.band = 'X'
        elif self.restfreq < 1.8e10:
            self.band = 'U'
        elif self.restfreq < 2.6e10:
            self.band = 'K'
        elif self.restfreq < 5e10:
            self.band = 'Ka'
        else:
            self.band = 'W'

class MultiFile:
    """Class that allows to write in mutiple files simulatenously.
    
    In ParselTongue, the AIPS log can be dumped into any object with the write method. 
    This class imitates the File class in Python and allows the AIPS log to be written 
    simultaneously in multiple files, which correspond to the multiple sources being 
    calibrated.
    """
    def __init__(self, *file_paths, mode='r'):
        """
        Initialize the MultiFile object with multiple file paths.
        """
        self.files = [open(file_path, mode) for file_path in file_paths]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def read(self):
        """
        Reads from all files and returns their content concatenated.
        """
        return ''.join(file.read() for file in self.files)

    def write(self, data):
        """
        Writes the given data to all files.
        """
        for file in self.files:
            file.write(data)

    def close(self):
        """
        Closes all opened files.
        """
        for file in self.files:
            file.close()

    def readlines(self):
        """
        Reads lines from all files and returns a list of lists, each 
        containing lines from one file.
        """
        return [file.readlines() for file in self.files]

    def writelines(self, lines):
        """
        Writes a list of lines to all files.
        """
        for file in self.files:
            file.writelines(lines)

    def seek(self, offset, whence=0):
        """
        Moves the file pointer to a new position in all files.
        """
        for file in self.files:
            file.seek(offset, whence)

    def tell(self):
        """
        Returns the current position of the file pointer from the first file.
        """
        return self.files[0].tell()

    def flush(self):
        """
        Flushes the write buffer of all files.
        """
        for file in self.files:
            file.flush()

    def __iter__(self):
        """
        Iterates over the lines of the first file. (This can be adjusted to 
        iterate over all files if needed).
        """
        return iter(self.files[0])

    def __repr__(self):
        return f"MultiFile({[file.name for file in self.files]}, \
            mode={self.files[0].mode})"

################################################
####                Functions               ####
################################################

def ddhhmmss(time):
    """Convert decimal dates into AIPS dd hh mm ss format.

    :param time: decimal date
    :type time: float
    :return: 1D array with day, hour, minute and second
    :rtype: ndarray
    """   
    total_seconds = int(time * 24 * 60 * 60)
    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return np.array([days,hours,minutes,seconds])

def open_log(path_list, filename_list):
    """Create a log.txt to store AIPS outputs.

    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param filename_list: list of file names
    :type filename_list: list of str
    """
    log_paths = []
    for i, path in enumerate(path_list):
        log_paths.append(path + '/' + filename_list[i] + '_AIPSlog.txt')

    AIPS.log = MultiFile(*log_paths, mode = 'w')

def tacop(data, ext, invers, outvers):
    """Copy one calibration table to another.

    Copies one AIPS calibration table from one version to another one.

    :param data: visibility data
    :type data: AIPSUVData
    :param ext: table extension
    :type ext: str
    :param invers: input version
    :type invers: int
    :param outvers: output version
    :type outvers: int
    """    
    tacop = AIPSTask('tacop')
    tacop.inname = data.name
    tacop.inclass = data.klass 
    tacop.indisk = data.disk
    tacop.inseq = data.seq
    
    tacop.outname = data.name
    tacop.outclass = data.klass 
    tacop.outdisk = data.disk
    tacop.outseq = data.seq
    
    tacop.inext = ext
    tacop.invers = invers
    tacop.outvers = outvers
    
    tacop.go()