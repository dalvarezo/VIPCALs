import warnings
import copy
import pickle
import numpy as np

from matplotlib import pyplot as plt

from AIPS import AIPS
from AIPSData import AIPSUVData
from AIPSTask import AIPSTask, AIPSList

import Wizardry.AIPSData as wizard

AIPSTask.msgkill = -1

class Datum(wizard._AIPSVisibility):
    def __init__(self):
        super().__init__()
        self.if_avg_vis = None
        self.uvdist = None
        self.visshape = None
        self.timestamp = None
        self.bline = None
        self.central_freq = None
    def set_attributes(self, if_freq):
        central_uv_dist = np.sqrt(self.uvw[0]**2 + self.uvw[1]**2)
        self.uvdist = [central_uv_dist * (1+x/self.central_freq) for x in if_freq]
        self.visshape = self.visibility.shape
        self.if_avg_vis = np.full([self.visshape[0], 1, self.visshape[2], 
                                   self.visshape[3]], 1, dtype = float)
        for IF in range(self.visshape[0]):
            for pol in range(self.visshape[2]):
                reals = self.visibility[IF, :, pol, 0]
                imags = self.visibility[IF, :, pol, 1]
                weights = self.visibility[IF, :, pol, 2]
                if sum(weights) == 0:
                    self.if_avg_vis[IF, 0, pol, 0] = 0
                    self.if_avg_vis[IF, 0, pol, 1] = 0
                    self.if_avg_vis[IF, 0, pol, 2] = 0
                else:
                    self.if_avg_vis[IF, 0, pol, :] = np.average(reals, weights= weights), \
                                                     np.average(imags, weights= weights), \
                                                     sum(weights)

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
    

def possm_plotter(filepath, data, target, cal_scans, \
                  gainuse, bpver = 0, flagver = 0, \
                  flag_edge = True, flag_frac = 0.1):
    """Plot visibilities as a function of frequency to a PostScript file.

    DOESNT PLOT THE CALIBRATORS ANYMORE! NEEDS TO BE MODIFIED

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param cal_scans: list of scans used for the calibration
    :type cal_scans: list of Scan object
    :param gainuse: CL version to apply
    :type gainuse: int
    :param bpver: BP table version to use, if = 0 then don't correct for bandpass; \
                  defaults to 0
    :type bpver: int, optional
    :param flagver: FG table version to use, if = 0 then apply the highest; \
                  defaults to 0
    :type flagver: int, optional
    :param flag_edge: flag edge channels; defaults to True
    :type flag_edge: bool, optional
    :param flag_frac: number of edge channels to flag, either a percentage (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_frac: float, optional
    """    
    
    filename = filepath.split('/')[-1]

    #calib_names = [x.name for x in cal_scans]
    
    possm = AIPSTask('possm')
    possm.inname = data.name
    possm.inclass = data.klass
    possm.indisk = data.disk
    possm.inseq = data.seq

    #possm.sources = AIPSList(calib_names + [target])
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
            # I NEED TO PRINT AN ERROR MESSAGE
        else:
            flag_chann = flag_frac
    if flag_edge == False:
        flag_chann = 0
    
    possm.bchan = flag_chann + 1
    possm.echan = no_channels - flag_chann

    possm.aparm = AIPSList([1, 1, 0, 0, -180, 180, 0, 0, 1, 0])
    possm.nplots = 9
    
    possm.dotv = -1
    # possm.msgkill = -4
    
    possm.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
        return(999)
    
    lwpla = AIPSTask('lwpla')
    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath +  '/PLOTS/' + filename + '_CL' + str(gainuse) + '_POSSM.ps'
    
    # lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)


def uvplt_plotter(filepath, data, target, solint = 0.17):
    """Plot UV coverage for a source to a PostScript file.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param target: science target name
    :type target: str
    :param solint: time averaging interval in minutes; defaults to 0.17
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
    # uvplt.msgkill = -4
    
    uvplt.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
        return(999)
    
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
    
    # lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)


def vplot_plotter(filepath, data, target, gainuse, bpver = 0, avgif = 1, avgchan = 1, \
                  solint = 0.17):
    """Plot visibilities as a function of time to a PostScript file.

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
    :param solint: time averaging interval in minutes; defaults to 0.17
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
    # vplot.msgkill = -4
    
    vplot.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
        return(999)
    
    lwpla = AIPSTask('lwpla')

    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath + '/PLOTS/' + filename + '_VPLOT.ps'
    
    # lwpla.msgkill = -4
    
    lwpla.go()
    
    # Clean all plots
    data.zap_table('PL', -1)

def generate_pickle_plots(data, target_list, path_list):
    """Generate multiple plots and serialize them in pickle format.

    The function applies all the different calibration tables to the data and 
    creates multiple matplotlib figures with each of them. This figures are 
    serialized with pickle and can be later displayed in the GUI.

    Generated plots are amp&phase vs freq (for each table), amp&phase vs time 
    (for the last table), amp&phase vs uvdist (for the last table), and 
    uv coverage. They are stores in a temporary directory in order to be read 
    by the GUI.

    :param data: visibility data
    :type data: AIPSUVData
    :param target_list: list of sources to split
    :type target_list: list of str  
    :param path_list: list of paths of the visibilities
    :type path_list: list of str
    """
    # Apply all calibrations tables to each target
    max_cl = data.table_highver('CL')
    for i, target in enumerate(target_list):
        name =  path_list[i].split('/')[-1]
        # Generate amp&phas vs freq
        for n in range(max_cl):
            if (n+1) < 7:
                wuvdata = wizard.AIPSUVData(target, 'PLOT', data.disk, n+1)
                pickle_possm(wuvdata, '../tmp/', name)
            else:
                wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, n+1)
                pickle_possm(wuvdata, '../tmp/', name ,bp=True)

        # Generate amp&phas vs time
        wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, max_cl)
        pickle_vplot(wuvdata, '../tmp/', name)

        # Generate amp&phas vs uvdist
        wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, max_cl)
        pickle_radplot(wuvdata, '../tmp/', name)

        # Generate uvplot
        wuvdata = wizard.AIPSUVData(target, 'PLOTBP', data.disk, max_cl)
        pickle_uvplt(wuvdata, '../tmp/', name)

        # Delete the AIPS entries
        #for n in range(max_cl):
        #    pickle_data = AIPSUVData(target, 'PLOTS', data.disk, n+1)
        #    pickle_data.zap()

def pickle_uvplt(wuvdata, path, name):
        u = []
        v = []
        fq_table = wuvdata.table('FQ', 0)
        if_freq = fq_table[0]['if_freq']
        central_freq =  wuvdata.header['crval'][2]
        for vis in wuvdata:
            for i, IF in enumerate(vis.visibility):
                if sum(IF.flatten()) == 0:
                    continue
                else:
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
        #plt.show()
        with open(f'{path}{name}.uvplt.pickle', 'wb') as f:
            pickle.dump(uvplt_fig, f)
        plt.close()

def pickle_radplot(wuvdata, path, name):
    central_freq = wuvdata.header['crval'][2]
    if_freq = wuvdata.table('FQ', 0)[0]['if_freq']
    reals_list = []
    imags_list = []
    amps = []
    phases = []
    uvdists = []
    for v in wuvdata:
        central_uv_dist = np.sqrt(v.uvw[0]**2 + v.uvw[1]**2)
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
            #imags_list = np.concatenate([imags_list, if_avg_vis[:, 0, 0, 1][indx]])
            uvdists += (np.array(uvdist)[indx]/1e6).tolist()
    reals_array = np.concatenate(reals_list)
    imags_array = np.concatenate(imags_list)
    amps = np.sqrt(reals_array**2 + imags_array**2).tolist()
    phases = (np.arctan2(imags_array, reals_array) * 360 / (2 * np.pi)).tolist()
    #return(amps,phases,uvdists)
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
    with open(f'{path}{name}.radplot.pickle', 'wb') as f:
        pickle.dump(radplot_fig, f)

def pickle_vplot(wuvdata, path, name):
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
        
        #fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True) 
        #fig.suptitle('Amp&Phase - UV Radius')

        # First subplot - Amplitudes vs. UV distances
        #axes[0].scatter(times, amps, label='Amplitude', marker = '.',
        #                s = 3, c = 'k')
        #axes[0].set_ylabel('Amplitude (JY)')
        #axes[0].set_ylim(bottom = 0, top = 1.15* max(amps))

        # Second subplot - Phases vs. UV distances
        #axes[1].scatter(times, phases, label='Phase', marker = '.',
        #                s = 3, c = 'k')
        #axes[1].set_xlabel('Time')
        #axes[1].set_ylabel('Phase (degrees)')
        #with open(f'{path}{wuvdata.name}_{bl[0]}_{bl[1]}.vplt.pickle', 'wb') as f:
        #    pickle.dump(fig, f)
        with open(f'{path}{name}.vplt.pickle', 'wb') as f:
            pickle.dump(vplot_dict, f)
        #plt.close(vplot_dict)

def pickle_possm(wuvdata, path, name, bp = False):
    blines = [x.baseline for x in wuvdata]
    blines_unique =  list(set(tuple(x) for x in blines))
    POSSM = {}
    scans = []

    for s in wuvdata.table('NX', 1):
        scans.append((s['time'] - + s['time_interval'], s['time'] + s['time_interval']))
    for v in wuvdata:
        try:
            _ = POSSM[tuple(v.baseline)]
        except KeyError:
            POSSM[tuple(v.baseline)] = [[] for x in range(len(scans))]
        for m, s in enumerate(scans):
            if v.time <= s[1] and v.time >= s[0]:
                vis = copy.deepcopy(v.visibility)
                POSSM[tuple(v.baseline)][m].append(vis)

    POSSM['if_freq'] = wuvdata.table('FQ', 0)[0]['if_freq']
    POSSM['total_bandwidth'] = wuvdata.table('FQ', 0)[0]['total_bandwidth']
    POSSM['ch_width'] = wuvdata.table('FQ', 0)[0]['ch_width']
    POSSM['central_freq'] = wuvdata.header['crval'][2]

    if bp == False:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.VisibleDeprecationWarning)
            POSSM_str =  {str(key): value for key, value in POSSM.items()}
            np.savez_compressed(f'{path}{name}_CL{wuvdata.seq}.possm.npz', **POSSM_str)
            

    if bp == True:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.VisibleDeprecationWarning)
            POSSM_str =  {str(key): value for key, value in POSSM.items()}
            np.savez_compressed(f'{path}{name}_CL{wuvdata.seq}_BP.possm.npz', **POSSM_str)

def interactive_possm(POSSM, bline, scan):
            
            n = scan
    #for n, scan in enumerate(scans):
            bl = bline
        #for bl in blines_unique:
            reals = np.array(POSSM[bl][n])[:,:,:,:,0]
            imags = np.array(POSSM[bl][n])[:,:,:,:,1]
            weights = np.array(POSSM[bl][n])[:,:,:,:,2]
            avg_reals = sum(reals*weights)/sum(weights)
            avg_imags = sum(imags*weights)/sum(weights) 
            amps = np.sqrt(avg_reals**2 + avg_imags**2).flatten()
            phases = (np.arctan2(avg_imags, avg_reals) * 360/(2*np.pi)).flatten()
            
            if_freq = POSSM['if_freq']
            # central_freq =  wuvdata.header['crval'][2]
            chan_freq = []
            for IF, freq in enumerate(if_freq):
                n_chan = int(POSSM['total_bandwidth'][IF]/POSSM['ch_width'][IF])
                for c in range(n_chan):
                    chan_freq.append(POSSM['central_freq'] + freq + c * POSSM['ch_width'][IF]) 
            chan_freq = np.array(chan_freq) / 1e9
            # Number of chunks
            chunk_size = n_chan
            num_chunks = len(chan_freq) // chunk_size
            possm_fig, axes = plt.subplots(2, num_chunks, figsize=(8, 4), gridspec_kw = {'height_ratios': [1,2]})
            axes_top, axes_bottom = axes
            # Plot each chunk in its respective subplot
            for i in range(num_chunks):
                start, end = i * chunk_size, (i + 1) * chunk_size   
                axes_top[i].plot(chan_freq[start:end], phases[start:end], color="g",  mec = 'c', mfc='c', marker="+", markersize = 12,
                                linestyle="none")
                axes_bottom[i].plot(chan_freq[start:end], amps[start:end], color="g",  mec = 'c', mfc='c', marker="+", markersize = 12, )
                axes_top[i].hlines(y = 0, xmin =  chan_freq[start], xmax = chan_freq[end-1], color = 'y')
                axes_top[i].set_ylim(-180,180)
                axes_bottom[i].set_ylim(0, np.nanmax(amps) * 1.10)
                axes_top[i].tick_params(labelbottom=False)
                axes_top[i].spines['bottom'].set_color('yellow')
                axes_top[i].spines['top'].set_color('yellow')
                axes_top[i].spines['right'].set_color('yellow')
                axes_top[i].spines['left'].set_color('yellow')
                axes_bottom[i].spines['bottom'].set_color('yellow')
                axes_bottom[i].spines['top'].set_color('yellow')
                axes_bottom[i].spines['right'].set_color('yellow')
                axes_bottom[i].spines['left'].set_color('yellow')
            axes_top[0].set_ylabel('Phase (Degrees)', fontsize = 16)
            axes_bottom[0].set_ylabel('Amplitude (Jy)', fontsize = 16)
            plt.style.use('dark_background')
            possm_fig.supxlabel("Frequency (GHz)", fontsize = 16)
            plt.subplots_adjust(wspace=0, hspace = 0)  # No horizontal spacing

            plt.show()   
