import numpy as np

from astropy.coordinates import SkyCoord

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def uv_shift(data, target, new_coord):
    """Shift the phase center of a dataset.

    The produced dataset has the same AISP name and class, but the sequence number 
    increases by one for every shifted source. If the new coordinates are 0h0m0s +0d0m0s,
    then no shift is produced.

    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :param new_coord: Astropy SkyCoord object with new coordinates for the phase center
    :type new_coord: SkyCoord
    """    
    if new_coord == SkyCoord(0, 0, unit = 'deg'):
        return()

    su_table = data.table('SU', 1)
    
    for entry in su_table:
        if target == entry['source'].replace(' ',''):
            old_coord = SkyCoord(entry['raepo'], entry['decepo'], unit = 'deg')

    shift_1 = np.cos(old_coord.dec.arcsec) \
                * (new_coord.ra.arcsec - old_coord.ra.arcsec)
    shift_2 = new_coord.dec.arcsec - old_coord.dec.arcsec

    uvfix = AIPSTask('uvfix')
    uvfix.inname = data.name
    uvfix.inclass = data.klass
    uvfix.indisk = data.disk
    uvfix.inseq = data.seq

    uvfix.outname = data.name
    uvfix.outclass = data.klass
    uvfix.outdisk = data.disk
    uvfix.outseq = data.seq + 1
    
    uvfix.srcname = target
    uvfix.shift = AIPSList([float(shift_1), float(shift_2)])

    uvfix.msgkill = -4
    uvfix.go()