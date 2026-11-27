import functools
print = functools.partial(print, flush=True)

import json

from vipcals.scripts.helper import tacop, edge_channel_range

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

def fringe_fit_with_fallback(data, refant, priority_refants, snr_cutoff,
                             fit_source, target, version, label='',
                             flag_edge=0):
    """Fringe fit fit_source into SN `version`. If <99% of solutions are
    good, retry averaging IFs (in a scratch SN table) and keep the better one.

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param priority_refants: list of alternatives to the reference antenna
    :type priority_refants: list of int
    :param snr_cutoff: S/N threshold for the FFT stage
    :type snr_cutoff: float
    :param fit_source: source to fringe fit (target or phase calibrator)
    :type fit_source: str
    :param target: target the solutions belong to
    :type target: :class:`~vipcals.scripts.helper.FFTarget`
    :param version: SN version where the final solutions are written
    :type version: int
    :param label: text before the source name in the log messages
    :type label: str, optional
    :param flag_edge: number of edge channels to ignore, either a fraction (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_edge: float, optional
    :return: multi-IF ratio, averaged-IF ratio, stats dictionary
    :rtype: float, float, dict
    """
    def has_sn(v):
        return [v, 'AIPS SN'] in data.tables

    def log(msg):
        print(msg)
        target.log.write(msg)

    stats = dict(good_sols=False, total_sols=False, ratios_dict=False,
                 good_sols_single=False, total_sols_single=False,
                 ratios_dict_single=False, single_ff=False)
    ratio = ratio_single = 0

    # Multi-IF fringe fit
    try:
        params = target_fring_fit(data, refant, priority_refants, fit_source,
                                  version=version, snr_cutoff=snr_cutoff,
                                  solint=float(target.solint), flag_edge=flag_edge)
        log(f'\nFringe search performed on {label}{fit_source}. Windows '
            f'for the search were {params[1]} ns and {params[2]} mHz.\n')
        bad, total, rdict = assess_fringe_fit(data, target.log, version=version)
        ratio = 1 - bad / total
        stats.update(good_sols=int(total - bad), total_sols=int(total),
                     ratios_dict=json.dumps(rdict))
    except RuntimeError:
        log('Fringe fit has failed.\n')

    if ratio >= 0.99:
        return ratio, ratio_single, stats

    # Retry averaging IFs, in a scratch table above all existing ones
    log(f'Ratio of good/total solutions is : {ratio:.2f}.\n'
        'Repeating the fringe fit solving for all IFs together:\n')
    scratch = max(data.table_highver('SN'), version) + 1
    try:
        params = target_fring_fit(data, refant, priority_refants, fit_source,
                                  version=scratch, snr_cutoff=snr_cutoff,
                                  solint=float(target.solint),
                                  solve_ifs=False, flag_edge=flag_edge)
        log(f'\nFringe search performed on {label}{fit_source}. Windows '
            f'for the search were {params[1]} ns and {params[2]} mHz.\n')
        bad_s, total_s, rdict_s = assess_fringe_fit(data, target.log,
                                                    version=scratch)
        ratio_single = 1 - bad_s / total_s
        stats.update(good_sols_single=int(total_s - bad_s),
                     total_sols_single=int(total_s),
                     ratios_dict_single=json.dumps(rdict_s))
    except RuntimeError:
        log('\nThe new fringe fit has failed, the previous one will be kept.\n')

    if ratio + ratio_single == 0:
        log('\nThe pipeline was not able to find any good solutions.\n')
        for v in (version, scratch):
            if has_sn(v):
                data.zap_table('SN', v)
        return ratio, ratio_single, stats

    log(f'New ratio of good/total solutions is : {ratio_single:.2f}.\n')
    if ratio_single > ratio:
        log('The averaged IF fringe fit will be applied.\n')
        if has_sn(version):
            data.zap_table('SN', version)
        tacop(data, 'SN', scratch, version)
        stats['single_ff'] = True
    else:
        log('The multi-IF fringe fit will be applied.\n')

    if has_sn(scratch):
        data.zap_table('SN', scratch)

    return ratio, ratio_single, stats
   
def target_fring_fit(data, refant, priority_refants, target_name, version, snr_cutoff,
                     solint, delay_w = 1000,\
                     rate_w = 200, solve_ifs = True,
                     flag_edge = 0):
    """Fringe fit the science target.

    Uses the FRING task on AIPS to correct for any residual delay and rate errors on the 
    phases. Creates a new SN table, which number depends on how many sources are being 
    calibrated, with the solutions from the first source being written to SN#6.

    Returns the reference antenna and the delay and search windows used to the main 
    workflow.

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param priority_refants: list of alternatives to the reference antenna
    :param priority_refants: list of int
    :param target_name: target name
    :type target_name: str
    :param version: SN version where to write the solutions.
    :type version: int
    :param snr_cutoff: S/N threshold for the FFT stage
    :type snr_cutoff: float
    :param solint: solution interval in minutes, if 0 => solint = 10 min, \
                   if > scan  => solint = scan
    :type solint: int
    :param delay_w: delay window in ns in which the search is performed; defaults to 1000\
    :type delay_w: int, optional
    :param rate_w: rate window in hz in which the search is performed; defaults to 200 \
    :type rate_w: int, optional 
    :param solve_ifs: solve IFs separatedly; defaults to True
    :type solve_ifs: bool, optional
    :param flag_edge: number of edge channels to ignore, either a fraction (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_edge: float, optional
    """       

    target_fring = AIPSTask('fring')
    target_fring.inname = data.name
    target_fring.inclass = data.klass
    target_fring.indisk = data.disk
    target_fring.inseq = data.seq
    target_fring.refant = refant
    target_fring.calsour = AIPSList([target_name])

    target_fring.bchan, target_fring.echan = edge_channel_range(data, flag_edge)
    
    target_fring.docalib = 1
    target_fring.gainuse = 8
    target_fring.doband = 1

    target_fring.solint = solint

    target_fring.aparm[1] = 2    # At least 2 antennas per solution

    # target_fring.aparm[3] = 1  # Average RR and LL

    if solve_ifs == True:
        target_fring.aparm[5] = 0    # Solve IFs separately
    else:
        target_fring.aparm[5] = 1    # Solve all IFs together

    target_fring.aparm[6] = 2    # Amount of information printed
    target_fring.aparm[7] = snr_cutoff    # SNR cutoff   
    target_fring.aparm[9] = 1    # Exhaustive search
    target_fring.search = AIPSList(priority_refants[:10])
    
    target_fring.dparm[1] = 1    # Number of baseline combinations searched
    target_fring.dparm[2] = delay_w  # Delay window (ns)
    target_fring.dparm[3] = rate_w  # Rate window (mHz)
    
    target_fring.snver = version
    
    target_fring.go()

    return(target_fring.refant, str(target_fring.dparm[2]), str(target_fring.dparm[3]))

def fringe_clcal(data, refant, target_list, target_scans, max_ver):
    """Apply SN solution table from FRING to a new CL table.

    Apply solution tables to a new calibration table using the CLCAL task in AIPS.
    Tables go from SN#6 to max_ver, and they correspond to science targets were phase 
    reference is not required. The new calibration tavle is always CL#9.

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param target_list: list of targets
    :type target_list: list of :class:`~vipcals.scripts.helper.FFTarget` objects
    :param target_scans: scans the target
    :type target_scans: list of :class:`~vipcals.scripts.helper.Scan` objects
    :param max_ver: maximum SN version to consider
    :type max_ver: int
    """    

    # Longest solution interval among the targets, in minutes
    max_solint = max(float(t.solint) for t in target_list)

    
    clcal = AIPSTask('clcal')
    clcal.inname = data.name
    clcal.inclass = data.klass
    clcal.indisk = data.disk
    clcal.inseq = data.seq
    clcal.refant = refant
    clcal.sources = AIPSList([t.name for t in target_list])
    
    clcal.opcode = 'CALP'
    clcal.interpol = 'SELF'
    # Maximum interpolation time range. Every point of a scan is within one solution
    # interval of a solution from the same scan, so solutions are never taken from
    # other scans further away
    clcal.cutoff = max_solint

    clcal.snver = 6
    clcal.invers = max_ver
    clcal.gainver = 8
    clcal.gainuse = 9

    clcal.go()

def fringe_phaseref_clcal(data, refant, target_list, version):
    """Apply phase reference SN solution table from FRING to a new CL table

    Apply phase reference solution tables to a new calibration table using the CLCAL 
    task in AIPS. These are always applied after the no-phase-reference solutions and 
    its done in multiple CLCAL runs, as many as phase reference sources are. Each time, 
    solutions are applied to CL#9, temporarily creating CL#10, which is then copied back 
    into CL#9. This ensures that CL#9 finally contains all solutions for all sources, 
    both phase referenced and not. 

    :param data: visibility data
    :type data: AIPSUVData
    :param refant: reference antenna number
    :type refant: int
    :param target_list: list of targets
    :type target_list: list of :class:`~vipcals.scripts.helper.FFtarget` objects
    :param version: first SN table version corresponding to the phase referenced sources
    :type version: int
    """    
    
    for i, target in enumerate(target_list):
        # Apply the solutions
        clcal = AIPSTask('clcal')
        clcal.inname = data.name
        clcal.inclass = data.klass
        clcal.indisk = data.disk
        clcal.inseq = data.seq
        clcal.refant = refant
        clcal.sources = AIPSList([target.name])
        clcal.calsour = AIPSList([target.phaseref])
        
        clcal.opcode = 'CALP'
        clcal.interpol = '2PT'
        clcal.snver = version + i
        clcal.gainver = 9
        clcal.gainuse = 10

        clcal.go()
        
        # Copy CL10 back into CL9
        data.zap_table('CL', 9)
        tacop(data, 'CL', 10, 9)
        data.zap_table('CL', 10)
 
def assess_fringe_fit(data, log, version = 6):
    """Retrieve the number of failed solutions after fringe fit

    Explore a solution table produced by FRING and print how many solutions failed. This 
    is done by looking at the weights of every entry in the SN table. Since each SN table 
    contains solutions only for one source, this information is also printed in the 
    corresponding log of each source.

    :param data: visibility data
    :type data: AIPSUVData
    :param log: pipeline log
    :type log: file
    :param version: SN version to evaluate, defaults to 6
    :type version: int, optional
    :return: total good solutions, total attempted solutions, 
        dictionary with good/attempted values per antenna
    :rtype: int, int, dict
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
    ratios_dict = {}
    for a in antennas:
        fring_dict[a] = []
        ratios_dict[a] = [0,0]

            
    # Single polarization:
    try:
        _ = sn_table[0]['weight_2']
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
            print('    ' + str(a) + '-' + antenna_dict[a] + ' failed in ' + str(counter) + \
                  ' out of ' + str(len(fring_dict[a])) + ' solutions.\n')
            log.write('    ' + str(a) + '-' + antenna_dict[a] + ' failed in ' \
                      + str(counter) + ' out of ' + str(len(fring_dict[a])) \
                      + ' solutions.\n')
            
            ratios_dict[a][0] = len(fring_dict[a]) - counter
            ratios_dict[a][1] = len(fring_dict[a])
               
        print('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n')
        log.write('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n')   
        
        return global_counter, total_length, ratios_dict
        
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
        print('    ' + str(a) + '-' + antenna_dict[a] + ' failed in ' + str(counter) + \
                ' out of ' + str(len(fring_dict[a])) + ' solutions.\n')
        log.write('    ' + str(a) + '-' + antenna_dict[a] + ' failed in ' \
                    + str(counter) + ' out of ' + str(len(fring_dict[a])) \
                    + ' solutions.\n')
        
        ratios_dict[a][0] = len(fring_dict[a]) - counter
        ratios_dict[a][1] = len(fring_dict[a])
               
    print('Fringe fit failed in ' + str(global_counter) + ' out of '\
          + str(total_length) + ' solutions.\n')
    log.write('Fringe fit failed in ' + str(global_counter) + ' out of '\
              + str(total_length) + ' solutions.\n') 
    
    return global_counter, total_length, ratios_dict