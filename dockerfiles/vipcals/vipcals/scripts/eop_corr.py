import os

from AIPSTask import AIPSTask

AIPSTask.msgkill = -8

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

def eop_correct(data):
    """Earth orientation parameters correction.
    
    Correction of UT1-UTC and Earth's pole position. Downloads a file and 
    applies the CLCOR task in AIPS.
    Create CL#3

    :param data: visibility data
    :type data: AIPSUVData
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    if os.path.exists('../../tmp/usno_finals_bis.erp') == False:
        curl_command = 'curl -su anonymous:daip@nrao.edu --ftp-ssl ' \
        + 'ftp://gdc.cddis.eosdis.nasa.gov/vlbi/gsfc/ancillary/' \
        + 'solve_apriori/usno_finals.erp > ' + tmp + '/usno_finals_bis.erp'
        os.system(curl_command)
    
    clcor = AIPSTask('clcor')
    clcor.inname = data.name
    clcor.inclass = data.klass
    clcor.indisk = data.disk
    clcor.inseq = data.seq
    clcor.opcode = 'EOPS'
    clcor.infile = f'{tmp}/usno_finals_bis.erp'
    clcor.gainver = 2
    clcor.gainuse = 3

    clcor.go()