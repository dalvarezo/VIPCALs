import numpy as np

from astropy.coordinates import SkyCoord

from AIPSTask import AIPSTask, AIPSList

AIPSTask.msgkill = -8

def get_coord(data, target): 
    """Get coordinate of the phase center for a given target.

    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :return: coordinates
    :rtype: SkyCoord object
    """    
    su_table = data.table('SU', 1)
    
    for entry in su_table:
        if target == entry['source'].replace(' ',''):
            coord = SkyCoord(entry['raepo'], entry['decepo'], unit = 'deg')
            break

    return(coord)

def uv_shift(data, target, new_coord):
    """Shift the phase center of a dataset.

    Creates a new AIPS entry by shifting the correlation phase center of a previous 
    entry using the UVFIX task in AIPS. The new entry has the same AIPS name and class, 
    but the sequence number increases by one for every shifted source. If the new 
    coordinates are 0h0m0s +0d0m0s, then no shift is produced.

    :param data: visibility data
    :type data: AIPSUVData
    :param target: source name
    :type target: str
    :param new_coord: Astropy SkyCoord object with new coordinates for the phase center
    :type new_coord: SkyCoord
    :return: old coordinates, new coordinates
    :rtype: SkyCoord objects
    """    
    su_table = data.table('SU', 1)
    
    for entry in su_table:
        if target == entry['source'].replace(' ',''):
            old_coord = SkyCoord(entry['raepo'], entry['decepo'], unit = 'deg')

    if new_coord == None:
        return(old_coord, old_coord)

    shift_1 = np.cos(old_coord.dec.rad) * (new_coord.ra.arcsec - old_coord.ra.arcsec)
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

    uvfix.go()

    return(old_coord, new_coord)