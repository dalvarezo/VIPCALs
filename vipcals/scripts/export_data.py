import numpy as np
import os

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList

def data_export(filename, data, target_list, log, doflag = True, flag_frac = 0.1):
    """Split multi-source uv data to single source and export it to uvfits format.

    By default, it averages visibilities in frequency, producing one single channel 
    per IF. If doflag is set as True, it also omits the edge channels in each IF, to 
    correct for roll-off. The number of channels omitted can be given either as an 
    integer number of channels, or as a percentage.

    :param filename: name of the output folder 
    :type filename: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str
    :param log: pipeline log
    :type log: file
    :param doflag: flag edge channels; defaults to True
    :type doflag: bool, optional
    :param flag_frac: number of channels to flag, either a percentage (if < 1) or an \
                      integer number of channels (if >= 1); defaults to 0.1
    :type flag_frac: float, optional
    """
    split = AIPSTask('split')
    split.inname = data.name
    split.inclass = data.klass
    split.indisk = data.disk
    split.inseq = data.seq
    split.sources = AIPSList(target_list)
    split.docal = 1
    split.gainuse = 0
    split.doband = 1
    split.msgkill = -4
    split.aparm[1] = 2  # Average frequency in IFs, produce one channel per IF
    try:
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'][0] / \
                      data.table('FQ',1)[0]['ch_width'][0])
    except TypeError:   # Single IF datasets
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'] / \
                      data.table('FQ',1)[0]['ch_width'])
    if doflag == True and flag_frac < 1:
        flag_chann = int(flag_frac * no_channels)
    if doflag == True and flag_frac >= 1:
        if type(flag_frac) != int:
            flag_chann = 0
            # PRINT ERROR MESSAGE
        else:
            flag_chann = flag_frac
    split.bchan = flag_chann + 1
    split.echan = no_channels - flag_chann
    split.go()
    for target in target_list:
        fittp = AIPSTask('fittp')
        fittp.inname = target
        fittp.inclass = 'SPLIT'
        fittp.indisk = data.disk
        fittp.inseq = 1
        fittp.dataout = './' + filename + '/' + target + '.uvfits'
        fittp.msgkill = -4        
        fittp.go()
        #log.write('\n' + target + ' visibilites exported to ' + target + '.uvfits\n')
        print('\n' + target + ' visibilites exported to ' + target + '.uvfits\n')