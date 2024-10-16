from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

import numpy as np
import os


def ddhhmmss(time):
    """Convert decimal dates into AIPS dd hh mm ss format.

    :param time: decimal date
    :type time: float
    :return: 1D array with day, hour, minute and second
    :rtype: ndarray
    """
    total_seconds = int(time * 24 * 60 * 60)
    days, remainder = divmod(total_seconds, 24 * 60 * 60)
    hours, remainder = divmod(remainder, 60 * 60)
    minutes, seconds = divmod(remainder, 60)
    return np.array([days,hours,minutes,seconds])


def calib_fring_fit(data, refant, calib_scans, solint = 0, \
                    delay_w = 0, rate_w = 0):
    """Fringe fit the calibrator

    Creates SN#5

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param calib_scans: list of scans of bright calibrators
    :type calib_scans: list of Scan object
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    :param delay_w: delay window in ns in which the search is performed, defaults to 0 \
                    (full Nyquist range)
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed, defaults to 0 \
                   (full Nyquist range)
    :type rate_w: int, optional 
    """    
    calib_names = [x.name for x in calib_scans]
    # This is not neccesary! I could pass only the name!
    
    calib_fring = AIPSTask('fring')
    calib_fring.inname = data.name
    calib_fring.inclass = data.klass
    calib_fring.indisk = data.disk
    calib_fring.inseq = data.seq
    calib_fring.refant = refant
    calib_fring.calsour = AIPSList(calib_names)
    
    calib_fring.docalib = 1
    calib_fring.gainuse = 0
    calib_fring.doband = -1

    calib_fring.solint = solint

    calib_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    calib_fring.aparm[1] = 2    # At least 2 antennas per solution
    calib_fring.aparm[5] = 0    # Solve IFs separatedly
    calib_fring.aparm[6] = 2    # Amount of information printed
    calib_fring.aparm[7] = 5    # SNR cutoff   
    calib_fring.aparm[9] = 1    # Exhaustive search
    calib_fring.aparm[10] = 1   # Solve for dispersive delay uncorrected by TECOR
    
    calib_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    calib_fring.dparm[1] = 1    # Number of baseline combinations searched
    calib_fring.dparm[2] = delay_w  # Delay window (ns)
    calib_fring.dparm[3] = rate_w  # Rate window (mHz)
    
    calib_fring.snver = 5
    calib_fring.msgkill = -4
    
    calib_fring.go()
    
    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.sources = AIPSList(calib_names)
    
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = 5
    clcal.gainver = 7
    clcal.gainuse = 8
    clcal.msgkill = -4
    
    clcal.go()
    
def target_fring_fit(data, refant, target_name, solint = 0, version = 9, delay_w = 1000,\
                     rate_w = 200):
    """Fringe fit the science target

    Creates SN#6
    
    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param target_name: target name
    :type target_name: str
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan; defaults to 0
    :type solint: int, optional
    :param version: CL table version in which to apply the solutions. SN version will \
                    be ('version' - 3); defaults to 9
    :type version: int, optional
    :param delay_w: delay window in ns in which the search is performed; defaults to 1000\
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed; defaults to 200 \
    :type rate_w: int, optional 
    """    
    target_fring = AIPSTask('fring')
    target_fring.inname = data.name
    target_fring.inclass = data.klass
    target_fring.indisk = data.disk
    target_fring.inseq = data.seq
    target_fring.refant = refant
    target_fring.calsour = AIPSList([target_name])
    
    target_fring.docalib = 1
    target_fring.gainuse = 0
    target_fring.doband = 1

    target_fring.solint = solint

    target_fring.aparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    target_fring.aparm[1] = 2    # At least 2 antennas per solution
    target_fring.aparm[5] = 0    # Solve IFs separately
    target_fring.aparm[6] = 2    # Amount of information printed
    target_fring.aparm[7] = 5    # SNR cutoff   
    target_fring.aparm[9] = 1    # Exhaustive search
    target_fring.aparm[10] = 1   # Solve for dispersive delay uncorrected by TECOR
    
    target_fring.dparm[1:] = [0,0,0,0,0,0,0,0,0]    # Reset parameters
    target_fring.dparm[1] = 1    # Number of baseline combinations searched
    target_fring.dparm[2] = delay_w  # Delay window (ns)
    target_fring.dparm[3] = rate_w  # Rate window (mHz)
    
    target_fring.snver = version-3
    target_fring.msgkill = -4
    
    target_fring.go()
    
    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.sources = AIPSList([target_name])
    
    clcal.opcode = 'calp'
    clcal.interpol = 'self'
    clcal.snver = version-3
    clcal.gainver = 8
    clcal.gainuse = version
    clcal.msgkill = -4
    
    clcal.go()

    return(target_fring.refant, str(target_fring.dparm[2]), str(target_fring.dparm[3]))
    
def assess_fringe_fit(data, log, version = 6):
    """Print the number of failed solutions after fringe fit

    Explore a solution table produced by FRING and print how many solutions failed. This \
    is done by looking at the weights of each entry in the SN table.

    :param data: visibility data
    :type data: AIPSUVData
    :param log: pipeline log
    :type log: file
    :param version: SN version to evaluate, defaults to 6
    :type version: int, optional
    """    
    an_table = data.table('AN', 1)
    sn_table = data.table('SN', version)
    
    antenna_dict = {}
    for ant in an_table:
        antenna_dict[ant['nosta']] = ant['anname'].strip()
        
    antennas = []
    for s in sn_table:
        antennas.append(s['antenna_no'])
    antennas = list(set(antennas))
    
    fring_dict = {}
    for a in antennas:
        fring_dict[a] = []
            
    # Single polarization:
    try:
        dummy = sn_table[0]['weight_2']
    except KeyError:      
    
        for s in sn_table:
            if type(s['weight_1']) == float: # single IF
                fring_dict[s['antenna_no']].append(s['weight_1'])
            else:
                for i in range(len(s['weight_1'])):
                    fring_dict[s['antenna_no']].append(s['weight_1'][i])
    
        total_length = sum((len(v) for v in fring_dict.values()))
        global_counter = 0
        for a in fring_dict:
            counter = 0
            for val in fring_dict[a]:
                if val == 0:
                    counter += 1
                    global_counter += 1
            print('    ' + antenna_dict[a] + ' failed in ' + str(counter) + \
                  ' out of ' + str(len(fring_dict[a])) + ' solutions.\n')
            log.write('    ' + antenna_dict[a] + ' failed in ' \
                      + str(counter) + ' out of ' + str(len(fring_dict[a])) \
                      + ' solutions.\n')
               
        print('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n')
        log.write('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n')   
        return
        
    # Dual polarization
    for s in sn_table:
        try:
            for i in range(len(s['weight_1'])):
                fring_dict[s['antenna_no']].append(s['weight_1'][i])
                fring_dict[s['antenna_no']].append(s['weight_2'][i])
        except TypeError: # Single IF datasets
            fring_dict[s['antenna_no']].append(s['weight_1'])
            fring_dict[s['antenna_no']].append(s['weight_2'])
    
    total_length = sum((len(v) for v in fring_dict.values()))
    global_counter = 0
    for a in fring_dict:
        counter = 0
        for val in fring_dict[a]:
            if val == 0:
                counter += 1
                global_counter += 1
        print(antenna_dict[a] + ' failed in ' + str(counter) + \
              ' out of ' + str(len(fring_dict[a])) + ' solutions.\n')
        log.write(antenna_dict[a] + ' failed in ' + str(counter) + \
                  ' out of ' + str(len(fring_dict[a])) + ' solutions.\n')
               
    print('Fringe fit failed in ' + str(global_counter) + ' out of '\
          + str(total_length) + ' solutions.\n')
    log.write('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n') 
    