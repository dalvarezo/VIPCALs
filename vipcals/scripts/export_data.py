import os
import functools
print = functools.partial(print, flush=True)
import numpy as np

from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

import Wizardry.AIPSData as wizard

def data_export(path_list, data, target_list, filename_list, \
                ignore_list, channel_out, flag_edge = True, flag_frac = 0.1):
    """Split multi-source uv data to single source and export it to uvfits format.

    Uses the SPLIT task in AIPS to apply the calibration tables to each source and 
    split them into separate catalogue entries. By default, it averages visibilities 
    in frequency, producing one single channel per IF. If flag_edge is set as True, 
    it also omits the edge channels in each IF, to correct for roll-off. The number of 
    channels omitted can be given either as an integer number of channels, or as a 
    percentage. If the splitting fails, it calls 
    :function:`~vipcals.scripts.export_data.are_there_any_baselines`, to make sure 
    that there are enough data to be splitted. If that's not the case, the name of 
    that source is returned to the main workflow.
    Data splitted are named after each source, and they keep the sequence and class of 
    the original catalogue entry. 
    After splitting, data are exported into a uvfits file using the FITTP task in AIPS. 

    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str
    :param filename_list: list containing the subdirectories of each target
    :type filename_list: list of str
    :param ignore_list: list of targets to ignore because the fringe fit failed
    :type ignore_list: list of str
    :param channel_out: 'SINGLE' -> export one channel per IF, 'MULTI' -> export 
        multiple channels per IF
    :type channel_out: str
    :param flag_edge: flag edge channels; defaults to True
    :type flag_edge: bool, optional
    :param flag_frac: number of edge channels to flag, either a percentage (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_frac: float, optional
    :return: list of sources where no baselines could be formed, if any
    :rtype: list of str
    """
    no_baseline = []
    if flag_frac == 0:
        flag_edge = False

    # Delete the file if it already exists
    for name in target_list:
        if name in ignore_list:
            continue
        split_data = AIPSUVData(name, data.klass ,data.disk, data.seq)
        if split_data.exists():
            split_data.zap()

    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        split = AIPSTask('split')
        split.inname = data.name
        split.inclass = data.klass
        split.indisk = data.disk
        split.inseq = data.seq

        split.outdisk = data.disk
        split.outclass = data.klass
        split.outseq = data.seq

        split.sources = AIPSList([target])
        split.docal = 1
        split.gainuse = 9
        split.doband = 1
        if channel_out == 'SINGLE':
            split.aparm[1] = 2  # Average in frequency, produce one channel per IF
        if channel_out == 'MULTI':
            split.aparm[1] = 1  # DON't average in frequency, produce multiple channels 
                                # per IF
    
        if flag_edge == False or flag_frac == None:
            flag_chann = 0
            no_channels = 0

        else:
            try:
                no_channels = int(data.table('FQ',1)[0]['total_bandwidth'][0] / \
                            data.table('FQ',1)[0]['ch_width'][0])
            except TypeError:   # Single IF datasets
                no_channels = int(data.table('FQ',1)[0]['total_bandwidth'] / \
                            data.table('FQ',1)[0]['ch_width'])
                
            if flag_edge == True and flag_frac < 1:
                flag_chann = round(flag_frac * no_channels)
            if flag_edge == True and flag_frac >= 1:
                if type(flag_frac) != int:
                    flag_chann = 0
                else:
                    flag_chann = flag_frac

        split.bchan = flag_chann + 1
        split.echan = no_channels - flag_chann

        try:
            split.go()
        except RuntimeError:
            # Check if there are enough visibilities to make at least one baseline
            baselines = are_there_baselines(data, 9, target)
            if baselines == False:
                no_baseline.append(target)
            else:
                # THIS WILL CRASH THE PIPELINE, NEEDS TO BE ADDRESSED
                print("\n\nDATA COULD NOT BE EXPORTED \n\n")
                return(999)


    for i, target in enumerate(target_list):
        if target in ignore_list:
            continue
        if target not in no_baseline:
            fittp = AIPSTask('fittp')
            fittp.inname = target
            fittp.inclass = data.klass
            fittp.indisk = data.disk
            fittp.inseq = data.seq
            fittp.dataout = path_list[i] + '/' + filename_list[i] + '.uvfits'  
            fittp.go()

    return(no_baseline)

def table_export(path_list, data, target_list, filename_list):
    """Copy calibration tables to a dummy AIPS entry and export them.

    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str
    :param filename_list: list containing the subdirectories of each target
    :type filename_list: list of str
    """    

    tasav = AIPSTask('tasav')
    tasav.inname = data.name
    tasav.inclass = data.klass
    tasav.indisk = data.disk
    tasav.inseq = data.seq
    tasav.outname = data.name
    tasav.outclass = 'DUMMY'
    tasav.outdisk = data.disk
 
    tasav.go()

    for i, target in enumerate(target_list):
        fittp = AIPSTask('fittp')
        fittp.inname = data.name
        fittp.inclass = 'DUMMY'
        fittp.indisk = data.disk

        # AIPS name limit is 135 characters
        if len(path_list[i] + '/TABLES/' + filename_list[i] + '.caltab.uvfits') < 100:
            fittp.dataout = path_list[i] + '/TABLES/' + filename_list[i] \
                            + '.caltab.uvfits'
        # If the name is too long, save the tables on aux.caltab.fits   
        else:
            fittp.dataout = path_list[i] + '/TABLES/aux.caltab.uvfits' 
      
        fittp.go()

        # If created, rename aux.caltab.fits with the proper name
        if len(path_list[i] + '/TABLES/' + filename_list[i] + '.caltab.uvfits') >= 100:
            os.system('mv ' + path_list[i] + '/TABLES/aux.caltab.uvfits ' \
                      + path_list[i] + '/TABLES/' + filename_list[i] + '.caltab.uvfits')

    # Remove the DUMMY AIPS entry
    AIPSUVData(data.name, 'DUMMY', data.disk, 1).zap()


def data_split(data, target_list, cl_table = 1, bpass = False, flagver = 0, \
               keep = False):
    """Split source data applying different CL tables and/or the BP table.

    Uses the SPLIT task in AIPS to apply the calibration tables to each source and 
    split them into separate catalogue entries. There is no average in channels, and 
    only cross correlations are splitted. These are entries are later used by 
    :function:`~vipcals.scripts.export_data.vis_count` to compute the number of 
    unflagged visibilities.    
    The class of the splitted catalogue entries is "PLOTS", since these entries can be 
    also used for the interactive plots of the GUI.

    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str  
    :param cl_table: CL table number to apply; defaults to 1
    :type cl_table: int, optional
    :param bpass: apply the bandpass table; defaults to False
    :type bpass: bool, optional
    :param flagver: flag table version to apply, 0 => max; defaults to 0
    :type flagver: int, optional
    :param keep: delete previous entries for the same table; defaults to 0
    :type keep: bool, optional
    """

    for i, target in enumerate(target_list):
        # Remove the split file if it already exists
        if keep == False:
            if AIPSUVData(target, 'PLOT', data.disk, cl_table).exists() == True:
                AIPSUVData(target, 'PLOT', data.disk, cl_table).zap()
            
            if AIPSUVData(target, 'PLOTBP', data.disk, cl_table).exists() == True:
                AIPSUVData(target, 'PLOTBP', data.disk, cl_table).zap()

        data_split = AIPSTask('split')
        data_split.inname = data.name
        data_split.inclass = data.klass
        data_split.indisk = data.disk
        data_split.inseq = data.seq

        data_split.outdisk = data.disk
        if bpass == True:
            data_split.outclass = 'PLOTBP'
        else:
            data_split.outclass = 'PLOT'
        data_split.outseq = cl_table

        data_split.sources = AIPSList([target])

        data_split.docal = 1
        data_split.gainuse = cl_table
        data_split.flagver = flagver
        if bpass == True:
            data_split.doband = 1
        data_split.aparm[1] = 0  #Don't average frequency in IFs, multi-channel out
        data_split.aparm[5] = 0  # Pass ONLY xc

        data_split.go()

def vis_count(data):
    """Fast count of unflagged visibilities using NumPy vectorization.

    :param data: visibility data
    :type data: AIPSUVData
    :return: Total number of unflagged visibilities
    :rtype: int
    """
    n_vis = 0

    w_data = wizard.AIPSUVData(data.name, data.klass, data.disk, data.seq)

    for record in w_data:
        vis = record.visibility  # shape: [IF, chan, pol, N]
        # Extract weight axis (index 2 of the last dim)
        weights = vis[..., 2]  # shape: [IF, chan, pol]
        n_vis += np.count_nonzero(weights)

    return int(n_vis)

def are_there_baselines(data, table_number, source_name):
    """Check if there are enough unflagged visibilities to form at least a baseline.

    Given a soure name and a CL table, the function looks for visibilities in 2 or more 
    antennas at each timestamp. It can happen that only one antenna (the reference 
    antenna) has unflagged visibilities, as the fringe fit solutions are antenna based. 
    In that case, data cannot be splitted and this function returns a False value.

    :param data: visibility data
    :type data: AIPSUVData
    :param table_number: number of CL table where to perform the check
    :type table_number: int
    :param source_name: name of the source to be checked
    :type source_name: str
    :return: whether there are available baselines or not
    :rtype: bool
    """    
    for srcs in data.table('SU', 1):
        clean_name = srcs['source'].strip(' ')
        if clean_name == source_name:
            source_id = srcs['id__no']
            break
    table = data.table('CL', table_number)
    good_entries_RR = []
    good_entries_LL = []
    for element in table:
        if element['source_id'] == source_id:
            if any(x!=0 for x in element['weight_1']):
                good_entries_RR.append(element)
            try:
                if any(x!=0 for x in element['weight_2']):
                    good_entries_LL.append(element) 
            except KeyError:
                pass
    if len(good_entries_RR) == 0 and len(good_entries_LL) == 0:
        return(False) 
    # Check RR    
    for i, entry in enumerate(good_entries_RR):
        for j, entry_n in enumerate(good_entries_RR[i:]):
            if entry['time'] == entry_n['time']:
                if entry['antenna_no'] != entry_n['antenna_no']:
                    for k, wei in enumerate(entry['weight_1']):
                        if wei != 0 and entry_n['weight_1'][k] != 0:
                            return(True) 
    # Check LL    
    for i, entry in enumerate(good_entries_LL):
        for j, entry_n in enumerate(good_entries_LL[i:]):
            if entry['time'] == entry_n['time']:
                if entry['antenna_no'] != entry_n['antenna_no']:
                    for k, wei in enumerate(entry['weight_2']):
                        if wei != 0 and entry_n['weight_2'][k] != 0:
                            return(True)
    return(False)