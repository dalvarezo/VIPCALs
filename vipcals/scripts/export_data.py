import numpy as np
import os
import string

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList
from AIPSData import AIPSUVData

import Wizardry.AIPSData as wizard

import functools
print = functools.partial(print, flush=True)

AIPSTask.msgkill = -8

def are_there_baselines(data, table_number, source_name):
    """Check if there are enough unflagged visibilities to form at least a baseline

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


def data_export(path_list, data, target_list, filename_list, flag_edge = True, \
                flag_frac = 0.1):
    """Split multi-source uv data to single source and export it to uvfits format.

    By default, it averages visibilities in frequency, producing one single channel 
    per IF. If flag_edge is set as True, it also omits the edge channels in each IF, to 
    correct for roll-off. The number of channels omitted can be given either as an 
    integer number of channels, or as a percentage.

    :param path_list: list of filepaths for each source
    :type path_list: list of str
    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str
    :param filename_list: list containing the subdirectories of each target
    :type filename_list: list of str
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

    # The 'IGNORE' part has to be changed, it's not needed anymore!
    for name in target_list:
        if name == 'IGNORE':
            continue
        split_data = AIPSUVData(name, data.klass ,data.disk, data.seq)
        if split_data.exists():
            split_data.zap()

    for i, target in enumerate(target_list):
        if target == 'IGNORE':
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
        split.gainuse = 9+i
        split.doband = 1
        # split.msgkill = -4
        split.aparm[1] = 2  # Average frequency in IFs, produce one channel per IF
    
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
                # I NEED TO PRINT AN ERROR MESSAGE
            else:
                flag_chann = flag_frac
        if flag_edge == False:
            flag_chann = 0

        split.bchan = flag_chann + 1
        split.echan = no_channels - flag_chann
        try:
            split.go()
        except RuntimeError:
            # Check if there are enough visibilities to make at least one baseline
            baselines = are_there_baselines(data, 9+i, target)
            if baselines == False:
                no_baseline.append(target)
            else:
                # THIS WILL CRASH THE PIPELINE, NEEDS TO BE ADDRESSED
                print("\n\nDATA COULD NOT BE EXPORTED \n\n")
                return(999)


    for i, target in enumerate(target_list):
        if target == 'IGNORE':
            continue
        if target not in no_baseline:
            fittp = AIPSTask('fittp')
            fittp.inname = target
            fittp.inclass = data.klass
            fittp.indisk = data.disk
            fittp.inseq = data.seq
            fittp.dataout = path_list[i] + '/' + filename_list[i] + '.uvfits'
            # fittp.msgkill = -4        
            fittp.go()

    return(no_baseline)

def table_export(path_list, data, target_list, filename_list):
    """Copy calibration tables to a dummy file and export them.

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

        # fittp.msgkill = -4        
        fittp.go()

        # If created, rename aux.caltab.fits with the proper name
        if len(path_list[i] + '/TABLES/' + filename_list[i] + '.caltab.uvfits') >= 100:
            os.system('mv ' + path_list[i] + '/TABLES/aux.caltab.uvfits ' \
                      + path_list[i] + '/TABLES/' + filename_list[i] + '.caltab.uvfits')

    # Remove the DUMMY AIPS entry
    AIPSUVData(data.name, 'DUMMY', data.disk, 1).zap()


def data_split(data, target_list, cl_table = 1, bpass = False):
    """Split source data applying different CL tables and/or the BP table.

    The class of the splitted catalogue entries is "PLOTS", since this entries 
    can be later used for the interactive plots of the GUI.

    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str  
    :param cl_table: CL table number to apply; defaults to 1
    :type cl_table: int, optional
    :param bpass: apply the bandpass table; defaults to False
    :type bpass: bool, optional
    """

    for i, target in enumerate(target_list):
        # Remove the split file if it already exists
        if AIPSUVData(target, 'PLOTS', data.disk, cl_table).exists() == True:
            AIPSUVData(target, 'PLOTS', data.disk, cl_table).zap()

        data_split = AIPSTask('split')
        data_split.inname = data.name
        data_split.inclass = data.klass
        data_split.indisk = data.disk
        data_split.inseq = data.seq

        data_split.outdisk = data.disk
        data_split.outclass = 'PLOTS'
        data_split.outseq = cl_table

        data_split.sources = AIPSList([target])

        data_split.docal = 1
        data_split.gainuse = cl_table
        if bpass == True:
            data_split.doband = 1
        data_split.aparm[1] = 1  #Don't average frequency in IFs, multi-channel out
        # TEST        
        data_split.aparm[5] = 1  # Pass xc and ac
        data_split.go()

def vis_count(data):
    """Count how many visibilities are unflagged in a catalogue entry.
    
    :param data: visibility data
    :type data: AIPSUVData    
    """

    n_vis_final = 0

    wfinal_data = wizard.AIPSUVData(data.name, data.klass, data.disk, data.seq)

    for x in wfinal_data:
        for IF in x.visibility:
            for chan in IF:
                for pol in chan:
                    if pol[2] != 0:
                        n_vis_final += 1 
                        #for antennas in list(set(x.baseline)):
                        #    final_dict[antennas] += 1

    return(n_vis_final)