import numpy as np

from AIPSTask import AIPSTask

import Wizardry.AIPSData as wizard

from vipcals.scripts.helper import NoAutocorrError

AIPSTask.msgkill = -8

def autocorr_correct(data, solint = -3):
    """Auto corelation scaling correction - ACSCL
    
    Corrects errors in the scaling of auto correlations due to the bandpass 
    using the ACSCL task in AIPS.    
    Creates SN#4 and CL#7.

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval in minutes. If > 0, does not pay 
        attention to scan boundaries; defaults to -3
    :type solint: float, optional
    """    
    acscl = AIPSTask('acscl')
    acscl.inname = data.name
    acscl.inclass = data.klass
    acscl.indisk = data.disk
    acscl.inseq = data.seq
    acscl.solint = solint 

    acscl.docalib = 1
    acscl.gainuse = 0
    acscl.doband = 1 

    acscl.go()

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = 4
    clcal.gainver = 6
    clcal.gainuse = 7

    clcal.go()

def sampling_correct(data, solint = -3):
    """Digital sampling correction - ACCOR
    
    Correct cross correlations using auto correlations using the ACCOR
    task in AIPS.
    Creates SN#2 and CL#5.

    :param data: visibility data
    :type data: AIPSUVData
    :param solint: solution interval in minutes. If > 0, does not pay 
        attention to scan boundaries; defaults to -3
    :type solint: float, optional
    """    
    accor = AIPSTask('accor')
    accor.inname = data.name
    accor.inclass = data.klass
    accor.indisk = data.disk
    accor.inseq = data.seq
    accor.solint = solint 

    try:
        accor.go()
    except RuntimeError:
        wuvdata = wizard.AIPSUVData(data.name, data.klass, data.disk, data.seq)
        baselines = np.array([w.baseline for w in wuvdata])
        mask = baselines[:, 0] == baselines[:, 1]
        if mask.sum() == 0:
            raise NoAutocorrError("The dataset does not contain auto-correlation data.") from None
        else:
            raise

    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = 2
    clcal.gainver = 4
    clcal.gainuse = 5

    clcal.go()