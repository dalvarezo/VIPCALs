from AIPS import AIPS
from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList

import time
import sys
import numpy as np

from astropy.io import fits
from astropy.table import Table
from astropy.coordinates import SkyCoord
from astropy.coordinates import search_around_sky
from astropy import units as u

if __name__ == "__main__":

    #################
    #               #
    #    INPUTS     #
    #               #
    #################

    AIPS.userno = 4

    # Name, class, seq and disk of the entry in AIPS
    aips_name = 'TEST'
    klass = 'UVDATA'
    disk_number = 1
    seq = 1
    
    ##############################################################################
    ##############################################################################

    #################
    #               #
    #   WORKFLOW    #
    #               #
    #################
    
    with open('../GUI/ascii_logo_string.txt', 'r') as f:
        ascii_logo = f.read()
        print(ascii_logo + '\n', flush=True)
    uvdata = AIPSUVData(aips_name, klass, disk_number, seq)
    for i in range(2):
        time.sleep(3)
        print(f"\nIteration number: {i+1}:\n", flush=True)
        print(uvdata.tables, flush=True)
    print('\n\n\nTHE END.', flush = True)
