import warnings
import copy
import ast
import os
import subprocess
import sys
import shutil
import pickle
import numpy as np

from pathlib import Path
from matplotlib import pyplot as plt
import matplotlib as mpl
from matplotlib.ticker import ScalarFormatter
from scipy.interpolate import PchipInterpolator
mpl.use('Agg')

from vipcals.scripts.helper import edge_channel_range

from AIPSData import AIPSCat

import Wizardry.AIPSData as wizard

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

# Check if /home/vipcals exists
if os.path.isdir("/home/vipcals"):
    tmp_dir = "/home/vipcals/.vipcals/tmp"

def find_ghostscript():
    """Locate the Ghostscript executable on the system."""
    if sys.platform.startswith("win"):
        candidates = ["gswin64c.exe", "gswin32c.exe"]
    else:
        candidates = ["gs"]
    
    for cmd in candidates:
        path = shutil.which(cmd)
        if path:
            return path
    raise RuntimeError(
        "Ghostscript executable not found. "
        "Please install 'ghostscript' in your Conda environment."
    )

def ps_to_pdf(ps_path):
    ps_path = str(ps_path)
    pdf_path = str(Path(ps_path).with_suffix(".pdf"))

    # Find Ghostscript executable
    gs_path = find_ghostscript()

    subprocess.run(["ps2pdf", ps_path, pdf_path], check=True)

    # Remove the original PS file
    os.remove(ps_path)

def plot_vis_per_antenna(stats_df, target_list, filename_list, outpath_list):
    """Plot visibility count per antenna across the pipeline.

    :param stats_df: _description_
    :type stats_df:
    :param target_list: list of sources to plot
    :type target_list: list of str
    :param filename_list: list of names to use in the plots
    :type filename_list: list of str
    :param outpath_list: list of paths where to save the plots
    :type outpath_list: list of str
    """    
    markers = [
    "o", "s",  "D", "^",  "v", "<", ">","p", "P", "X",  "*","h", 
    "H","+", "x", "1", "2","3", "4","|","_" ]

    col_names = ['CL1_ant_vis', 'CL1_FG2_ant_vis',
                'CL2_ant_vis', 'CL3_ant_vis',
                'CL4_ant_vis', 'CL4_FG3_ant_vis',
                'CL5_ant_vis', 'CL6_ant_vis',
                'CL6_BP1_ant_vis', 'CL7_BP1_ant_vis',
                'CL8_BP1_ant_vis', 'CL9_BP1_ant_vis']   
         
    for i, target in enumerate(target_list):
        idx = stats_df.index[stats_df["target"] == target].tolist()[0]
        dicts = [ast.literal_eval(stats_df.loc[idx, col]) for col in col_names]
        antennas = list(dicts[0].keys())
        x_orig = np.arange(len(dicts)) 
        x_smooth = np.linspace(x_orig.min(), x_orig.max(), 200)
        max_val = max(max(d.values()) for d in dicts)

        x_labels = ['CL1', 'CL1_FG2', 'CL2', 'CL3', 'CL4', 
                    'CL4_FG3', 'CL5', 'CL6', 'CL6_BP',
                    'CL7_BP', 'CL8_BP', 'CL9_BP']
        
        plt.figure(figsize=(13, 5))

        for j, ant in enumerate(antennas):
            y_orig = [d[ant] for d in dicts]
            f = PchipInterpolator(x_orig, y_orig)
            y_smooth = f(x_smooth)

            plt.plot(x_smooth, y_smooth, label=ant, linestyle = 'dotted', lw = 2, 
                     alpha = 0.75, marker=markers[j % len(markers)], markevery = 8)

        plt.xlabel("Steps", fontsize = 16)
        plt.xticks(ticks=range(len(dicts)), labels=x_labels, rotation=45, fontsize = 12)

        plt.gca().yaxis.set_major_formatter(ScalarFormatter(useMathText=True))
        plt.gca().yaxis.get_major_formatter().set_scientific(True)
        plt.gca().yaxis.get_major_formatter().set_powerlimits((0,0)) 
        plt.ylim(0, 1.1 * max_val)  
        plt.ylabel("Visibility count",  fontsize = 16)

        plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize = 13)
        plt.tight_layout()
        plt.savefig(f'{outpath_list[i]}/PLOTS/{filename_list[i]}_VISANT.pdf', 
                    bbox_inches='tight', dpi=260, format='pdf')
        plt.close()

def possm_plotter(filepath, data, target, \
                  gainuse, bpver = 0, flagver = 0, \
                  flag_edge = 0):
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
    :param flag_edge: number of edge channels to flag, either a fraction (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_edge: float, optional
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

    possm.bchan, possm.echan = edge_channel_range(data, flag_edge)

    possm.flagver = flagver

    possm.aparm = AIPSList([1, 1, 0, 0, -180, 180, 0, 0, 1, 0])
    possm.nplots = 9
    possm.dotv = -1
    
    possm.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    max_plot = 0
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
    if max_plot == 0:
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
    if len(outpath) >= 110:
        lwpla.outfile = f'{tmp}/CL{gainuse}.ps'
    else:    
        lwpla.outfile = outpath
    
    lwpla.go()
    
    # If filename was long, move it
    if len(outpath) >= 110:
        shutil.move(f'{tmp}/CL{gainuse}.ps', outpath)

    # Convert to pdf
    ps_to_pdf(outpath)
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
    max_plot = 0
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
    if max_plot == 0:
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
    if len(filepath + '/PLOTS/' + filename + '_UVPLT.ps') < 110:
        lwpla.outfile = filepath + '/PLOTS/' + filename + '_UVPLT.ps'
    else:
        lwpla.outfile = tmp_dir + '/aux.uvplt.ps'
    
    lwpla.go()

    # If the filepath name was too long, move the auxiliary file to the correct place
    if len(filepath + '/PLOTS/' + filename + '_UVPLT.ps') >= 110:
        shutil.move(tmp_dir + '/aux.uvplt.ps', filepath 
                    + '/PLOTS/' + filename + '_UVPLT.ps')

    # Convert to pdf
    ps_to_pdf(filepath + '/PLOTS/' + filename + '_UVPLT.ps')
    # Clean all plots
    data.zap_table('PL', -1)


def vplot_plotter(filepath, data, target, gainuse, bpver = 0, avgif = 1, avgchan = 1, \
                  solint = 0.09, flag_edge = 0):
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
    :param flag_edge: number of edge channels to flag, either a fraction (if < 1) \
                      or an integer number of channels (if >= 1); defaults to 0.1
    :type flag_edge: float, optional
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
    vplot.bchan, vplot.echan = edge_channel_range(data, flag_edge)
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
    max_plot = 0
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
    if max_plot == 0:
        raise RuntimeError("VPLOT could not create any plot.")
    
    lwpla = AIPSTask('lwpla')

    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])

    if len(filepath + '/PLOTS/' + filename + '_VPLOT.ps') < 110:
        lwpla.outfile = filepath + '/PLOTS/' + filename + '_VPLOT.ps'
    else:
        lwpla.outfile = tmp_dir + '/aux.vplot.ps'
    
    lwpla.go()

    # If the filepath name was too long, move the auxiliary file to the correct place
    if len(filepath + '/PLOTS/' + filename + '_VPLOT.ps') >= 110:
        shutil.move(tmp_dir + '/aux.vplot.ps', filepath 
                    + '/PLOTS/' + filename + '_VPLOT.ps')
        
    # Convert to pdf
    ps_to_pdf(filepath + '/PLOTS/' + filename + '_VPLOT.ps')
    # Clean all plots
    data.zap_table('PL', -1)

def tsys_plotter(filepath, data, tyver = 1):
    """Plot system temperatures as a function of time to a PostScript file.

    Uses the SNPLT task in AIPS to plot system temperatures of the antennas as a function 
    of time. Only points relevant to the observation are plotted.
    The plot is written into a ps file using the LWPLA task.

    :param filepath: path of the output directory 
    :type filepath: str
    :param data: visibility data
    :type data: AIPSUVData
    :param tyver: TY table version to print; defaults to 1
    :type tyver: int, optional
    """    
    filename = filepath.split('/')[-1]

    snplt = AIPSTask('snplt')
    snplt.inname = data.name
    snplt.inclass = data.klass
    snplt.indisk = data.disk
    snplt.inseq = data.seq

    snplt.inext = 'TY'
    snplt.optype = 'TSYS'
    snplt.invers = tyver
    snplt.nplots = 8

    snplt.dotv = -1
    
    snplt.go()

    # Check if plots have been created, if not, exit with an error message
    # Also get the maximum plot file number 
    max_plot = 0
    for elements in reversed(data.tables):
        if 'AIPS PL' in elements:
            max_plot = elements[0]
            break
    if max_plot == 0:
        raise RuntimeError("SNPLT could not create any plot.")
    
    lwpla = AIPSTask('lwpla')

    lwpla.inname = data.name
    lwpla.inclass = data.klass
    lwpla.indisk = data.disk
    lwpla.inseq = data.seq

    lwpla.plver = 1
    lwpla.invers = max_plot
    
    lwpla.dparm = AIPSList([0, 0, 0, 0, 0, 4, 31, 7, 0 ])
    lwpla.outfile = filepath + '/PLOTS/' + filename + '_TSYS_TY' + str(tyver) + '.ps'

    if len(filepath + '/PLOTS/' + filename + '_TSYS_TY' + str(tyver) + '.ps') < 110:
        lwpla.outfile = filepath + '/PLOTS/' + filename + '_TSYS_TY' + str(tyver) + '.ps'
    else:
        lwpla.outfile = tmp_dir + f'/aux.tsys{tyver}.ps'
    
    lwpla.go()

    # If the filepath name was too long, move the auxiliary file to the correct place
    if len(filepath + '/PLOTS/' + filename + '_TSYS_TY' + str(tyver) + '.ps') >= 110:
        shutil.move(tmp_dir + f'/aux.tsys{tyver}.ps', filepath + '/PLOTS/' 
                    + filename + '_TSYS_TY' + str(tyver) + '.ps')
    
    # Convert to pdf
    ps_to_pdf(filepath + '/PLOTS/' + filename + '_TSYS_TY' + str(tyver) + '.ps')
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
        max_cl = max([x.seq for x in catalog if x.name==target 
                      and 'PLOT' in x.klass])
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
        max_cl = max([x.seq for x in catalog if x.name==target 
                      and 'PLOT' in x.klass])
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

def pickle_radplot(wuvdata, path, name, difmap_convention=True):
    """Generate visibility vs uvdist plots and serialize them into a pickle object.

    For dual-polarization data (RR, LL, ...), Stokes I is formed per channel as
    (RR + LL) / 2. If the data are already in Stokes I, they are used directly. For
    single-polarization data (only RR or only LL), that polarization is plotted on its
    own and the plot title states which one it is.
    Visibilities are averaged over channels within each IF (i.e. one value per IF), but
    not between IFs nor in time. Flagged data (non-positive weights) are excluded.
    Requires the Wizardry module, as it gives you full access to the visibilities.

    :param wuvdata: AIPSUVData from the Wizardry module
    :type wuvdata: Wizardry.AIPSData.AIPSUVData object
    :param path: path were to write the pickle object
    :type path: str
    :param name: name to be given to the file
    :type name: str
    :param difmap_convention: if True, flip the sign of the phases to match the
    convention used by Difmap (equivalent to plotting the complex conjugate)
    :type difmap_convention: bool
    :raises ValueError: if the Stokes axis is not supported (e.g. linear feeds)
    """
    # Read axes from the header instead of assuming their order
    ctype = [c.strip() for c in wuvdata.header['ctype']]
    crval = wuvdata.header['crval']
    stokes_idx = ctype.index('STOKES')
    central_freq = crval[ctype.index('FREQ')]
    stokes_start = crval[stokes_idx]
    npol = wuvdata.header['naxis'][stokes_idx]

    # Decide what to plot: Stokes I if possible, otherwise the single available hand
    if stokes_start == 1:
        mode, pol_label = 'single', 'Stokes I'
    elif stokes_start == -1 and npol >= 2:
        mode, pol_label = 'RRLL', 'Stokes I'
    elif stokes_start == -1:
        mode, pol_label = 'single', 'RR'
    elif stokes_start == -2:
        mode, pol_label = 'single', 'LL'
    else:
        raise ValueError(f'Unsupported Stokes axis: starts at {stokes_start}, '
                         f'{npol} polarization(s)')

    if_freq = wuvdata.table('FQ', 0)[0]['if_freq']
    if isinstance(if_freq, float):  # Single IF
        if_freq = [if_freq]
    freq_scale = 1 + np.array(if_freq) / central_freq

    reals_list = []
    imags_list = []
    uvdists = []

    # Go through each record and compute IF-averaged visibilities
    for v in wuvdata:
        central_uv_dist = np.hypot(v.uvw[0], v.uvw[1])
        vis = np.asarray(v.visibility)   # shape (nIF, nchan, npol, 3)

        if mode == 'single':
            # Data already in I, or single-pol RR/LL: use the first Stokes entry
            reals = vis[:, :, 0, 0]
            imags = vis[:, :, 0, 1]
            weights = vis[:, :, 0, 2]
        else:
            w_rr = vis[:, :, 0, 2]
            w_ll = vis[:, :, 1, 2]
            reals = 0.5 * (vis[:, :, 0, 0] + vis[:, :, 1, 0])
            imags = 0.5 * (vis[:, :, 0, 1] + vis[:, :, 1, 1])
            # Var(I) = (Var_RR + Var_LL) / 4  ->  w_I = 4 w_RR w_LL / (w_RR + w_LL)
            # Only channels where both hands are unflagged are kept
            both_good = (w_rr > 0) & (w_ll > 0)
            with np.errstate(divide='ignore', invalid='ignore'):
                weights = np.where(both_good, 4 * w_rr * w_ll / (w_rr + w_ll), 0.)

        # Negative weights are flagged data in AIPS
        weights = np.where(weights > 0, weights, 0.)

        # Weighted average over channels, one value per IF
        wsum = weights.sum(axis=1)
        ok = wsum > 0
        reals_list.append((reals * weights).sum(axis=1)[ok] / wsum[ok])
        imags_list.append((imags * weights).sum(axis=1)[ok] / wsum[ok])
        uvdists.extend((central_uv_dist * freq_scale[ok] / 1e6).tolist())

    reals_array = np.concatenate(reals_list)
    imags_array = np.concatenate(imags_list)
    amps = np.hypot(reals_array, imags_array)
    phases = np.degrees(np.arctan2(imags_array, reals_array))
    if difmap_convention:
        phases = -phases

    radplot_fig, axes = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    radplot_fig.suptitle(f'{pol_label} Amp&Phase - UV Radius')

    # First subplot - Amplitudes vs. UV distances
    axes[0].scatter(uvdists, amps, marker='.', s=1, c='lime')
    axes[0].set_ylabel('Amplitude (Jy)')

    # Second subplot - Phases vs. UV distances
    axes[1].scatter(uvdists, phases, marker='.', s=1, c='lime')
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

    # Average the data per scan
    for bline in POSSM:
        if not isinstance(bline, tuple):
            continue
        avg_data = []
        for scan in POSSM[bline]:
            if len(scan) == 0:
                avg_data.append(scan)
                continue
            arr = np.array(scan)
            weighted_reals = arr[..., 0] * arr[..., 2]
            weighted_imags = arr[..., 1] * arr[..., 2]
            sum_weights = np.sum(arr[..., 2], axis=0)
            avg_reals = np.divide(np.sum(weighted_reals, axis=0), sum_weights, where=sum_weights!=0)
            avg_imags = np.divide(np.sum(weighted_imags, axis=0), sum_weights, where=sum_weights!=0)
            #avg_data.append(np.stack([avg_reals, avg_imags, sum_weights], axis=-1))

            # Replace flagged (weight=0) entries with NaN in reals and imags
            avg_reals_masked = np.where(sum_weights==0, np.nan, avg_reals)
            avg_imags_masked = np.where(sum_weights==0, np.nan, avg_imags)
            avg_data.append(np.stack([avg_reals_masked, avg_imags_masked, sum_weights], axis=-1))

        POSSM[bline] = avg_data

    POSSM['scans'] = scans
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
            np.savez(f'{path}/{name}_CL{wuvdata.seq}.possm.npz', **POSSM_str)

    if bp == True:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", category=np.VisibleDeprecationWarning)
            POSSM_str = {str(key): np.array(value, dtype=object) for key, value in POSSM.items()}
            np.savez(f'{path}/{name}_CL{wuvdata.seq}_BP.possm.npz', **POSSM_str)