import numpy as np
import os
import math
import pandas as pd
import pkg_resources

from astropy.io import fits
from astropy.table import Table

from AIPS import AIPS
from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList


class MultiFile:
    def __init__(self, *file_paths, mode='r'):
        """
        Initialize the MultiFile object with multiple file paths.
        
        :param file_paths: The paths of the files to be opened.
        :param mode: The mode in which the files should be opened.
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
        
        :param data: The data to be written to the files.
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
        
        :param lines: The list of lines to write to the files.
        """
        for file in self.files:
            file.writelines(lines)

    def seek(self, offset, whence=0):
        """
        Moves the file pointer to a new position in all files.
        
        :param offset: The offset to move the pointer to.
        :param whence: The reference point (0: start, 1: current position, 2: end).
        """
        for file in self.files:
            file.seek(offset, whence)

    def tell(self):
        """
        Returns the current position of the file pointer from the first file.
        (Note: Assumes all files are at the same position.)
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


class Source():
    """Sources within a fits file."""
    def __init__(self):
        self.name = None
        self.id = None
        self.inlist = None
        self.restfreq = None
        self.band = None
        self.band_flux = None
        
    def set_band(self):
        """Set band name depending on rest frequency."""
        if self.restfreq < 3e9:
            self.band = 'S'
        elif self.restfreq < 7e9:
            self.band = 'C'
        elif self.restfreq < 1e10:
            self.band = 'X'
        elif self.restfreq < 1.8e10:
            self.band = 'U'
        elif self.restfreq < 2.6e10:
            self.band = 'K'
        else:
            self.band = 'Ka'


def set_name(path, source, klass):
    hdul = fits.open(path)
    obs = hdul[0].header['OBSERVER']
    if '/' in hdul[0].header['DATE-OBS']:
        date = hdul[0].header['DATE-OBS'].split('/')
        if int(date[2]) > 90:
            date_obs = '19' + date[2] + '-' + date[1] + '-' + date[0]
        else:
            date_obs = '20' + date[2] + '-' + date[1] + '-' + date[0]
    if '-' in hdul[0].header['DATE-OBS']:
        date_obs = hdul[0].header['DATE-OBS']
    freq = int(klass.strip('G'))
    if freq < 3:
        band = 'S'
    elif freq < 7:
        band = 'C'
    elif freq < 10:
        band = 'X'
    elif freq < 18:
        band = 'U'
    elif freq < 26:
        band = 'K'
    else:
        band = 'Ka'

    name = source + '_' + obs + '_' + band + '_' + date_obs
    return(name)



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

def copy_log(path_list, filename_list):
    """Copy AIPS log to all folders when multiple targets are selected

    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param filename_list: list of file names
    :type filename_list: list of str
    """ 
    log_name = path_list[0] + '/' + filename_list[0] + '_AIPS_log.txt'
    for i, name in enumerate(filename_list[1:]):
        os.system('cp ' + log_name\
                  + ' ' + path_list[i+1] + '/' + name + '_AIPS_log.txt')



def get_source_list(file_path_list, freq = 0):
    """Get a source list from a uvfits/idifits file.

    :param file_path_list: list of paths of the uvfits/idifts files
    :type file_path_list: list of str
    :param freq: if there are multiple frequency ids, which one to choose; defaults to 0
    :type freq: int, optional
    :return: list of sources contained in the file
    :rtype: list of Source objects
    """    
    full_source_list = []
    for file_path in file_path_list:
        hdul = fits.open(file_path)
        for elements in Table(hdul['SOURCE'].data):
            a = Source()
            a.name = elements['SOURCE']
            try:
                a.id = elements['ID_NO.']
            except KeyError:
                a.id = elements['SOURCE_ID']
            try:
                a.restfreq = elements['RESTFREQ'][0]
            except IndexError: # Single IF datasets
                a.restfreq = elements['RESTFREQ']      
                
            # Frequency can be given as an input
            if freq != 0:
                a.restfreq = freq
                
            a.set_band()      

            # Check if the source was already on the list (multiple files)
            if a.name not in [s.name for s in full_source_list]:
                full_source_list.append(a)
                
            a = None        
        
    # Make sure that source names are ASCII characters
    for s in full_source_list:
        name_string = s.name
        s.name = ''.join(char for char in name_string \
                         if ord(char) < 128).rstrip('\x00')
        
    return(full_source_list)

def redo_source_list(uvdata):
    """Create again the source list after loading the data.

    This is done to avoid problems with the source IDs after 
    concatenating multiple files.

    :param data: visibility data
    :type data: AIPSUVData
    :return: list of sources contained in the observations
    :rtype: list of Source objects
    """    
    su_table = uvdata.table('SU', 1)
    full_source_list = []
    for source in su_table:
        b = Source()
        b.name = source['source'].replace(" ", "")
        b.id = source['id__no']
        freq_indx = uvdata.header['ctype'].index('FREQ')
        b.restfreq = uvdata.header['crval'][freq_indx]
        #try:
        #    b.restfreq = source['restfreq'][0]
        #except (IndexError, TypeError): # Single IF datasets
        #    b.restfreq = source['restfreq']  

        b.set_band()

        full_source_list.append(b)
        b= None

    return full_source_list

def find_calibrators(full_source_list):
    """Choose possible calibrators from a source list.

    It loads information of ~ 9000 sources from an external file.
    Then, checks if there is available flux information for the
    sources in the source list generated by the get_source_list() 
    function. If there are more than 3 observed sources, the names 
    of the brightest 3 are given in return. If not, only the 
    brighthest source is returned.

    :param full_source_list: list of sources contained in the file
    :type full_source_list: list of Source objects
    :return: names of possible calibrators available in the file
    :rtype: list of str
    """    
    col_names = ['NameJ2000', 'NameB1950', 'NameICRF3', 'NameOther','RA',\
                 'DEC', 'RAE', 'DECE', 'S_short', 'S_long', 'C_short',\
                 'C_long', 'X_short', 'X_long', 'U_short', 'U_long',\
                 'K_short', 'K_long', 'Ka', 'Ref']

    catalogue_path = \
        pkg_resources.resource_filename(__name__,\
                                         '../catalogues/vlbaCalib_allfreq_full.txt')
    
    calib_list = pd.read_fwf(catalogue_path, skiprows = 16,\
                             names = col_names)

    
    for elements in full_source_list:
        row = calib_list.loc[calib_list.isin([elements.name]).any(axis=1)]
        try:
            elements.band_flux = float(row.iloc[0][elements.band + '_short'])
        except:
            elements.band_flux = np.NaN
        
    full_source_list.sort(key = lambda x: 0 if math.isnan(x.band_flux)\
                          else x.band_flux, reverse = True)
    
    # If none of the sources is on the calibrator list, load all
    if np.isnan(full_source_list[0].band_flux) == True:
        return(999)

    if len(full_source_list) > 3:
        return [str(full_source_list[0].name),str(full_source_list[1].name),\
                str(full_source_list[2].name)]
            
    # If there are 3 or less sources just load all 
    else:
        calibs = []
        for src in full_source_list:
            calibs.append(src.name)
        return(calibs)
    
def is_it_multifreq_id(file_path):
    """Check if the file contains multiple bands splitted in IDs.

    :param file_path: path of the uvfits/idifts file
    :type file_path: str
    :return: True if the dataset has multiple bands, False if not; number of ids; \
             frequency of each id
    :rtype: tuple with (boolean, int, list of float)
    """    
    multifreq = False
    hdul = fits.open(file_path)
    howmanyids = len(hdul['FREQUENCY'].data['FREQID'])
    bands = []
    if howmanyids > 1:
        for i in range(howmanyids):
            freq = np.floor(hdul['SOURCE'].data['RESTFREQ'][0] \
                            + hdul['FREQUENCY'].data['BANDFREQ'][i])
            if freq[0] > 1e10:
                bands.append(freq[0])
            else:
                bands.append(freq[0])
        multifreq = True
    return (multifreq, howmanyids, bands)

def is_it_multifreq_if(file_path):
    """Check if the file contains multiple bands splitted in IFs.
    
    Looks at the central frequency of all IFs and looks for jumps of
    more than 1 GHz between them. Only works for datasets with 1 or 2
    frequency bands, not more.

    :param file_path: path of the uvfits/idifts file
    :type file_path: str
    :return: True if the dataset has multiple bands, False if not; Value of the first \
             IF, always 1; value of the last IF of band 1; value of the first IF of \
             band 2; value of the last IF of band 2; first digit of the frequency of \
             band 1; first digit of the frequency of band 2; frequency of band 1 ;\
             frequency of band 2
    :rtype: tuple with (boolean, int, int, int, int, str, str, float, float)
    """    
    multifreq = False
    hdul = fits.open(file_path)
    if_freq = hdul['SOURCE'].data['RESTFREQ'][0] \
              + hdul['FREQUENCY'].data['BANDFREQ']
    if isinstance(if_freq[0], np.float64) == True:
        # Data is single IF
        if if_freq[0] > 1e10:
            freq = str(if_freq[0])[:2] 
        else:
            freq = str(if_freq[0])[:1] 
        return(False, 1, 1, 1, 1, freq, freq)
               
    for IF,freq in enumerate(if_freq[0]):
        if IF == 0:
            continue
        if abs(freq - if_freq[0][IF-1]) > 1e9 :
            multifreq = True
            break
    freq_1 = np.floor(if_freq[0][0])
    freq_2 = np.floor(if_freq[0][-1])

    if freq_1 > 1e10:
        klass_1 = str(freq_1)[:2]
    else:
        klass_1 = str(freq_1)[0]
    if freq_2 > 1e10:
        klass_2 = str(freq_2)[:2]
    else:
        klass_2 = str(freq_2)[0]

    return(multifreq, 1, IF, IF+1, len(if_freq[0]), klass_1,\
           klass_2, freq_1, freq_2)
        

def load_data(file_path_list, name, sources, disk, multi_id, selfreq, klass = '', \
              seq = 1, bif = 0, eif = 0, l_a = False, symlink_path = '.'):
    """Load data from a uvfits/idifits file.

    :param file_path_list: list of paths of the uvfits/idifts files
    :type file_path_list: list of str
    :param name: file name whithin AIPS
    :type name: str
    :param sources: list of sources to load
    :type sources: list of str
    :param disk: disk number whithin AIPS
    :type disk: int
    :param multi_id: True if there are multiple frequency ids, False otherwise
    :type multi_id: bool
    :param selfreq: if there are multiple frequency ids, which one to load
    :type selfreq: int
    :param klass: class name whithin AIPS; defaults to ''
    :type klass: str, optional
    :param seq: sequence number within AIPS; defaults to 1
    :type seq: int, optional
    :param bif: first IF to copy, 0 => 1; defaults to 0
    :type bif: int, optional
    :param eif: highest IF to copy,  0 => all higher than bif; defaults to 0
    :type eif: int, optional
    :param l_a: load all sources; default False
    :type l_a: bool, optional
    :param symlink_path: path where to create the symbolic links needed to load the data
    :type symlink_path: str
    """      
    fitld = AIPSTask('fitld')
    # Create symbolic links for each of the files
    # This is necessary when multiple files need to be concatenated
    # Delete if it already exists
    if os.path.exists(symlink_path + '/aux_1'):
        os.system('rm ' + symlink_path + '/aux_*')
    for n, filepath in enumerate(file_path_list):
        os.system('ln -s ' + filepath + ' ' + symlink_path + '/aux_' + str(n+1))
    

    fitld.ncount = int(len(file_path_list))  
    if len(file_path_list) > 1:
        fitld.doconcat = 1 
    fitld.outname = name
    fitld.outdisk = disk
    fitld.outclass = klass
    fitld.outseq = seq

    # If the data already exists in AIPS, delete it
    uvdata = AIPSUVData(name, klass, disk, seq)
    if uvdata.exists() == True:
        uvdata.zap()
    
    if l_a == False:
        fitld.sources = AIPSList(sources)
    fitld.bif = bif
    fitld.eif = eif
    fitld.clint = 0.1
    fitld.msgkill = -4
    if multi_id == True:
        fitld.selfreq = float(selfreq)  

    fitld.datain = symlink_path + '/aux_'

    fitld.go()
    # Remove the symbolic links
    os.system('rm ' + symlink_path + '/aux_*')


def write_info(data, filepath_list, log_list, sources):
    """Write some basic information about the loaded file to the logs

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath_list: list of paths to the original uvfits/idifits files
    :type filepath_list: list of str
    :param log_list: list of the pipeline logs
    :type log_list: list of file
    :param sources: list of sources loaded
    :type sources: list of str
    """    
    for log in log_list:
        for path in filepath_list:
            log.write('\nLoaded file: ' + os.path.basename(path) + '\n')
            size = os.path.getsize(path)
            if size >= 1024**3:
                log.write('Size: ' + '{:.2f} GB \n'.format(os.path.getsize(path)/1024**3))
            if size < 1024**3:
                log.write('Size: ' + '{:.2f} MB \n'.format(os.path.getsize(path)/1024**2))

        log.write('\nProject: ' + data.header['observer'])
        log.write('\nObservation date: ' + data.header['date_obs'])

        freq_indx = data.header['ctype'].index('FREQ')
        freq = data.header['crval'][freq_indx]
        if freq >= 1e9:
            log.write('\nFrequency: ' + str(np.round(freq/1e9,2)) + ' GHz')
        if freq < 1e9:
            log.write('\nFrequency: ' + str(np.round(freq/1e6,2)) + ' MHz')

        log.write('\nLoaded sources: ' + str(list(set(sources))) + '\n')


def print_info(data, filepath_list, sources):
    """Print some basic information about the loaded file to the logs

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath_list: list of paths to the original uvfits/idifits files
    :type filepath_list: list of str
    :param sources: list of sources loaded
    :type sources: list of str
    """    
    for path in filepath_list:
        print('\nLoaded file: ' + os.path.basename(path) + '\n')
        size = os.path.getsize(path)
        if size >= 1024**3:
            print('Size: ' + '{:.2f} GB \n'.format(os.path.getsize(path)/1024**3))
        if size < 1024**3:
            print('Size: ' + '{:.2f} MB \n'.format(os.path.getsize(path)/1024**2))

    print('\nProject: ' + data.header['observer'])
    print('\nObservation date: ' + data.header['date_obs'])

    freq_indx = data.header['ctype'].index('FREQ')
    freq = data.header['crval'][freq_indx]
    if freq >= 1e9:
        print('\nFrequency: ' + str(np.round(freq/1e9,2)) + ' GHz')
    if freq < 1e9:
        print('\nFrequency: ' + str(np.round(freq/1e6,2)) + ' MHz')

    print('\nLoaded sources: ' + str(list(set(sources))) + '\n')


def print_listr(data, path_list, filename_list):
    """Print scan information in an external file.

    Runs the FITLD task and prints the output in scansum.txt

    :param data: visibility data
    :type data: AIPSUVData
    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param filename_list: list of folder names for the different science targets
    :type filename_list: list of str
    """    
    listr = AIPSTask('listr')
    listr.inname = data.name
    listr.inclass = data.klass
    listr.indisk = data.disk
    listr.inseq = data.seq
    
    listr.optype = 'SCAN'
    listr.xinc = 1
    listr.docrt = -2
    for i, name in enumerate(filename_list):
        listr.outprint = path_list[i] + '/' + name + '_scansum.txt'
        listr.msgkill = -4
        
        listr.go()