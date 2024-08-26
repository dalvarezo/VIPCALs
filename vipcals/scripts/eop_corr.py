import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def eop_correct(data):
    """Earth orientation parameters correction.
    
    Correction of UT1-UTC and Earth's pole position.
    Downloads a file and applies CLCOR
     
    Create CL#3

    :param data: visibility data
    :type data: AIPSUVData
    """    
    if os.path.exists('/tmp/usno_finals_bis.erp') == False:
        curl_command = 'curl -u anonymous:daip@nrao.edu --ftp-ssl ' \
        + 'ftp://gdc.cddis.eosdis.nasa.gov/vlbi/gsfc/ancillary/' \
        + 'solve_apriori/usno_finals.erp > /tmp/usno_finals_bis.erp'
        os.system(curl_command)
    
    clcor = AIPSTask('clcor')
    clcor.inname = data.name
    clcor.inclass = data.klass
    clcor.indisk = data.disk
    clcor.inseq = data.seq
    clcor.opcode = 'EOPS'
    clcor.infile = '/tmp/usno_finals_bis.erp'
    clcor.gainver = 2
    clcor.gainuse = 3
    clcor.msgkill = -4

    clcor.go()