from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os

def print_box(s):
    """Print some text inside a box in the terminal 

    :param s: text to display in the box
    :type s: str
    """    
    box_width = 80

    # Split the input string into lines to fit within the box width
    lines = [s[i:i+box_width-8] for i in range(0, len(s), box_width-8)]

    # Create the box
    box = '//' + '/' * (box_width - 6) + '//'

    # Print the box with the lines centered inside
    print(box)
    for line in lines:
        print(f'// {line.center(box_width - 8)} //')
    print(box + '\n')
    
def write_box(log, s):
    """Write some text inside a box in the log file

    :param log: pipeline log
    :type log: file
    :param s: text to display in the box
    :type s: str
    """    
    box_width = 100

    # Split the input string into lines to fit within the box width
    lines = [s[i:i+box_width-8] for i in range(0, len(s), box_width-8)]

    # Create the box
    box = '//' + '/' * (box_width - 6) + '//\n'

    # Print the box with the lines centered inside
    log.write('\n' + box)
    for line in lines:
        log.write(f'// {line.center(box_width - 8)} //\n')
    log.write(box)