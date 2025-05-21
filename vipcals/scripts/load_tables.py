import os
import re
import glob
import requests 
import functools
print = functools.partial(print, flush=True)

from datetime import datetime
from string import ascii_lowercase as alc 
from astropy.io import fits
from astropy.table import Table

from scripts.helper import NoTablesError
from scripts.helper import GC_entry

from AIPSTask import AIPSTask, AIPSList
AIPSTask.msgkill = -8

def load_ty_tables(data, bif, eif):
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
    tmp = os.path.abspath(os.path.join(here, "../../tmp"))

    # Obtain cal.vlba file
    YY = int(data.header.date_obs[2:4])
    MM = int(data.header.date_obs[5:7])
    month_dict = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', \
                  6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', \
                  11: 'nov', 12: 'dec'}
    mmm = month_dict[MM]
    yy = str(YY)
    project = data.header.observer.lower()
    
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
            for s in alc:
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
            for s in alc:
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
            
            for s in alc:
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
            
            for s in alc:
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
            
            for s in alc:
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

            for s in alc:
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
    antab.calin = f'{tmp}/tsys.vlba'

    # Ignore antennas not in the observation
    tsys_ants = []
    with open('/home/dalvarez/vipcals/tmp/tsys.vlba', 'r') as f:
        lines = f.readlines()
        for l in lines:
            if 'Tsys information' in l: 
                tsys_ants.append(l.split(' ')[-2])
    ignore_ants = [x for x in tsys_ants if x not in [a.strip() for a in data.antennas]]

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
    tmp = os.path.abspath(os.path.join(here, "../../tmp"))

    # Obtain cal.vlba file
    YY = int(data.header.date_obs[2:4])
    MM = int(data.header.date_obs[5:7])
    month_dict = {1: 'jan', 2: 'feb', 3: 'mar', 4: 'apr', 5: 'may', \
                  6: 'jun', 7: 'jul', 8: 'aug', 9: 'sep', 10: 'oct', \
                  11: 'nov', 12: 'dec'}
    mmm = month_dict[MM]
    yy = str(YY)
    project = data.header.observer.lower()
    
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
            for s in alc:
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
            for s in alc:
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
            
            for s in alc:
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
            
            for s in alc:
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
            
            for s in alc:
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

            for s in alc:
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
    tmp = os.path.abspath(os.path.join(here, "../../tmp"))

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

def ty_tsm_vlog(data, bif, eif, table_paths):
    """Split tsys tables from a TSM produced cal.vlba file.

    Uses the VLOG task in AIPS to separate the system temperature information from one 
    or multiple cal.vlba files in the TSM format. The output is written onto 
    /vipcals/tmp/tsys.vlba

    :param data: visibility data
    :type data: AIPSUVData
    :param bif: first frequency IF to consider 
    :type bif: int
    :param eif: last frequency IF to consider
    :type eif: int
    :param table_paths: list of paths where the calibration tables have been downloaded
    :type table_pahts: list of str
    """ 
    here = os.path.dirname(__file__)
    tmp = os.path.abspath(os.path.join(here, "../../tmp"))
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
    # If multi-if dataset:
    if bif == 0 and eif != 0:
        final_list = tsys_list
        
    if bif == 0 and eif == 0:
        final_list = tsys_list
    
    if bif == 1 and eif != 0:
        final_list = []
        for item in tsys_list:
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
        for item in tsys_list:
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
            # Replace the offset with 0.0 
            if '*' in item:
                item = item.replace('*', '0.0')
            # write each item on a new line
            fp.write("%s\n" % item)

def fg_tsm_vlog(data, table_paths):
    """Split flag tables from a TSM produced cal.vlba file.

    Uses the VLOG task in AIPS to separate the flag information from one or multiple 
    cal.vlba files in the TSM format. The output is written onto /vipcals/tmp/flags.vlba

    :param data: visibility data
    :type data: AIPSUVData
    :param table_paths: list of paths where the calibration tables have been downloaded
    :type table_pahts: list of str
    """    
    here = os.path.dirname(__file__)
    tmp = os.path.abspath(os.path.join(here, "../../tmp"))
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