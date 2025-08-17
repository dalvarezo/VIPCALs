import os
import numpy as np

from datetime import datetime

from AIPSTask import AIPSTask

AIPSTask.msgkill = -8

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

# Check if /home/vipcals exists
if os.path.isdir("/home/vipcals"):
    tmp_dir = "/home/vipcals/.vipcals/tmp"

def ionos_correct(data):
    """Ionospheric delay calibration.

    Calls :func:`~vipcals.scripts.ionos_corr.new_tecor` or \
    :func:`~vipcals.scripts.ionos_corr.old_tecor` depending on the observation date \
    of the dataset. Information on the different formats can be found `here <TE>`_.

    .. _TE: https://cddis.nasa.gov/Data_and_Derived_Products/GNSS/atmospheric_products.html
    
    :param data: visibility data
    :type data: AIPSUVData
    :return: list of retrieved files
    :rtype: list of str
    """
    # GPS Week 2238  -> 26/11/2022
    
    date_lim = datetime(2022,11,26)
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    if date_obs > date_lim:
        files = new_tecor(data)
    else:
        files = old_tecor(data)

    return(files)

def old_tecor(data):
    """Ionospheric delay calibration using TECOR.

    Derives corrections for ionospheric Faraday rotation and \
    dispersive delay from maps of total electron content in IONEX \
    format. 

    Reads the date from the header and the different observed days \
    from each scan, then downloads the corresponding file(s) using the old format \
    (older than 26/11/2022) and applies the TECOR task in AIPS. The downloaded files 
    are of the CODG type (Center for Orbit Determination in Europe).

    Creates CL#2

    :param data: visibility data
    :type data: AIPSUVData
    :return: list of retrieved files
    :rtype: list of str
    """
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    DDD = date_obs.timetuple().tm_yday

    cl1_table = data.table('CL',1)

    days = [*range(int(np.floor(cl1_table[-1]['time']))+1)]

    # If the file is older than 04/11/2002, download also the day after and 
    # the day before. Explanation of this in the EXPLAIN file of the TECOR task in AIPS.
    if date_obs < datetime(2002,11,4):
        days = [(min(days)-1)] + days + [(max(days)+1)]

    files = []

    for elements in days:
        YY = data.header.date_obs[2:4]
        if DDD + elements <= 365:
            new_DDD = str(DDD + elements)
            if len(new_DDD) == 2:
                new_DDD = '0' + new_DDD
            if len(new_DDD) == 1:
                new_DDD = '00' + new_DDD
            new_YYYY = YYYY
            new_YY = YY

        if DDD + elements > 365:
            new_DDD = str(DDD + elements - 365)
            if len(new_DDD) == 2:
                new_DDD = '0' + new_DDD
            if len(new_DDD) == 1:
                new_DDD = '00' + new_DDD
            new_YYYY = YYYY + 1
            new_YY = str(new_YYYY)[2:4]
        
        if os.path.exists(tmp + '/codg' + new_DDD +'0.'+ new_YY +'i') == False:
            curl_command = (
    f"curl -sf --retry 5 --retry-delay 10 -u 'anonymous:daip@nrao.edu' --ftp-ssl "
    f"ftp://gdc.cddis.eosdis.nasa.gov/gps/products/ionex/{str(new_YYYY)}/{new_DDD}/"
    f"codg{new_DDD}0.{new_YY}i.Z > {tmp}/codg{new_DDD}0.{new_YY}i.Z")

            os.system(curl_command)

            files.append(curl_command.split(' ')[9])
            
            zcat_command = f"""zcat {tmp}/codg{new_DDD}0.{new_YY}i.Z >> {tmp}/codg{new_DDD}0.{new_YY}i"""
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
    tecor.infile = f'{tmp}/codg{infile}0.{YY}i'
    tecor.nfiles = len(days)
    tecor.aparm[1] = 1   # Correct for dispersive delays
    tecor.gainver = 1
    tecor.gainuse = 2

    tecor.go()

    return(files)

def new_tecor(data):
    """Ionospheric delay calibration using TECOR.

    Derives corrections for ionospheric Faraday rotation and \
    dispersive delay from maps of total electron content in IONEX \
    format. 

    Reads the date from the header and the different observed days \
    from each scan, then downloads the corresponding file(s) using the new format \
    (recent than 26/11/2023) and applies the TECOR task in AIPS. The downloaded files 
    are of the CODG type (Center for Orbit Determination in Europe).

    Creates CL#2

    :param data: visibility data
    :type data: AIPSUVData
    :return: list of retrieved files
    :rtype: list of str
    """
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])

    date_obs = datetime(YYYY, MM, DD)
    DDD = date_obs.timetuple().tm_yday

    cl1_table = data.table('CL',1)

    days = [*range(int(np.floor(cl1_table[-1]['time']))+1)]

    files = []

    for elements in days:
        YY = data.header.date_obs[2:4]
        if DDD + elements <= 365:
            new_DDD = str(DDD + elements)
            if len(new_DDD) == 2:
                new_DDD = '0' + new_DDD
            if len(new_DDD) == 1:
                new_DDD = '00' + new_DDD
            new_YYYY = YYYY
            new_YY = YY

        if DDD + elements > 365:
            new_DDD = str(DDD + elements - 365)
            if len(new_DDD) == 2:
                new_DDD = '0' + new_DDD
            if len(new_DDD) == 1:
                new_DDD = '00' + new_DDD
            new_YYYY = YYYY + 1
            new_YY = str(new_YYYY)[2:4]
        
        if os.path.exists(tmp + '/codg' + new_DDD +'0.'+ new_YY +'i') == False:
            curl_command = (
    f"curl -sf --retry 5 --retry-delay 10 -u 'anonymous:daip@nrao.edu' --ftp-ssl "
    f"ftp://gdc.cddis.eosdis.nasa.gov/gps/products/ionex/{new_YYYY}/{new_DDD}/"
    f"COD0OPSFIN_{new_YYYY}{new_DDD}0000_01D_01H_GIM.INX.gz "
    f"> {tmp}/codg{new_DDD}0.{new_YY}i.gz")

            os.system(curl_command)

            files.append(curl_command.split(' ')[9])
            
            zcat_command = f'zcat {tmp}/codg{new_DDD}0.{new_YY}i.gz >> {tmp}/codg{new_DDD}0.{new_YY}i'
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
    tecor.infile = f'{tmp}/codg{infile}0.{YY}i'
    tecor.nfiles = len(days)
    tecor.aparm[1] = 1   # Correct for dispersive delays
    tecor.gainver = 1
    tecor.gainuse = 2

    tecor.go()

    return(files)