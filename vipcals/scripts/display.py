import os
import functools
print = functools.partial(print, flush=True)

import numpy as np
import pandas as pd

def print_box(s):
    """Print some text inside a box in the terminal 

    :param s: text to display in the box
    :type s: str
    """    
    box_width = 90

    # Split the input string into lines to fit within the box width
    lines = [s[i:i+box_width-8] for i in range(0, len(s), box_width-8)]

    # Create the box
    box = '//' + '/' * (box_width - 6) + '//'

    # Print the box with the lines centered inside
    print(box)
    for line in lines:
        print(f'// {line.center(box_width - 8)} //')
    print(box + '\n')
    
def write_box(log_list, s):
    """Write some text inside a box in the log file

    :param log_list: list of the pipeline logs
    :type log_list: list of file
    :param s: text to display in the box
    :type s: str
    """    
    box_width = 100

    # Split the input string into lines to fit within the box width
    lines = [s[i:i+box_width-8] for i in range(0, len(s), box_width-8)]

    # Create the box
    box = '//' + '/' * (box_width - 6) + '//\n'

    # Print the box with the lines centered inside
    for log in log_list:
        log.write('\n' + box)
        for line in lines:
            log.write(f'// {line.center(box_width - 8)} //\n')
        log.write(box)

def write_info(data, filepath_list, log_list, sources, stats_df = 'None'):
    """Write some basic information about the loaded file to the logs

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath_list: list of paths to the original uvfits/idifits files
    :type filepath_list: list of str
    :param log_list: list of the pipeline logs
    :type log_list: list of file
    :param sources: list of sources loaded
    :type sources: list of str
    :param stats_df: if given, Pandas DataFrame where to keep track of the different statistics
    :type stats_df: pandas.DataFrame object, optional
    """    
    for log in log_list:
        total_size = 0
        for path in filepath_list:
            log.write('\nLoaded file: ' + os.path.basename(path) + '\n')
            size = os.path.getsize(path)
            total_size += size
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

        if type(stats_df) == pd.core.frame.DataFrame:
            stats_df['files'] = str([x.split('/')[-1] for x in filepath_list])
            stats_df['total_size'] = total_size
            stats_df['project'] = data.header['observer']
            stats_df['obs_date'] = data.header['date_obs']
            stats_df['frequency'] = np.round(freq/1e9,6)


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