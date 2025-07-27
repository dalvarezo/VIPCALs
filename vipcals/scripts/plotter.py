import warnings
import copy
import os
import pickle
import numpy as np

from matplotlib import pyplot as plt
import matplotlib as mpl
mpl.use('Agg')

from AIPSData import AIPSCat

import Wizardry.AIPSData as wizard

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

def possm_plotter(filepath, data, target, \
                  gainuse, bpver = 0, flagver = 0, \
                  flag_edge = False, flag_frac = 0.1):
    """Plot visibilities as a function of frequency to a PostScript file.

    Uses the POSSM task in AIPS to plot amplitudes and phases as a function of frequency.
    These plots are written into a ps file using the LWPLA task.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: target name
    :type target: str
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass; 
                  defaults to 0
    :type bpver: int, optional
    :param flagver: FG table version to use, if = 0 then apply the highest; 
                  defaults to 0
    :type flagver: int, optional
    :param flag_edge: flag edge channels; defaults to False
    :type flag_edge: bool, optional
    :param flag_frac: number of edge channels to flag, either a fraction (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_frac: float, optional
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir
    
    filename = filepath.split('/')[-1]
    
    possm = AIPSTask('possm')
    possm.inname = data.name
    possm.inclass = data.klass
    possm.indisk = data.disk
    possm.inseq = data.seq

    possm.sources = AIPSList([target])
    possm.stokes = 'RRLL'
    possm.solint = -1
    
    possm.docalib = 1
    possm.gainuse = gainuse

    if bpver > 0:
        possm.doband = 1
        possm.bpver = bpver

    try:
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'][0] / \
                      data.table('FQ',1)[0]['ch_width'][0])
    except TypeError:   # Single IF datasets
        no_channels = int(data.table('FQ',1)[0]['total_bandwidth'] / \
                      data.table('FQ',1)[0]['ch_width'])
        
    if flag_edge == True and flag_frac < 1:
        flag_chann = int(flag_frac * no_channels)
    if flag_edge == True and flag_frac >= 1:
        if type(flag_frac) != int:
            flag_chann = 0
        else:
            flag_chann = flag_frac
    if flag_edge == False:
        flag_chann = 0
    
    possm.bchan = flag_chann + 1
    possm.echan = no_channels - flag_chann

    possm.flagver = flagver

    possm.aparm = AIPSList([1, 1, 0, 0, -180, 180, 0, 0, 1, 0])
    possm.nplots = 9
    possm.dotv = -1
    
    possm.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
        else:
            raise RuntimeError("POSSM could not create any plot.")
    
    lwpla = AIPSTask('lwpla')
    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    outpath = filepath +  '/PLOTS/' + filename + '_CL' + str(gainuse) + '_POSSM.ps'
    if len(outpath) >= 114:
        lwpla.outfile = f'{tmp}/CL{gainuse}.ps'
    else:    
        lwpla.outfile = outpath
    
    lwpla.go()
    
    # If filename was long, move it
    if len(outpath) > 114:
        os.system(f'mv {tmp}/CL{gainuse}.ps {outpath}')
    # Clean all plots
    data.zap_table('PL', -1)


def uvplt_plotter(filepath, data, target, solint = 0.09):
    """Plot UV coverage for a source to a PostScript file.

    Uses the UVPLT task in AIPS to plot the UV coverage of a source. By default it plots 
    one visibility every 10 seconds.
    The plot is written into a ps file using the LWPLA task.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: target name
    :type target: str
    :param solint: time averaging interval in minutes; defaults to 0.09 (~5 seconds)
    :type solint: float, optional
    """    
    filename = filepath.split('/')[-1]

    uvplt = AIPSTask('uvplt')
    uvplt.inname = data.name
    uvplt.inclass = data.klass
    uvplt.indisk = data.disk
    uvplt.inseq = data.seq

    uvplt.sources = AIPSList([target])
    uvplt.docalib = 1
    uvplt.gainuse = 0

    uvplt.bparm = AIPSList([6, 7, 2, 0, 0, 0, 0, 0, 0, 0])  # (u,v) for x-  and y- axes
    uvplt.solint = solint  # Default is 0.17 min (10 seconds)

    uvplt.do3color = -1  # Black and white plot
    uvplt.dotv = -1
    
    uvplt.go()

    # Check if plots have been created, if not, exit with an error message
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            break
        else:
            raise RuntimeError("UVPLT could not create any plot.")
    
    # Export the plot

    lwpla = AIPSTask('lwpla')
    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = 1
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath + '/PLOTS/' + filename + '_UVPLT.ps'
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)


def vplot_plotter(filepath, data, target, gainuse, bpver = 0, avgif = 1, avgchan = 1, \
                  solint = 0.09):
    """Plot visibilities as a function of time to a PostScript file.

    Uses the VPLOT task in AIPS to plot amplitudes and phases of a source as a function 
    of time. By default it plots one visibility every ~5 seconds. Data are also averaged 
    in IFs and channels.
    The plot is written into a ps file using the LWPLA task.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass; \
                  defaults to 0
    :type bpver: int, optional
    :param avgif: average the data in IFs, 0 => False, 1 => True; defaults to 1
    :type avgif: int, optional
    :param avgchan: average the data in channels, 0 => False, 1 => True; defaults to 1
    :type avgchan: int, optional
    :param solint: time averaging interval in minutes; defaults to 0.09
    :type solint: float, optional
    """    
    filename = filepath.split('/')[-1]

    vplot = AIPSTask('vplot')
    vplot.inname = data.name
    vplot.inclass = data.klass
    vplot.indisk = data.disk
    vplot.inseq = data.seq

    vplot.sources = AIPSList([target])
    vplot.avgchan = avgchan
    vplot.avgif = avgif
    vplot.solint = solint

    vplot.docalib = 1
    vplot.gainuse = gainuse
    if bpver > 0:
        vplot.doband = 1
        vplot.bpver = bpver

    vplot.bparm = AIPSList([12, -1, 0, 0, 0, 0, 0, 0, 0, 0])  
                  # (IAT hours, Amp & Phase) for x-  and y- axes
    vplot.nplots = 2
    vplot.dotv = -1
    
    vplot.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
        else:
            raise RuntimeError("VPLOT could not create any plot.")
    
    lwpla = AIPSTask('lwpla')

    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath + '/PLOTS/' + filename + '_VPLOT.ps'
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)

def generate_pickle_plots(data, target_list, path_list):
    """Generate multiple plots and serialize them in a compressed format.

    The function applies all the different calibration tables to the data and 
    creates multiple matplotlib figures and dictionaries with each of them. 
    The figures (UVPLT, RADPLOT) are serialized with pickle and can be later displayed 
    in the GUI; the dictionaries (POSSM, VPLOT) are compressed in npz format and the GUI 
    can generate the plots with them.

    Generated plots are amp&phase vs freq (for each table), amp&phase vs time 
    (for the last table), amp&phase vs uvdist (for the last table), and 
    uv coverage. They are stored in a vipcals/tmp in order to be read 
    by the GUI.

    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str  
    :param path_list: list of paths of the visibilities
    :type path_list: list of str
    """
    an_table = data.table('AN', 1)
    disk = data.disk
    catalog = AIPSCat(disk)[disk]

    here = os.path.dirname(__file__)
    tmp = tmp_dir
    # Apply all calibrations tables to each target
    
    for i, target in enumerate(target_list):
        max_cl = max([x for x in catalog if x.name == target], 
                     key = lambda y: y.get('seq', float('-inf')))['seq']
        name =  path_list[i].split('/')[-1]
        # Generate amp&phas vs freq
        for n in range(max_cl):
            if (n+1) < 7:
                wuvdata = wizard.AIPSUVData(target, 'PLOT', data.disk, n+1)
                pickle_possm(wuvdata, tmp, name, an_table)
            else:
                wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, n+1)
                pickle_possm(wuvdata, tmp, name, an_table, bp=True)

        # Generate amp&phas vs time        
        pickle_vplot(wuvdata, tmp, name, an_table)

        # Generate amp&phas vs uvdist
        pickle_radplot(wuvdata, tmp, name)

        # Generate uvplot
        pickle_uvplt(wuvdata, tmp, name)


def generate_pickle_radplot(data, target_list, path_list):
    """Generate radplots and serialize them in pickle format.

    Exactly the same as :func:`~vipcals.scripts.plotter.generate_pickle_plots` but only 
    for the amplitudes&phases vs frequency. This function is called when the interactive 
    mode of the pipeline is disabled, since AIPS cannot generate these plots on its own 
    (or at least with the desired layout).

    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str  
    :param path_list: list of paths of the visibilities
    :type path_list: list of str
    """
    here = os.path.dirname(__file__)
    tmp = tmp_dir
    # Apply all calibrations tables to each target
    disk = data.disk
    catalog = AIPSCat(disk)[disk]
    for i, target in enumerate(target_list):
        max_cl = max([x for x in catalog if x.name == target], 
                key = lambda y: y.get('seq', float('-inf')))['seq']
        name =  path_list[i].split('/')[-1]
        # Generate amp&phas vs freq
        if max_cl < 7:
            wuvdata = wizard.AIPSUVData(target, 'PLOT', data.disk, max_cl)
            pickle_radplot(wuvdata, tmp, name)
        else:
            wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, max_cl)
            pickle_radplot(wuvdata, tmp, name)

def pickle_uvplt(wuvdata, path, name):
    """Generate uv-coverage plots and serialize them into a pickle object.

    Requires the Wizardry module, as it gives you full access to the visibilities.

    :param wuvdata: AIPSUVData from the Wizardry module
    :type wuvdata: Wizardry.AIPSData.AIPSUVData object
    :param path: path were to write the pickle object
    :type path: str
    :param name: name to be given to the file
    :type wuvdata: str
    """    
        
    u = []
    v = []
    fq_table = wuvdata.table('FQ', 0)
    if_freq = fq_table[0]['if_freq']
    central_freq =  wuvdata.header['crval'][2]
    for vis in wuvdata:
        for i, IF in enumerate(vis.visibility):
            if sum(IF.flatten()) == 0:      # Flagged visibility
                continue
            elif type(if_freq) == float:    # Single IF
                u.append(vis.uvw[0]/(1e6) * (1 + if_freq/central_freq))
                u.append(-vis.uvw[0]/(1e6) * (1 + if_freq/central_freq))     
                v.append(vis.uvw[1]/(1e6) * (1 + if_freq/central_freq))
                v.append(-vis.uvw[1]/(1e6) * (1 + if_freq/central_freq))
            else:                           # Multiple IFs
                u.append(vis.uvw[0]/(1e6) * (1 + if_freq[i]/central_freq))
                u.append(-vis.uvw[0]/(1e6) * (1 + if_freq[i]/central_freq))     
                v.append(vis.uvw[1]/(1e6) * (1 + if_freq[i]/central_freq))
                v.append(-vis.uvw[1]/(1e6) * (1 + if_freq[i]/central_freq))

    umax, vmax = max(u), max(v)
    m = 1.05* max(umax, vmax)

    uvplt_fig, ax = plt.subplots(1, 1, figsize=(8, 8))
    ax.scatter(u, v, marker = '.', s = 2, c = 'lime') 
    ax.set_xlim(+m, -m)
    ax.set_ylim(-m, +m)
    plt.gca().set_aspect('equal')
    ax.set_title('U-V coverage')
    ax.set_xlabel('U (M$\lambda$)')
    ax.set_ylabel('V (M$\lambda$)')

    with open(f'{path}/{name}.uvplt.pickle', 'wb') as f:
        pickle.dump(uvplt_fig, f)
    plt.close()

def pickle_radplot(wuvdata, path, name):
    """Generate visibility vs uvdist plots and serialize them into a pickle object.

    Produced plots are averaged in IFs (i.e. one value per IF) but not between IFs nor 
    in time. RR and LL polarizations are plotted together.
    Requires the Wizardry module, as it gives you full access to the visibilities.

    :param wuvdata: AIPSUVData from the Wizardry module
    :type wuvdata: Wizardry.AIPSData.AIPSUVData object
    :param path: path were to write the pickle object
    :type path: str
    :param name: name to be given to the file
    :type wuvdata: str
    """    

    central_freq = wuvdata.header['crval'][2]
    if_freq = wuvdata.table('FQ', 0)[0]['if_freq']
    reals_list = []
    imags_list = []
    amps = []
    phases = []
    uvdists = []

    # Go through each timestamp and record uv distance and IF-averaged visibilities
    for v in wuvdata:
        central_uv_dist = np.sqrt(v.uvw[0]**2 + v.uvw[1]**2)
        if type(if_freq) == float:  # Single IF
            uvdist = [central_uv_dist * (1+if_freq/central_freq)]
        else:
            uvdist = [central_uv_dist * (1+x/central_freq) for x in if_freq]
        visshape = v.visibility.shape
        if_avg_vis = np.zeros([visshape[0], 1, visshape[2], 
                                   visshape[3]], dtype = float)
        for IF in range(visshape[0]):
            for pol in range(visshape[2]):
                reals = v.visibility[IF, :, pol, 0]
                imags = v.visibility[IF, :, pol, 1]
                weights = v.visibility[IF, :, pol, 2]
                if np.sum(weights) == 0:
                    if_avg_vis[IF, 0, pol, 0] = 0
                    if_avg_vis[IF, 0, pol, 1] = 0
                    if_avg_vis[IF, 0, pol, 2] = 0
                else:
                    if_avg_vis[IF, 0, pol, :] = np.average(reals, weights= weights), \
                                                np.average(imags, weights= weights), \
                                                sum(weights)
            indx = np.nonzero(if_avg_vis[:,0,0,2])[0].tolist()
            reals_list.append(if_avg_vis[:, 0, 0, 0][indx])
            imags_list.append(if_avg_vis[:, 0, 0, 1][indx])
            uvdists += (np.array(uvdist)[indx]/1e6).tolist()
    reals_array = np.concatenate(reals_list)
    imags_array = np.concatenate(imags_list)
    amps = np.sqrt(reals_array**2 + imags_array**2).tolist()
    phases = (np.arctan2(imags_array, reals_array) * 360 / (2 * np.pi)).tolist()

    radplot_fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True) 
    radplot_fig.suptitle('Amp&Phase - UV Radius')

    # First subplot - Amplitudes vs. UV distances
    axes[0].scatter(uvdists, amps, label='Amplitude', marker = '.',
                    s = 1, c = 'lime')
    axes[0].set_ylabel('Amplitude (JY)')

    # Second subplot - Phases vs. UV distances
    axes[1].scatter(uvdists, phases, label='Phase', marker = '.',
                    s = 1, c = 'lime')
    axes[1].set_xlabel(r'UV Radius (M$\lambda$)')
    axes[1].set_ylabel('Phase (degrees)')

    plt.subplots_adjust(hspace=0)

    # Save the plot
    with open(f'{path}/{name}.radplot.pickle', 'wb') as f:
        pickle.dump(radplot_fig, f)
    plt.close()

def pickle_vplot(wuvdata, path, name, an_table):
    """Generate visibility vs time dicitonaries and compress them into a pickle object.

    Produces a dictionary with amplitude, phase, and timestamps of each baseline. This 
    is written into a pickle object, from which the GUI can generate plots. 
    Requires the Wizardry module, as it gives you full access to the visibilities.

    :param wuvdata: AIPSUVData from the Wizardry module
    :type wuvdata: Wizardry.AIPSData.AIPSUVData object
    :param path: path were to write the pickle object
    :type path: str
    :param name: name to be given to the file
    :type name: str
    :param an_table: table with the antenna information
    :type an_table: AIPSTable
    """    
    blines = [x.baseline for x in wuvdata]
    blines_unique =  list(set(tuple(x) for x in blines))
    vplot_dict = {}
    for bl in blines_unique:
        vplot_dict[bl] = []
        vis = [copy.deepcopy(x.visibility) for x in wuvdata if tuple(x.baseline) == bl]
        times = [copy.deepcopy(x.time) for x in wuvdata if tuple(x.baseline) == bl]
        amps = []
        phases= []
        for i, t in enumerate(times):
            real = np.average(vis[i][:,:,:,0].flatten(), weights = vis[i][:,:,:,2].flatten())
            imag = np.average(vis[i][:,:,:,1].flatten(), weights = vis[i][:,:,:,2].flatten())
            amps.append(np.sqrt(real**2 + imag**2))
            phases.append(np.arctan2(imag, real) * 360/np.pi)

        vplot_dict[bl].append(times)
        vplot_dict[bl].append(amps)
        vplot_dict[bl].append(phases)

        vplot_dict['ant_dict'] = {x.nosta: x.anname.strip() for x in an_table}
        
        with open(f'{path}/{name}.vplt.pickle', 'wb') as f:
            pickle.dump(vplot_dict, f)



def pickle_possm(wuvdata, path, name, an_table, bp = False):
    """Generate visibility vs freq dicitonaries and compress them into an npz object.

    Produces a dictionary with visiblities and frequency information of each baseline. 
    This is compressed into an npz object, from which the GUI can generate plots. 
    Requires the Wizardry module, as it gives you full access to the visibilities.

    :param wuvdata: AIPSUVData from the Wizardry module
    :type wuvdata: Wizardry.AIPSData.AIPSUVData object
    :param path: path were to write the pickle object
    :type path: str
    :param name: name to be given to the file
    :type name: str
    :param an_table: table with the antenna information
    :type an_table: AIPSTable
    """    

    POSSM = {}
    scans = []

    for s in wuvdata.table('NX', 1):
        scans.append((s['time'] - s['time_interval'], s['time'] + s['time_interval']))
    for v in wuvdata:
        try:
            _ = POSSM[tuple(v.baseline)]
        except KeyError:
            POSSM[tuple(v.baseline)] = [[] for x in range(len(scans))]
        for m, s in enumerate(scans):
            if v.time <= s[1] and v.time >= s[0]:
                vis = copy.deepcopy(v.visibility)
                POSSM[tuple(v.baseline)][m].append(vis)

    POSSM['ant_dict'] = {x.nosta: x.anname.strip() for x in an_table}
    POSSM['pols'] = list(wuvdata.polarizations)
    POSSM['if_freq'] = wuvdata.table('FQ', 0)[0]['if_freq']
    POSSM['total_bandwidth'] = wuvdata.table('FQ', 0)[0]['total_bandwidth']
    POSSM['ch_width'] = wuvdata.table('FQ', 0)[0]['ch_width']
    POSSM['central_freq'] = wuvdata.header['crval'][2]

    if bp == False:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.VisibleDeprecationWarning)
            POSSM_str = {str(key): np.array(value, dtype=object) for key, value in POSSM.items()}
            np.savez_compressed(f'{path}/{name}_CL{wuvdata.seq}.possm.npz', **POSSM_str)

            

    if bp == True:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.VisibleDeprecationWarning)
            POSSM_str = {str(key): np.array(value, dtype=object) for key, value in POSSM.items()}
            np.savez_compressed(f'{path}/{name}_CL{wuvdata.seq}_BP.possm.npz', **POSSM_str)
