import numpy as np
import os

from datetime import datetime
from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

#from AIPSData import AIPSUVData, AIPSImage
#import Wizardry.AIPSData as wizard

def tacop(data, ext, invers, outvers):
    """
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
    tacop.msgkill = -4
    
    tacop.go()


def old_tecor(data):
    """Ionospheric delay calibration.
    
    Derives corrections for ionospheric Faraday rotation and 
    dispersive delay from maps of total electron content in IONEX 
    format.
    Reads the date from the header and the different observed days 
    from each scan, then downloads the corresponding file(s).
    Applies the TECOR task and creates CL#2
    """
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    DDD = date_obs.timetuple().tm_yday

    nx_table = data.table('NX',1)

    scan_times = []

    for scans in nx_table:
        scan_times.append(int(np.floor(scans['time'])))
    days = [*range(max(scan_times)+1)]

    for elements in days:
        YY = data.header.date_obs[2:4]
        new_DDD = str(DDD + elements)
        if len(new_DDD) == 2:
            new_DDD = '0' + new_DDD
        if len(new_DDD) == 1:
            new_DDD = '00' + new_DDD
        
        if os.path.exists('/tmp/jplg' + new_DDD +'0.'+ YY +'i') == False:
            curl_command = 'curl -u anonymous:daip@nrao.edu --ftp-ssl' \
                            + ' ftp://gdc.cddis.eosdis.nasa.gov/gps' \
                            + '/products/ionex/'+ str(YYYY) + '/' \
                            + new_DDD + '/' + 'jplg'+ new_DDD +'0.'+ YY \
                            + 'i.Z > /tmp/' + 'jplg' + new_DDD +'0.' \
                            + YY +'i.Z'
            os.system(curl_command)
            
            zcat_command = 'zcat /tmp/jplg'+ new_DDD +'0.'+ YY \
                            + 'i.Z >> /tmp/jplg'+ new_DDD +'0.'+ YY +'i'
            os.system(zcat_command)
    
    infile = str(DDD + days[0])
    if len(infile) == 2:
        infile = '0' + infile
    if len(infile) == 1:
        infile = '00' + infile
    
    tecor = AIPSTask('tecor')
    tecor.inname = data.name
    tecor.inclass = data.klass 
    tecor.indisk = data.disk
    tecor.inseq = data.seq
    tecor.infile = '/tmp/jplg' + infile + '0.' + YY + 'i'
    tecor.nfiles = len(days)
    tecor.aparm[1] = 1   # Correct for dispersive delays
    tecor.gainver = 1
    tecor.gainuse = 2
    tecor.msgkill = -4

    tecor.go()

def new_tecor(data):
    """Ionospheric delay calibration.
    
    Derives corrections for ionospheric Faraday rotation and 
    dispersive delay from maps of total electron content in IONEX 
    format.
    Reads the date from the header and the different observed days 
    from each scan, then downloads the corresponding file(s).
    Applies the TECOR task and creates CL#2
    """
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    DDD = date_obs.timetuple().tm_yday

    nx_table = data.table('NX',1)

    scan_times = []

    for scans in nx_table:
        scan_times.append(int(np.floor(scans['time'])))
    days = [*range(max(scan_times)+1)]

    for elements in days:
        YY = data.header.date_obs[2:4]
        new_DDD = str(DDD + elements)
        if len(new_DDD) == 2:
            new_DDD = '0' + new_DDD
             
        if len(new_DDD) == 1:
            new_DDD = '00' + new_DDD
        
        if os.path.exists('/tmp/jplg' + new_DDD +'0.'+ YY +'i') == False:
            curl_command = 'curl -u anonymous:daip@nrao.edu --ftp-ssl' \
                            + ' ftp://gdc.cddis.eosdis.nasa.gov/gps' \
                            + '/products/ionex/'+ str(YYYY) + '/' \
                            + new_DDD + '/' + 'JPL0OPSFIN_' + str(YYYY)\
                            + new_DDD + '0000_01D_02H_GIM.INX.gz '\
                            + '> /tmp/' + 'jplg' + new_DDD +'0.' \
                            + YY +'i.gz'
            os.system(curl_command)
            
            zcat_command = 'zcat /tmp/jplg'+ new_DDD +'0.'+ YY \
                            + 'i.gz >> /tmp/jplg'+ new_DDD +'0.'+ YY +'i'
            os.system(zcat_command)
    
    infile = str(DDD + days[0])
    if len(infile) == 2:
        infile = '0' + infile
    if len(new_DDD) == 1:
        infile = '00' + infile
    
    tecor = AIPSTask('tecor')
    tecor.inname = data.name
    tecor.inclass = data.klass 
    tecor.indisk = data.disk
    tecor.inseq = data.seq
    tecor.infile = '/tmp/jplg' + infile + '0.' + YY + 'i'
    tecor.nfiles = len(days)
    tecor.aparm[1] = 1   # Correct for dispersive delays
    tecor.gainver = 1
    tecor.gainuse = 2
    tecor.msgkill = -4

    tecor.go()
def ionos_correct(data):
    """Ionospheric delay calibration.
    
    Derives corrections for ionospheric Faraday rotation and 
    dispersive delay from maps of total electron content in IONEX 
    format.
    Reads the date from the header and the different observed days 
    from each scan, then downloads the corresponding file(s).
    Applies the TECOR task and creates CL#2
    """
    date_lim = datetime(2023,8,6)
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    if date_obs > date_lim:
        new_tecor(data)
    else:
        old_tecor(data)