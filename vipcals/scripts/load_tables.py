import os
import re
import glob
import requests 
import functools
print = functools.partial(print, flush=True)

import numpy as np

from concurrent.futures import ThreadPoolExecutor, as_completed

from datetime import datetime
from string import ascii_lowercase as alc 
from astropy.io import fits
from astropy.table import Table

from vipcals.scripts.helper import NoTablesError
from vipcals.scripts.helper import GC_entry

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

tmp_dir = os.path.expanduser("~/.vipcals/tmp")

# Check if /home/vipcals exists
if os.path.isdir("/home/vipcals"):
    tmp_dir = "/home/vipcals/.vipcals/tmp"

def load_evn_tables(data, load_flags=True):
    """Retrieve and load TY, GC and (optionally) FG tables from the EVN Archive.

    Tries <exp>.antab.gz, <exp>.antab, then <exp>_1, <exp>_2, ... with
    both extensions. Uses the unversioned file if present, otherwise the
    lowest-numbered version. If load_flags is True, the flag file
    (<exp>[_N].uvflg[.gz]) from the same version is loaded into FG#1.
    A missing flag file is not an error.

    :param data: visibility data
    :type data: AIPSUVData
    :param load_flags: retrieve and load the flag file into FG#1; defaults to True
    :type load_flags: bool, optional
    :return: URL of the antab file, URL of the flag file (None if not loaded) and
        URLs of all the antab files found in the archive
    :rtype: str, str or None, list of str
    """
    tmp = tmp_dir
    max_versions = 10

    obs = data.header.observer
    date = data.header.date_obs.replace('-', '')
    base = f"https://archive.jive.nl/exp/{obs}_{date[2:]}/pipe/{obs.lower()}"

    raw = f'{tmp}/tables.evn.download'

    def fetch(stem, exts, path):
        """Download the first existing stem+ext to path, decompressing if
        gzipped. Return the URL used, or None."""
        for ext in exts:
            url = stem + ext
            if os.path.exists(raw):
                os.remove(raw)
            status = os.system(f'curl -sf --retry 5 --retry-delay 10 '
                               f'-o {raw} {url}')
            if status != 0 or not os.path.exists(raw) \
                    or os.path.getsize(raw) == 0:
                continue

            # Decompress if gzipped, regardless of extension
            with open(raw, 'rb') as f:
                is_gzip = f.read(2) == b'\x1f\x8b'
            if is_gzip:
                os.system(f'zcat {raw} > {path}')
                os.remove(raw)
            else:
                os.replace(raw, path)
            return url

        if os.path.exists(raw):
            os.remove(raw)
        return None

    ## ANTAB FILE ##
    stems = [(None, base)] + [(i, f'{base}_{i}')
                              for i in range(1, max_versions + 1)]

    available = {}   # {version: (url, local_path)}
    for version, stem in stems:
        path = f'{tmp}/tables.evn' if version is None \
            else f'{tmp}/tables_{version}.evn'
        url = fetch(stem, ('.antab.gz', '.antab'), path)
        if url:
            available[version] = (url, path)
        elif version is not None:
            break    # stop at the first missing numbered version

    if not available:
        raise NoTablesError(f'No antab file found in the EVN archive for '
                            f'{obs} (tried {base}[_N].antab[.gz])')

    # Choose which file to use
    if None in available:
        chosen = None
    else:
        chosen = min(v for v in available if v is not None)
    evn_url, antab_path = available[chosen]

    # Remove any pre-existing tables
    if [1, 'AIPS TY'] in data.tables:
        data.zap_table('TY', 1)
    if [1, 'AIPS GC'] in data.tables:
        data.zap_table('GC', 1)

    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.tyver = 1
    antab.calin = antab_path
    antab.go()

    ## FLAG FILE (same version as the antab file) ##
    flag_url = None
    if load_flags:
        flag_stem = base if chosen is None else f'{base}_{chosen}'
        flag_path = f'{tmp}/flags.evn'
        flag_url = fetch(flag_stem, ('.uvflg.gz', '.uvflg'), flag_path)

        if flag_url is not None:
            uvflg = AIPSTask('uvflg')
            uvflg.inname = data.name
            uvflg.inclass = data.klass
            uvflg.indisk = data.disk
            uvflg.inseq = data.seq
            uvflg.intext = flag_path
            uvflg.outfgver = 1
            uvflg.go()

    return evn_url, flag_url, [u for u, _ in available.values()]

def load_evn_tables_old(data):
    """Retrieve and load TY and GC tables from the EVN Archive

    :param data: vibility data
    :type data: AIPSUVData
    """
    tmp = tmp_dir

    # Remove any pre-existing tables
    if ([1, 'AIPS TY'] in data.tables):
        data.zap_table('TY', 1)
    if ([1, 'AIPS GC'] in data.tables):
        data.zap_table('GC', 1)
    # Retrieve the EVN antab tables
    obs = data.header.observer
    date = data.header.date_obs.replace('-', '')
    evn_url = f"https://archive.jive.nl/exp/{obs}_{date[2:]}/pipe/{obs.lower()}.antab.gz"
    os.system('curl -sf --retry 5 --retry-delay 10 ' + evn_url \
                    + ' > ' + tmp + '/tables.evn.gz')  
    os.system('zcat ' + tmp + '/tables.evn.gz > ' + tmp + '/tables.evn')

    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.tyver = 1
    antab.calin = f'{tmp}/tables.evn'
    antab.go()

    return(evn_url) 

# Channel description lines of a Tsys block: Chan FE IF Pol BBC SB BBCFreq BW Freq Tcal
CHANNEL_LINE = re.compile(r'^!\s*(\d+)\s+\S+\s+\S+\s+([RL])CP\s+\d+\s+([UL])\s+'
                          r'[\d.]+MHz\s+([\d.]+)M\s+(-?[\d.]+)MHz')

def get_if_centres(data):
    """Get the central frequency of each IF of a dataset loaded in AIPS.

    :param data: visibility data
    :type data: AIPSUVData
    :return: central frequency of each IF in MHz, in the order they are loaded in AIPS
    :rtype: list of float
    """
    fq = data.table('FQ', 1)[0]
    if_freq = np.atleast_1d(fq['if_freq'])
    ch_width = np.atleast_1d(fq['ch_width'])
    total_bw = np.atleast_1d(fq['total_bandwidth'])
    ref_freq = data.header.crval[data.header.ctype.index('FREQ')]
    ref_pix = data.header.crpix[data.header.ctype.index('FREQ')]
    n_chan = np.round(total_bw / np.abs(ch_width))
    first_chan = ref_freq + if_freq - (ref_pix - 1) * ch_width
    return list((first_chan + (n_chan - 1) / 2 * ch_width) / 1e6)

def match_tsys_channels(channels, if_centres, pols):
    """Find the Tsys column of each IF and polarization of the dataset.

    The channel frequency is the central frequency in some cal.vlba files and the band
    edge in others, so both conventions are tried and the one that matches more IFs
    is kept. Columns are assigned in three passes: same frequency and polarization,
    then same frequency and any unused column (polarizations recorded as separate
    IFs), and finally any column at the same frequency (only one polarization
    measured).

    :param channels: (polarization, sideband, bandwidth in MHz, frequency in MHz) of
        each column, as listed in the Tsys block
    :type channels: list of tuple
    :param if_centres: central frequency in MHz of each loaded IF, in AIPS order
    :type if_centres: list of float
    :param pols: polarizations of the dataset, e.g. ['R', 'L']
    :type pols: list of str
    :return: column index for each IF and polarization (IF-major), None if not found
    :rtype: list of int or None
    """
    slots = [(f, p) for f in if_centres for p in pols]
    best = None
    for edge in [False, True]:
        centres = []
        for pol, sb, bw, freq in channels:
            if edge:
                centres.append(abs(freq) - bw/2 if sb == 'L' else abs(freq) + bw/2)
            else:
                centres.append(abs(freq))
        cols = [None] * len(slots)
        used = set()
        for same_pol, reuse in [(True, False), (False, False), (False, True)]:
            for i, (f, p) in enumerate(slots):
                if cols[i] is not None:
                    continue
                for n, c in enumerate(centres):
                    if abs(c - f) < channels[n][2]/4 and (reuse or n not in used) \
                       and (not same_pol or channels[n][0] == p):
                        cols[i] = n
                        used.add(n)
                        break
        if best is None or cols.count(None) < best.count(None):
            best = cols
    return best

def select_tsys_columns(lines, if_centres, pols):
    """Keep only the Tsys columns that correspond to the loaded IFs.

    The channels of each Tsys block are read from the '!  n  FE IF Pol ...' lines that
    precede the measurements and matched to the loaded IFs with
    :func:`~vipcals.scripts.load_tables.match_tsys_channels`. Columns are written in
    the order IF 1 pol 1, IF 1 pol 2, IF 2 pol 1, ... of the AIPS dataset. Lines where
    an IF cannot be matched (e.g. scans with a different frequency setup) are
    commented out.

    :param lines: lines of the Tsys section of the cal.vlba file
    :type lines: list of str
    :param if_centres: central frequency in MHz of each loaded IF, in AIPS order
    :type if_centres: list of float
    :param pols: polarizations of the dataset, e.g. ['R', 'L']
    :type pols: list of str
    :return: lines with only the selected Tsys columns
    :rtype: list of str
    """
    channels = []
    cols = None
    new_block = True
    out = []
    for item in lines:
        item = re.sub(r'([^\s/])/$', r'\1 /', item)
        match = CHANNEL_LINE.match(item)
        if match:
            if new_block:
                channels = []
                new_block = False
            channels.append((match.group(2), match.group(3), float(match.group(4)),
                             float(match.group(5))))
            cols = None
            out.append(item)
            continue
        new_block = True

        aux = item.split()
        if len(aux) == 0 or aux[0] in ['!', 'TSYS', '/', 'INDEX'] or len(channels) == 0:
            out.append(item)
            continue

        if cols is None:
            cols = match_tsys_channels(channels, if_centres, pols)

        values, _, comment = item.partition('!')
        values = values.split()
        if None in cols or max(cols) >= len(values) - 2:
            out.append('! ' + item)
            continue
        new = values[:2] + [values[2 + c] for c in cols]
        if comment.strip() != '':
            new += ['!', comment.strip()]
        out.append(' '.join(new))
    return out

def load_ty_tables(data):
    """Retrieve and load TY tables from an external server.

    Download TY data from an external repository, edit them in a suitable format, and 
    then load them into AIPS using the ANTAB task.
     
    The function can retrieve vlba.cal files produced by two different softwares: TSM 
    before October 2015, and RDBETSM after. The files are retrieved from 
    `http://www.vlba.nrao.edu/astro/VOBS/astronomy/ <VOBS>`_. The function uses 
    brute-force to look for any possible name of vlba.cal files from the same 
    project as the one in the data header. Then, the retrieved files are formatted 
    automatically and saved into /TABLES/tsys.vlba on the output directory. The required 
    IFs have to be given as an input, as usually they will come all together in the same 
    calibration file. For the files in TSM format, the function  
    :func:`~vipcals.scripts.load_tables.ty_tsm_vlog` uses the VLOG task in AIPS to split 
    the TY tables from the rest of the calibration tables. 

    .. _VOBS: http://www.vlba.nrao.edu/astro/VOBS/astronomy/

    :param data: visibility data
    :type data: AIPSUVData
    :return: urls from which the calibration tables have been retrieved
    :rtype: list of str
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    # Obtain cal.vlba file
    YY = int(data.header.date_obs[2:4])
    MM = int(data.header.date_obs[5:7])
    month_dict = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', \
                  6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', \
                  11: 'nov', 12: 'dec'}
    mmm = month_dict[MM]
    yy = str(YY)
    project = data.header.observer.lower()

    single_chars = list(alc) + list('123456789')
    combo_chars = [letter + number for letter in alc for number in '123456789']
    all_suffixes = single_chars + combo_chars
    
    # Weird exceptions:
    if project == 'bt022' and mmm == 'jul':
        project = 'bt22'
    if project == 'br005' and mmm == 'jul':
        project = 'br5'
    if project == 'bc016' and mmm == 'jun':
        project = 'bc16'
    
    normal = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project  #### + '[a-z]cal.vlba'
    
    normal_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba'
    compressed_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.Z'
    compressed_gz_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.gz'

    # If the file is splitted in different letters, we will keep them here
    letters = []
    
    # Here we store the urls from which the tables are retrieved
    retrieved_urls = []
    
    # try the new format
    
    for url in [normal_new, compressed_new, compressed_gz_new]:
        r = requests.head(url)
        if r.status_code != 404:
            good_url = url
            if '.Z' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.Z')
                os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables.vlba')
            elif '.gz' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.gz')
                os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables.vlba')
            else:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba')  
            retrieved_urls.append(good_url)
            break
    
    # try the old format... letter by letter

    if not glob.glob(tmp + '/tables*.vlba'):
        
        # CREATE A SESSION TO KEEP THE CONNECTION ALIVE
        session = requests.Session()
        
        # Define suffixes for multi-character checks
        single_chars = list(alc) + list('123456789')
        combo_chars = [letter + number for letter in alc for number in '123456789']
        
        # Include '' (empty string) to check the base file
        all_suffixes = [''] + single_chars + combo_chars

        # Define the 6 URL structures (Format Type, Extension)
        url_patterns = [
            (1, ''),
            (2, ''),
            (1, '.Z'),
            (2, '.Z'),
            (1, '.gz'),
            (2, '.gz')
        ]

        def check_url(url):
            """Probe URL existence."""
            try:
                r = session.head(url, timeout=5)
                if r.status_code != 404:
                    return url
            except requests.RequestException:
                pass
            return None

        # Iterate through the formats (Outer loop)
        for fmt, ext in url_patterns:
            found_tables = False

            # Build ALL candidate URLs for this format
            candidate_urls = []

            for s in all_suffixes:

                if fmt == 1:
                    url = normal + s + 'cal.vlba' + ext
                else:
                    url = (
                        'http://www.vlba.nrao.edu/astro/VOBS/astronomy/'
                        + mmm + yy + '/' + project + s + '/'
                        + project + s + 'cal.vlba' + ext
                    )

                candidate_urls.append((s, url))

            # CONCURRENT PROBING (MAX 16 THREADS)
            with ThreadPoolExecutor(max_workers = min(16, (os.cpu_count() or 4) * 2)) as executor:

                future_map = {
                    executor.submit(check_url, url): (s, url)
                    for s, url in candidate_urls
                }

                for future in as_completed(future_map):

                    result = future.result()

                    if result is None:
                        continue

                    s, url = future_map[future]
                    good_url = url

                    # Destination file
                    dest_file = f"{tmp}/tables{s}.vlba"

                    # Download exactly as before
                    if ext == '.Z':
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {tmp}/tables.vlba.Z'
                        )
                        os.system(
                            f'zcat {tmp}/tables.vlba.Z > {dest_file}'
                        )

                    elif ext == '.gz':
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {tmp}/tables.vlba.gz'
                        )
                        os.system(
                            f'zcat {tmp}/tables.vlba.gz > {dest_file}'
                        )

                    else:
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {dest_file}'
                        )

                    if s != '':
                        letters.append(s)

                    retrieved_urls.append(good_url)
                    found_tables = True

            # If we found files using this format pattern,
            # stop checking other formats
            if found_tables:
                break

        # Close the session
        session.close()

    # If the task did not succeed, raise an error and end the pipeline
    if not glob.glob(tmp + '/tables*.vlba'):
        raise NoTablesError("No vlba.cal tables were found online.")

    # Extract TSYS information from tables.vlba into tsys.vlba

    # If there are no letters:
    if len(letters) == 0:

        input_file = open(f"{tmp}/tables.vlba", "r") 
        cal_table = input_file.read() 
        cal_list = cal_table.split("\n")
        
        # If produced by TSM:
        if 'Produced by: TSM' in cal_list[0]:
        
            ty_tsm_vlog(data, [f"{tmp}/tables.vlba"])
                    
        # If produced by rdbetsm (from October 2015):
        if 'Produced by: rdbetsm ' in cal_list[0]:
            
            n_ant = len(data.table('AN', 1))
            for n, lines in enumerate(cal_list):
                if 'Tsys information' in lines:
                    start = n
                    break
                
            counter = 0
            for n, lines in enumerate(cal_list[start:]):
                if '! Produced by: ' in lines:
                    counter += 1
                if counter == n_ant:    
                    end = start+n-1
                    break
                end = start + n
            # Clean those * comments
            clean_list = cal_list[start:end]
            clean_list = [ elem for elem in clean_list if '*' not in elem]
            
            # If multi-if dataset:
            # Keep only the Tsys columns of the loaded IFs, matched by frequency
            final_list = select_tsys_columns(clean_list, get_if_centres(data),
                                             list(data.polarizations))
                
            
            with open(f'{tmp}/tsys.vlba', 'w') as fp:
                for item in final_list:
                    
                    # Im not sure of this part here... it was needed from 
                    # some old dataset but I dont know the implications
                    # Replace * with 0.0, is it safe?? 
                    if '*' in item:
                        item = item.replace('*', '0.0')
        
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
        if 'Produced by:' not in cal_list[0]:
            print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                  + ' UNRECOGNIZED FORMAT \n')           

              
    # If there are letters:
    else:
        for s in letters:
            input_file = open(tmp + "/tables" + s + ".vlba", "r") 
            cal_table = input_file.read() 
            cal_list = cal_table.split("\n")
            
            # If produced by TSM:
            if 'Produced by: TSM' in cal_list[0]:
                ty_tsm_vlog(data, glob.glob(f'{tmp}/tables*.vlba'))
                break
                        
            # If produced by rdbetsm (from October 2015):
            if 'Produced by: rdbetsm ' in cal_list[0]:
                
                n_ant = len(data.table('AN', 1))
                for n, lines in enumerate(cal_list):
                    if 'Tsys information' in lines:
                        start = n
                        break
                    
                counter = 0
                for n, lines in enumerate(cal_list[start:]):
                    if '! Produced by: ' in lines:
                        counter += 1
                    if counter == n_ant:    
                        end = start+n-1
                        break
                    end = start + n
                # Clean those * comments
                clean_list = cal_list[start:end]
                clean_list = [ elem for elem in clean_list if '*' not in elem]
                
                
                # Keep only the Tsys columns of the loaded IFs, matched by frequency
                final_list = select_tsys_columns(clean_list, get_if_centres(data),
                                             list(data.polarizations))
                    
                
                with open(f'{tmp}/tsys.vlba', 'a') as fp:
                    for item in final_list:
                        
                        # Im not sure of this part here... it was needed from 
                        # some old dataset but I dont know the implications
                        # Replace * with 0.0, is it safe?? 
                        if '*' in item:
                            item = item.replace('*', '0.0')
            
                        # write each item on a new line
                        fp.write("%s\n" % item)
                        
            if 'Produced by:' not in cal_list[0]:
                print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                      + ' UNRECOGNIZED FORMAT \n')
            
    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.tyver = 1
    antab.calin = f'{tmp}/tsys.vlba'

    # Ignore antennas not in the observation
    tsys_ants = []
    with open(f'{tmp}/tsys.vlba', 'r') as f:
        lines = f.readlines()
        for l in lines:
            if 'Tsys information' in l: 
                tsys_ants.append(l.split(' ')[-2])
    ignore_ants = list(set([x for x in tsys_ants 
                            if x not in [a.strip() for a in data.antennas]]))

    antab.sparm = AIPSList(ignore_ants)

    antab.go()

    return(retrieved_urls)    

def old_load_ty_tables(data, bif, eif):
    """Retrieve and load TY tables from an external server.

    Download TY data from an external repository, edit them in a suitable format, and 
    then load them into AIPS using the ANTAB task.
     
    The function can retrieve vlba.cal files produced by two different softwares: TSM 
    before October 2015, and RDBETSM after. The files are retrieved from 
    `http://www.vlba.nrao.edu/astro/VOBS/astronomy/ <VOBS>`_. The function uses 
    brute-force to look for any possible name of vlba.cal files from the same 
    project as the one in the data header. Then, the retrieved files are formatted 
    automatically and saved into /TABLES/tsys.vlba on the output directory. The required 
    IFs have to be given as an input, as usually they will come all together in the same 
    calibration file. For the files in TSM format, the function  
    :func:`~vipcals.scripts.load_tables.ty_tsm_vlog` uses the VLOG task in AIPS to split 
    the TY tables from the rest of the calibration tables. 

    .. _VOBS: http://www.vlba.nrao.edu/astro/VOBS/astronomy/

    :param data: visibility data
    :type data: AIPSUVData
    :param bif: first frequency IF to consider 
    :type bif: int
    :param eif: last frequency IF to consider
    :type eif: int
    :return: urls from which the calibration tables have been retrieved
    :rtype: list of str
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    # Obtain cal.vlba file
    YY = int(data.header.date_obs[2:4])
    MM = int(data.header.date_obs[5:7])
    month_dict = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', \
                  6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', \
                  11: 'nov', 12: 'dec'}
    mmm = month_dict[MM]
    yy = str(YY)
    project = data.header.observer.lower()
    
    # Weird exceptions:
    if project == 'bt022' and mmm == 'jul':
        project = 'bt22'
    if project == 'br005' and mmm == 'jul':
        project = 'br5'
    if project == 'bc016' and mmm == 'jun':
        project = 'bc16'
    
    normal = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project  #### + '[a-z]cal.vlba'
    
    normal_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba'
    compressed_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.Z'
    compressed_gz_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.gz'

    # If the file is splitted in different letters, we will keep them here
    letters = []
    
    # Here we store the urls from which the tables are retrieved
    retrieved_urls = []
    
    # try the new format
    
    for url in [normal_new, compressed_new, compressed_gz_new]:
        r = requests.get(url)
        if r.status_code != 404:
            good_url = url
            if '.Z' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.Z')
                os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables.vlba')
            elif '.gz' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.gz')
                os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables.vlba')
            else:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba')  
            retrieved_urls.append(good_url)
            break
    
    # try the old format... letter by letter
    
    if not glob.glob(tmp + '/tables*.vlba'):
        for i in range(1):
            # no letter
            url = normal + 'cal.vlba'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba')  
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.Z'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.Z')  
                os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables.vlba')
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.gz'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.gz')  
                os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables.vlba')
                retrieved_urls.append(good_url)
                break

            # Try all letters
            for s in alc + '123456789':
                url = normal + s +'cal.vlba'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables' + s + '.vlba') 
                    letters.append(s)
                    retrieved_urls.append(good_url)
            
            # Break the loop if it already found some tables
            if len(letters) != 0:
                break
                  
            # try all letters
            for s in alc + '123456789':
                url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
                + mmm + yy + '/' + project + s + '/' + project + s + 'cal.vlba'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables' + s + '.vlba') 
                    letters.append(s)
                    retrieved_urls.append(good_url)
            
            # Break the loop if it already found some tables
            if len(letters) != 0:
                break
            
            for s in alc + '123456789':
                url = normal + s +'cal.vlba.Z'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables.vlba.Z')  
                    os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)
                    
            # Break the loop if it already found some tables
            if len(letters) != 0:
                break
            
            for s in alc + '123456789':
                url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
                + mmm + yy + '/' + project + s + '/' + project + s + 'cal.vlba.Z'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables.vlba.Z')  
                    os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)
                    
            # Break the loop if it already found some tables
            if len(letters) != 0:
                break
            
            for s in alc + '123456789':
                url = normal + s +'cal.vlba.gz'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables.vlba.gz')  
                    os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)

            # Break the loop if it already found some tables
            if len(letters) != 0:
                break

            for s in alc + '123456789':
                url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
                    + mmm + yy + '/' + project + s + '/' + project + s + 'cal.vlba.gz'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                              + ' > ' + tmp + '/tables.vlba.gz')  
                    os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)
         
    # If the task did not succeed, raise an error and end the pipeline
    if not glob.glob(tmp + '/tables*.vlba'):
        raise NoTablesError("No vlba.cal tables were found online.")

    # Extract TSYS information from tables.vlba into tsys.vlba

    # If there are no letters:
    if len(letters) == 0:

        input_file = open(f"{tmp}/tables.vlba", "r") 
        cal_table = input_file.read() 
        cal_list = cal_table.split("\n")
        
        # If produced by TSM:
        if 'Produced by: TSM' in cal_list[0]:
        
            ty_tsm_vlog(data, bif, eif, [f"{tmp}/tables.vlba"])
                    
        # If produced by rdbetsm (from October 2015):
        if 'Produced by: rdbetsm ' in cal_list[0]:
            
            n_ant = len(data.table('AN', 1))
            for n, lines in enumerate(cal_list):
                if 'Tsys information' in lines:
                    start = n
                    break
                
            counter = 0
            for n, lines in enumerate(cal_list[start:]):
                if '! Produced by: ' in lines:
                    counter += 1
                if counter == n_ant:    
                    end = start+n-1
                    break
                end = start + n
            # Clean those * comments
            clean_list = cal_list[start:end]
            clean_list = [ elem for elem in clean_list if '*' not in elem]
            
            # If multi-if dataset:
            if bif == 0 and eif != 0:
                final_list = clean_list
                
            if bif == 0 and eif == 0:
                final_list = clean_list
            
            if bif == 1 and eif != 0:
                final_list = []
                for item in clean_list:
                    if len(item.split()) > 0:
                        if item.split()[0] in ['!', 'TSYS','/']:
                            final_list.append(item)
                            continue
                        aux = item.split()
                        del aux[2+eif:]
                        aux2 = ' '.join(aux)
                        final_list.append(aux2)
            if bif != 1 and eif != 0:
                final_list = []
                for item in clean_list:
                    if len(item.split()) > 0:
                        if item.split()[0] in ['!', 'TSYS','/']:
                            final_list.append(item)
                            continue
                        aux = item.split()
                        del aux[2:bif+1]
                        aux2 = ' '.join(aux)
                        final_list.append(aux2)
                
            
            with open(f'{tmp}/tsys.vlba', 'w') as fp:
                for item in final_list:
                    
                    # Im not sure of this part here... it was needed from 
                    # some old dataset but I dont know the implications
                    # Replace * with 0.0, is it safe?? 
                    if '*' in item:
                        item = item.replace('*', '0.0')
        
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
        if 'Produced by:' not in cal_list[0]:
            print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                  + ' UNRECOGNIZED FORMAT \n')           

              
    # If there are letters:
    else:
        for s in letters:
            input_file = open(tmp + "/tables" + s + ".vlba", "r") 
            cal_table = input_file.read() 
            cal_list = cal_table.split("\n")
            
            # If produced by TSM:
            if 'Produced by: TSM' in cal_list[0]:
                ty_tsm_vlog(data, bif, eif, glob.glob(f'{tmp}/tables*.vlba'))
                break
                        
            # If produced by rdbetsm (from October 2015):
            if 'Produced by: rdbetsm ' in cal_list[0]:
                
                n_ant = len(data.table('AN', 1))
                for n, lines in enumerate(cal_list):
                    if 'Tsys information' in lines:
                        start = n
                        break
                    
                counter = 0
                for n, lines in enumerate(cal_list[start:]):
                    if '! Produced by: ' in lines:
                        counter += 1
                    if counter == n_ant:    
                        end = start+n-1
                        break
                    end = start + n
                # Clean those * comments
                clean_list = cal_list[start:end]
                clean_list = [ elem for elem in clean_list if '*' not in elem]
                
                
                if bif == 0 and eif != 0:
                    final_list = clean_list
                    
                if bif == 0 and eif == 0:
                    final_list = clean_list
                
                if bif == 1 and eif != 0:
                    final_list = []
                    for item in clean_list:
                        if len(item.split()) > 0:
                            if item.split()[0] in ['!', 'TSYS','/']:
                                final_list.append(item)
                                continue
                            aux = item.split()
                            del aux[2+eif:]
                            aux2 = ' '.join(aux)
                            final_list.append(aux2)
                if bif != 1 and eif != 0:
                    final_list = []
                    for item in clean_list:
                        if len(item.split()) > 0:
                            if item.split()[0] in ['!', 'TSYS','/']:
                                final_list.append(item)
                                continue
                            aux = item.split()
                            del aux[2:bif+1]
                            aux2 = ' '.join(aux)
                            final_list.append(aux2)
                    
                
                with open(f'{tmp}/tsys.vlba', 'a') as fp:
                    for item in final_list:
                        
                        # Im not sure of this part here... it was needed from 
                        # some old dataset but I dont know the implications
                        # Replace * with 0.0, is it safe?? 
                        if '*' in item:
                            item = item.replace('*', '0.0')
            
                        # write each item on a new line
                        fp.write("%s\n" % item)
                        
            if 'Produced by:' not in cal_list[0]:
                print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                      + ' UNRECOGNIZED FORMAT \n')
            
    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.tyver = 1
    antab.calin = f'{tmp}/tsys.vlba'

    # Ignore antennas not in the observation
    tsys_ants = []
    with open(f'{tmp}/tsys.vlba', 'r') as f:
        lines = f.readlines()
        for l in lines:
            if 'Tsys information' in l: 
                tsys_ants.append(l.split(' ')[-2])
    ignore_ants = list(set([x for x in tsys_ants 
                            if x not in [a.strip() for a in data.antennas]]))

    antab.sparm = AIPSList(ignore_ants)

    antab.go()

    return(retrieved_urls)    
    
def load_fg_tables(data):
    """Retrieve and load FG tables from an external server.

    Download FG data from an external repository, edit them in a suitable format, and 
    then load them into AIPS using the UVFLG task.
     
    The function can retrieve vlba.cal files produced by two different softwares: TSM 
    before October 2015, and RDBETSM after. The files are retrieved from 
    `http://www.vlba.nrao.edu/astro/VOBS/astronomy/ <VOBS>`_. The function uses 
    brute-force to look for any possible name of vlba.cal files from the same 
    project as the one in the data header. Then, the retrieved files are formatted 
    automatically and saved into /TABLES/flags.vlba on the output directory. For the 
    files in TSM format, the function :func:`~vipcals.scripts.load_tables.fg_tsm_vlog` 
    uses the VLOG task in AIPS to split the TY tables from the rest of the calibration 
    tables. 

    .. _VOBS: http://www.vlba.nrao.edu/astro/VOBS/astronomy/    

    :param data: visibility data
    :type data: AIPSUVData
    :return: urls from which the calibration tables have been retrieved
    :rtype: list of str
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    # Obtain cal.vlba file
    YY = int(data.header.date_obs[2:4])
    MM = int(data.header.date_obs[5:7])
    month_dict = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', \
                  6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', \
                  11: 'nov', 12: 'dec'}
    mmm = month_dict[MM]
    yy = str(YY)
    project = data.header.observer.lower()

    single_chars = list(alc) + list('123456789')
    combo_chars = [letter + number for letter in alc for number in '123456789']
    all_suffixes = single_chars + combo_chars
    
    # Weird exceptions:
    if project == 'bt022' and mmm == 'jul':
        project = 'bt22'
    if project == 'br005' and mmm == 'jul':
        project = 'br5'
    if project == 'bc016' and mmm == 'jun':
        project = 'bc16'
    
    normal = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project  #### + '[a-z]cal.vlba'
    
    normal_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba'
    compressed_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.Z'
    compressed_gz_new = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/' \
             + mmm + yy + '/' + project + '/' + project + 'cal.vlba.gz'

    # If the file is splitted in different letters, we will keep them here
    letters = []
    
    # Here we store the urls from which the tables are retrieved
    retrieved_urls = []
    
    # try the new format
    
    for url in [normal_new, compressed_new, compressed_gz_new]:
        r = requests.head(url)
        if r.status_code != 404:
            good_url = url
            if '.Z' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.Z')
                os.system('zcat ' + tmp + '/tables.vlba.Z > ' + tmp + '/tables.vlba')
            elif '.gz' in url:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba.gz')
                os.system('zcat ' + tmp + '/tables.vlba.gz > ' + tmp + '/tables.vlba')
            else:
                os.system('curl -sf --retry 5 --retry-delay 10 ' + url \
                          + ' > ' + tmp + '/tables.vlba')  
            retrieved_urls.append(good_url)
            break
    
    # try the old format... letter by letter

    if not glob.glob(tmp + '/tables*.vlba'):
        
        # CREATE A SESSION TO KEEP THE CONNECTION ALIVE
        session = requests.Session()
        
        # Define suffixes for multi-character checks
        single_chars = list(alc) + list('123456789')
        combo_chars = [letter + number for letter in alc for number in '123456789']
        
        # Include '' (empty string) to check the base file
        all_suffixes = [''] + single_chars + combo_chars

        # Define the 6 URL structures (Format Type, Extension)
        url_patterns = [
            (1, ''),
            (2, ''),
            (1, '.Z'),
            (2, '.Z'),
            (1, '.gz'),
            (2, '.gz')
        ]

        def check_url(url):
            """Probe URL existence."""
            try:
                r = session.head(url, timeout=5)
                if r.status_code != 404:
                    return url
            except requests.RequestException:
                pass
            return None

        # Iterate through the formats (Outer loop)
        for fmt, ext in url_patterns:
            found_tables = False

            # Build ALL candidate URLs for this format
            candidate_urls = []

            for s in all_suffixes:

                if fmt == 1:
                    url = normal + s + 'cal.vlba' + ext
                else:
                    url = (
                        'http://www.vlba.nrao.edu/astro/VOBS/astronomy/'
                        + mmm + yy + '/' + project + s + '/'
                        + project + s + 'cal.vlba' + ext
                    )

                candidate_urls.append((s, url))

            # CONCURRENT PROBING (MAX 16 THREADS)
            with ThreadPoolExecutor(max_workers = min(16, (os.cpu_count() or 2) * 2)) as executor:

                future_map = {
                    executor.submit(check_url, url): (s, url)
                    for s, url in candidate_urls
                }

                for future in as_completed(future_map):

                    result = future.result()

                    if result is None:
                        continue

                    s, url = future_map[future]
                    good_url = url

                    # Destination file
                    dest_file = f"{tmp}/tables{s}.vlba"

                    # Download exactly as before
                    if ext == '.Z':
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {tmp}/tables.vlba.Z'
                        )
                        os.system(
                            f'zcat {tmp}/tables.vlba.Z > {dest_file}'
                        )

                    elif ext == '.gz':
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {tmp}/tables.vlba.gz'
                        )
                        os.system(
                            f'zcat {tmp}/tables.vlba.gz > {dest_file}'
                        )

                    else:
                        os.system(
                            f'curl -sf --retry 5 --retry-delay 10 '
                            f'{url} > {dest_file}'
                        )

                    if s != '':
                        letters.append(s)

                    retrieved_urls.append(good_url)
                    found_tables = True

            # If we found files using this format pattern,
            # stop checking other formats
            if found_tables:
                break

        # Close the session
        session.close()

    # If the task did not succeed, raise an error and end the pipeline
    if not glob.glob(tmp + '/tables*.vlba'):
        raise NoTablesError("No vlba.cal tables were found online.")
            
    # Extract FG information from tables.vlba into flags.vlba
    
    # If there are no letters:
    if len(letters) == 0:
        
        input_file = open(f"{tmp}/tables.vlba", "r") 
        cal_table = input_file.read() 
        cal_list = cal_table.split("\n")
        
        # If produced by TSM:
        if 'Produced by: TSM' in cal_list[0]:
            fg_tsm_vlog(data, [f"{tmp}/tables.vlba"])
                    
        # If produced by rdbetsm (from October 2015):
        if 'Produced by: rdbetsm ' in cal_list[0]:
            for n, lines in enumerate(cal_list):
                if 'Edit data' in lines:
                    start = n
                    break
    
            for n, lines in enumerate(cal_list[start:]):
                if '! Produced by: ' in lines:   
                    end = start+n
                    break
                end = start + n
                
            # Clean those * comments
            clean_list = cal_list[start:end]
            clean_list = [ elem for elem in clean_list if '*' not in elem]
            
            with open(f'{tmp}/flags.vlba', 'w') as fp:
                for item in clean_list[start:end]:
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
        if 'Produced by:' not in cal_list[0]:
            print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                  + ' UNRECOGNIZED FORMAT \n')
                
        
    # If there are letters:
    else:
        for s in letters:
            input_file = open(f"{tmp}/tables{s}.vlba", "r") 
            cal_table = input_file.read() 
            cal_list = cal_table.split("\n")
         
            # If produced by TSM:
            if 'Produced by: TSM' in cal_list[0]:
                fg_tsm_vlog(data, glob.glob(f'{tmp}/tables*.vlba'))
                     
            # If produced by rdbetsm (from October 2015):
            if 'Produced by: rdbetsm ' in cal_list[0]:
                for n, lines in enumerate(cal_list):
                    if 'Edit data' in lines:
                        start = n
                        break
     
                for n, lines in enumerate(cal_list[start:]):
                    if '! Produced by: ' in lines:   
                        end = start+n
                        break
                    end = start + n
                 
                # Clean those * comments
                clean_list = cal_list[start:end]
                clean_list = [ elem for elem in clean_list if '*' not in elem]
             
                with open(f'{tmp}/flags.vlba', 'a') as fp:
                    for item in clean_list[start:end]:
                        # write each item on a new line
                        fp.write("%s\n" % item)
                     
            if 'Produced by:' not in cal_list[0]:
                print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                      + ' UNRECOGNIZED FORMAT \n')

         
    # Run UVFLG
    uvflg = AIPSTask('uvflg')
    uvflg.inname = data.name
    uvflg.inclass = data.klass
    uvflg.indisk = data.disk
    uvflg.inseq = data.seq
    uvflg.intext = f'{tmp}/flags.vlba'
    
    uvflg.go()

    return(retrieved_urls)

def load_gc_tables(data, ant_list = ['all']):
    """Retrieve and load GC tables from an external file.

    Look for relevant gain curves from an external file, edit them in a suitable format, 
    and then load them into AIPS using the ANTAB task. It gets the curves from a master 
    file, and selects the ones corresponding to the time range of the observation.

    Final gain curve table is saved as /TABLES/gaincurves.vlba on the output directory.

    :param data: visibility data
    :type data: AIPSUVData
    :param log: pipeline log
    :type log: file
    """
    here = os.path.dirname(__file__)
    tmp = tmp_dir

    # Read data
    good_url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/vlba_gains.key'
    inputfile = open(os.path.dirname(__file__) + 
                     "/../catalogues/vlba_gains.key", "r") 
    readfile = inputfile.read() 
    # Split into list
    input_list = readfile.split("\n\n")
    # Edit the list
    gc_list = []
    for i, entry in enumerate(input_list):
        input_list[i] = entry.split('\n')
    input_list.pop(0)
    input_list.pop(0)
    input_list[0].remove('')
    # Extract relevant info from the file
    for block in input_list:
        if '! Where no measurements are available, values are from the '\
            + 'master gains file.' in block:
            block.remove('! Where no measurements are available, values '\
                         + 'are from the master gains file.')
        a = GC_entry()
        a.initime = block[1].split()[5]
        a.finaltime = block[1].split()[6]
        a.initime = datetime(int(a.initime[:4]),int(a.initime[5:7]),\
                             int(a.initime[8:10]))
        a.finaltime = datetime(int(a.finaltime[:4]),int(a.finaltime[5:7]),\
                               int(a.finaltime[8:10]))
        a.band = block[1].split()[2]
        a.antenna = block[4].split()[0] 
        a.entry = block[4]
        gc_list.append(a)
    # Read information from our dataset
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])
    date_obs = datetime(YYYY, MM, DD)
    
    #try:
    if ant_list == ["all"]:
        antennas = data.antennas
    else:
        antennas = ant_list
    
    # Handmade... hope it is accurate
    restfreq = data.header['crval'][2]/1e6
    if restfreq < 450:
        databand = "'90cm'"
    if restfreq > 450 and restfreq < 850:
        databand = "'50cm'"
    if restfreq > 850 and restfreq < 1550:
        databand = "'21cm'"
    if restfreq > 1550 and restfreq < 1900:
        databand = "'18cm'"
    if restfreq > 1900 and restfreq < 3500:
        databand = "'13cmsx'"
    if restfreq > 3500 and restfreq < 5500:
        databand = "'6cm'"
    if restfreq > 5500 and restfreq < 8000:
        databand = "'7ghz'"
    if restfreq > 8000 and restfreq < 11000:
        databand = "'4cmsx'"
    if restfreq > 11000 and restfreq < 18000:
        databand = "'2cm'"
    if restfreq > 18000 and restfreq < 22900:
        databand = "'1cm'"
    if restfreq > 22900 and restfreq < 26000:
        databand = "'24ghz'"
    if restfreq > 26000 and restfreq < 50000:
        databand = "'7mm'"
    if restfreq > 50000 and restfreq < 95000:
        databand = "'3mm'"
        
    # Look for the appropiate entries in the gc_list
    gain_curves = []
    for gc in gc_list:
        if (gc.antenna in antennas) and (gc.band == databand) \
            and (gc.initime < date_obs) and (gc.finaltime > date_obs):
            gain_curves.append(gc.entry)
            
    if len(gain_curves) == 0:
        # It would be ideal if it could just take the gain curve from the 
        # closest date, or even interpolate between two dates.
        raise NoTablesError('No gain curves available for the observation date.')
            
    with open(f'{tmp}/gaincurves.vlba', 'w') as fp:
        for item in gain_curves:
            # write each item on a new line
            fp.write("%s\n" % item)
            
    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.calin = f'{tmp}/gaincurves.vlba'
    antab.gcver = 1
    
    antab.go()

def load_external_antab(data, filepath):
    """Load amplitude calibration information from an external file

    Load Tsys and gain curve information from an external file. This information has to
    be on an ANTAB format readable by AIPS

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath: path to an ANTAB file
    :type filepath: str
    """

    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.calin = f'{filepath}'
    antab.tyver = 1
    antab.gcver = 1
    
    antab.go()

def load_external_flags(data, filepath):
    """Load flags from an external file with UVFLG.

    The file has to be a text file readable by UVFLG (see EXPLAIN UVFLG in AIPS).
    Flags are written into FG#1, which is created if it does not exist.

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath: path to a UVFLG flag file
    :type filepath: str
    """
    # Copy the file to the tmp directory, AIPS does not accept long file names
    tmp = tmp_dir
    os.system(f'cp "{filepath}" {tmp}/flags_user.vlba')

    uvflg = AIPSTask('uvflg')
    uvflg.inname = data.name
    uvflg.inclass = data.klass
    uvflg.indisk = data.disk
    uvflg.inseq = data.seq
    uvflg.intext = f'{tmp}/flags_user.vlba'
    uvflg.outfgver = 1
    uvflg.go()

    os.system(f'rm {tmp}/flags_user.vlba')

def remove_ascii_antname(data, filepath):
    """Remove non-ASCII characters from antenna names.

    Recovers the antenna names from the uvifts/idifits files, then runs the TABED \
    task to edit the AN table in AIPS.

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath: path to the original uvfits/idifits file
    :type filepath: str
    """    
    # Recover antenna names from fits file
    backup_names = []
    hdul = fits.open(filepath)
    non_ascii_antennas = list(Table(hdul['ANTENNA'].data)['ANNAME'])
    for ant in non_ascii_antennas:
        ant = re.sub(r'[^\x20-\x7E]', '', ant).strip()
        backup_names.append(ant)
    hdul.close()
        
    for i in range(len(data.table('AN',1))):
        # Replace antenna names row by row
        tabed_antname = AIPSTask('TABED')
        tabed_antname.inname = data.name
        tabed_antname.inclass = data.klass
        tabed_antname.indisk = data.disk
        tabed_antname.inseq = data.seq
        tabed_antname.inext = 'AN'
        tabed_antname.invers = 1
        
        tabed_antname.outname = data.name
        tabed_antname.outclass = data.klass
        tabed_antname.outdisk = data.disk
        tabed_antname.outseq = data.seq
        tabed_antname.outvers = 1
        
        tabed_antname.optype = 'REPL'
        tabed_antname.aparm[1] = 1  # Column number (Sure is always this?)
        tabed_antname.aparm[2] = 0  # 1st character to modify (0 => 1)
        tabed_antname.aparm[3] = 0  # Last character to modify (0 => last)
        tabed_antname.aparm[4] = 3  # String
        
        tabed_antname.bcount = i+1  # 1st row to modify
        tabed_antname.ecount = i+1  # Last row to modify
        
        tabed_antname.keystrng = AIPSList(backup_names[i]) # Antenna name
        
        tabed_antname.go()
    
def remove_ascii_poltype(data, filepath):
    """Remove non-ASCII characters from polarization types.

    Recovers the polarization labels from the uvifts/idifits files, then runs the TABED 
    task to edit the AN table in AIPS.

    :param data: visibility data
    :type data: AIPSUVData
    :param filepath: path to the original uvfits/idifits file
    :type filepath: str
    """
    # Recover polarization labels from fits file
    backup_names = []
    hdul = fits.open(filepath)
    poltya = list(Table(hdul['ANTENNA'].data)['POLTYA'])
    poltyb = list(Table(hdul['ANTENNA'].data)['POLTYB'])
    for n, ant in enumerate(poltya):
        pol = re.sub(r'[^\x20-\x7E]', '', poltya[n]).strip() \
            + re.sub(r'[^\x20-\x7E]', '', poltyb[n]).strip()
        backup_names.append(pol)
    hdul.close()

    for i in range(len(data.table('AN',1))):
        # Replace polarization type row by row
        tabed_poltype = AIPSTask('TABED')
        tabed_poltype.inname = data.name
        tabed_poltype.inclass = data.klass
        tabed_poltype.indisk = data.disk
        tabed_poltype.inseq = data.seq
        tabed_poltype.inext = 'AN'
        tabed_poltype.invers = 1
        
        tabed_poltype.outname = data.name
        tabed_poltype.outclass = data.klass
        tabed_poltype.outdisk = data.disk
        tabed_poltype.outseq = data.seq
        tabed_poltype.outvers = 1
        
        tabed_poltype.optype = 'REPL'
        tabed_poltype.aparm[1] = 9  # Column number (Sure it's always this?)
        tabed_poltype.aparm[2] = 0  # 1st character to modify (0 => 1)
        tabed_poltype.aparm[3] = 0  # Last character to modify (0 => last)
        tabed_poltype.aparm[4] = 3  # String
        
        tabed_poltype.bcount = i+1  # 1st row to modify
        tabed_poltype.ecount = i+1  # Last row to modify
        
        tabed_poltype.keystrng = AIPSList(backup_names[i])  # Replace value

        tabed_poltype.go()

def ty_tsm_vlog(data, table_paths):
    """Split tsys tables from a TSM produced cal.vlba file.

    Uses the VLOG task in AIPS to separate the system temperature information from one 
    or multiple cal.vlba files in the TSM format. The output is written onto 
    ./vipcals/tmp/tsys.vlba

    :param data: visibility data
    :type data: AIPSUVData
    :param table_paths: list of paths where the calibration tables have been downloaded
    :type table_pahts: list of str
    """ 
    here = os.path.dirname(__file__)
    tmp = tmp_dir
    for path in table_paths:
        vlog = AIPSTask('VLOG')
        vlog.inname = data.name
        vlog.inclass = data.klass
        vlog.inseq = data.seq
        vlog.indisk = data.disk

        vlog.calin = path
        vlog.outfile = path[:-5]

        vlog.go()

    for path in table_paths:
        with open(f'{tmp}/tsys.vlba', 'a') as f:
            f.write(open(path[:-5]+'.TSYS', 'r').read())

    tsys_file = open(f"{tmp}/tsys.vlba", "r")
    tsys_list = tsys_file.read().split('\n')

    # Keep only the Tsys columns of the loaded IFs, matched by frequency
    final_list = select_tsys_columns(tsys_list, get_if_centres(data),
                                     list(data.polarizations))

    # Make sure that the INDEX are coherent with the number of Tsys entries,
    # comment it out if not, and add a "/" line below it
    corrected_list = []
    for i, item in enumerate(final_list):
        if item.startswith('INDEX'):
            # Find the next valid data line to determine how many Tsys entries exist
            num_tsys = 0
            for j in range(i + 1, len(final_list)):
                next_item = final_list[j]
                if len(next_item.strip()) == 0: 
                    continue
                first_word = next_item.split()[0]
                if first_word not in ['!', 'TSYS', '/', 'INDEX']:
                    # Extract just the data portion before the '!' comment
                    data_part = next_item.split('!')[0]
                    # Subtract 2 because the first two columns are DAY and TIME
                    num_tsys = max(0, len(data_part.split()) - 2)
                    break
            
            # Parse the current INDEX line
            prefix, rest = item.split('=', 1)
            if '/' in rest:
                content = rest.rsplit('/', 1)[0]
            else:
                content = rest
                
            # Extract the fields
            fields = [f.strip() for f in content.split(',')]
            fields = [f for f in fields if f] 
            
            # If the lengths do not match, comment out and add the '/' line
            if len(fields) != num_tsys:
                corrected_list.append("! " + item)
                corrected_list.append("/")
                continue  # Skip the default append below since we just handled it
            
        corrected_list.append(item)
        
    final_list = corrected_list


    date = datetime.strptime(data.header.date_obs, "%Y-%m-%d")
    dayno = date.timetuple().tm_yday

    with open(f'{tmp}/tsys.vlba', 'w') as fp:
        for item in final_list:
            # Replace the offset with 0.0 
            if '*' in item:
                item = item.replace('*', '0.0')
            if len(item) > 0 and item.split()[0] not in ['!', 'TSYS','/', 'INDEX']:
                if float(item.split()[0]) > dayno+3 or float(item.split()[0]) < dayno-3:
                    continue
            # write each item on a new line
            fp.write("%s\n" % item)

def fg_tsm_vlog(data, table_paths):
    """Split flag tables from a TSM produced cal.vlba file.

    Uses the VLOG task in AIPS to separate the flag information from one or multiple 
    cal.vlba files in the TSM format. The output is written onto /.vipcals/tmp/flags.vlba

    :param data: visibility data
    :type data: AIPSUVData
    :param table_paths: list of paths where the calibration tables have been downloaded
    :type table_pahts: list of str
    """    
    here = os.path.dirname(__file__)
    tmp = tmp_dir
    for path in table_paths:
        vlog = AIPSTask('VLOG')
        vlog.inname = data.name
        vlog.inclass = data.klass
        vlog.inseq = data.seq
        vlog.indisk = data.disk

        vlog.calin = path
        vlog.outfile = path[:-5]

        vlog.go()

    for path in table_paths:
        with open(f'{tmp}/flags.vlba', 'a') as f:
            f.write(open(path[:-5]+'.FLAG', 'r').read())