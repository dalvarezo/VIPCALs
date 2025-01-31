import numpy as np
import os

from datetime import datetime
import requests #### NEED TO BE INSTALLED W SUDO PIP INSTALL REQUESTS ####
from string import ascii_lowercase as alc # lowercase alphabet

from astropy.io import fits
from astropy.table import Table

from AIPS import AIPS
from AIPSTask import AIPSTask, AIPSList


class gc_entry():
    """Entries from the master gain curve (vlba_gains.key)"""
    def __init__(self):
        self.initime = None
        self.finaltime = None
        self.band = None
        self.antenna = None
        self.entry = None


def time_aver(data, oldtime, newtime):
    """Average visibility data in time

    Creates a new entry in AIPS adding '_AT' to the name

    :param data: visibility data
    :type data: AIPSUVData
    :param oldtime: previous time resolution in seconds
    :type oldtime: float
    :param newtime: new time resolution in seconds
    :type newtime: float
    """    
    uvavg = AIPSTask('uvavg')
    uvavg.inname = data.name
    uvavg.inclass = data.klass
    uvavg.indisk = data.disk
    uvavg.inseq = data.seq

    uvavg.doacor = 1
    uvavg.yinc = newtime
    uvavg.zinc = oldtime
    uvavg.opcode = 'TIME'
    
    uvavg.outname = data.name[:9] + '_TA'
    uvavg.outclass = data.klass
    uvavg.outdisk = data.disk
    uvavg.outseq = data.seq
    uvavg.msgkill = -4
    
    uvavg.go()
    
def freq_aver(data, ratio):
    """Average visibility data in frequency

    Creates a new entry in AIPS adding '_AF' or '_ATF' to the name if it has 
    already been averaged in time.

    :param data: visibility data
    :type data: AIPSUVData
    :param ratio: ratio between the old number of frequency channels and the new one, \
    e.g. when going from 64 channels to 16, this number is 4 
    :type ratio: float # maybe int?
    """    
    avspc = AIPSTask('avspc')
    avspc.inname = data.name
    avspc.inclass = data.klass
    avspc.indisk = data.disk
    avspc.inseq = data.seq

    avspc.doacor = 1
    avspc.channel = ratio
    avspc.avoption = 'SUBS'

    if data.name[-3:] == '_AT':
        avspc.outname = data.name[-4:] + '_ATF'
    else:
        avspc.outname = data.name[:9] + '_AF'
    avspc.outclass = data.klass
    avspc.outdisk = data.disk
    avspc.outseq = data.seq
    avspc.msgkill = -4

    avspc.go()

def run_indxr(data):
    """Creates an index (NX) table and indexes the uv data file.

    Also creates CL#1 with entries every 0.1 minutes.

    :param data: visibility data
    :type data: AIPSUVData
    """    
    indxr = AIPSTask('indxr')
    indxr.inname = data.name
    indxr.inclass = data.klass
    indxr.indisk = data.disk
    indxr.inseq = data.seq
    
    indxr.cparm[3] = 0.1  # Create CL#1
    indxr.cparm[4] = 1    # Recalculate CL entry group delays using IM table
    indxr.msgkill = -4
    
    indxr.go()
    
def load_ty_tables(data, bif, eif):
    """Retrieve and load TY tables from an external server.

    Download TY data from an external repository, edit it in a suitable format, and then \
    load it into AIPS using ANTAB. Calibration files are produced by two softwares, \
    tsm before Oct15 and rdbetsm after.

    Final system temperature table is stored as 'tsys.vlba'

    A MORE EXTENSIVE DOCSTRING IS NEEDED.

    :param data: visibility data
    :type data: AIPSUVData
    :param bif: first frequency IF to consider 
    :type bif: int
    :param eif: last frequency IF to consider
    :type eif: end
    :return: urls from which the calibration tables have been retrieved
    :rtype: list of str
    """    
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
                os.system('curl -f ' + url + ' > ./tables.vlba.Z')
                os.system('zcat ./tables.vlba.Z > ./tables.vlba')
            if '.gz' in url:
                os.system('curl -f ' + url + ' > ./tables.vlba.gz')
                os.system('zcat ./tables.vlba.gz > ./tables.vlba')
            else:
                os.system('curl -f ' + url + ' > ./tables.vlba')  
            retrieved_urls.append(good_url)
    
    # try the old format... letter by letter
    
    if os.path.exists('./tables.vlba') == False:
        for i in range(1):
            # no letter
            url = normal + 'cal.vlba'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba')  
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.Z'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba.Z')  
                os.system('zcat ./tables.vlba.Z > ./tables.vlba')
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.gz'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba.gz')  
                os.system('zcat ./tables.vlba.gz > ./tables.vlba')
                retrieved_urls.append(good_url)
                break
                  
            # try all letters
            for s in alc:
                url = normal + s +'cal.vlba'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -f ' + url + ' > ./tables' + s + '.vlba') 
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
                    os.system('curl -f ' + url + ' > ./tables.vlba.Z')  
                    os.system('zcat ./tables.vlba.Z > ./tables' + s +'.vlba')
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
                    os.system('curl -f ' + url + ' > ./tables.vlba.gz')  
                    os.system('zcat ./tables.vlba.gz > ./tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)
        
    # Extract TSYS information from tables.vlba into tsys.vlba

    # If there are no letters:
    if len(letters) == 0:

        input_file = open("tables.vlba", "r") 
        cal_table = input_file.read() 
        cal_list = cal_table.split("\n")
        
        # If produced by TSM:
        if 'Produced by: TSM' in cal_list[0]:
        
            for n, lines in enumerate(cal_list):
                if 'Tsys information' in lines:
                    start = n
                    break
            for n, lines in enumerate(cal_list[start:]):
                if '! For antenna(s): ' in lines:
                    end = start+n-1
                    break
                end = n
                
            clean_list = cal_list[start:end]
            
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
                
            
            with open(r'./tsys.vlba', 'w') as fp:
                for item in final_list:
                    
                    # Im not sure of this part here... it was needed from 
                    # some old dataset but I dont know the implications
                    # Replace * with 0.0, is it safe?? 
                    if '*' in item:
                        item = item.replace('*', '0.0')
        
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
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
                
            
            with open(r'./tsys.vlba', 'w') as fp:
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
            input_file = open("tables" + s + ".vlba", "r") 
            cal_table = input_file.read() 
            cal_list = cal_table.split("\n")
            
            # If produced by TSM:
            if 'Produced by: TSM' in cal_list[0]:
            
                for n, lines in enumerate(cal_list):
                    if 'Tsys information' in lines:
                        start = n
                        break
                for n, lines in enumerate(cal_list[start:]):
                    if '! For antenna(s): ' in lines:
                        end = start+n-1
                        break
                    end = n
                    

                clean_list = cal_list[start:end]
                
                
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
                    
                
                with open(r'./tsys.vlba', 'a') as fp:
                    for item in final_list:
                        
                        # Im not sure of this part here... it was needed from 
                        # some old dataset but I dont know the implications
                        # Replace * with 0.0, is it safe?? 
                        if '*' in item:
                            item = item.replace('*', '0.0')
            
                        # write each item on a new line
                        fp.write("%s\n" % item)
                        
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
                    
                
                with open(r'./tsys.vlba', 'a') as fp:
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
    antab.calin = './tsys.vlba'
    # We might need to add SELBAND and SELFREQ here...
    antab.msgkill = -4
    
    antab.go()

    return(retrieved_urls)    
    
def load_fg_tables(data):
    """Retrieve and load FG tables from an external server.

    Download FG data from an external repository, edit it in a suitable format, and then \
    load it into AIPS using UVFLG. Calibration files are produced by two softwares, \
    tsm before Oct15 and rdbetsm after.

    Final flag table is stored as 'flags.vlba'

    A MORE EXTENSIVE DOCSTRING IS NEEDED.

    :param data: visibility data
    :type data: AIPSUVData
    :return: urls from which the calibration tables have been retrieved
    :rtype: list of str
    """    
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
                os.system('curl -f ' + url + ' > ./tables.vlba.Z')
                os.system('zcat ./tables.vlba.Z > ./tables.vlba')
            if '.gz' in url:
                os.system('curl -f ' + url + ' > ./tables.vlba.gz')
                os.system('zcat ./tables.vlba.gz > ./tables.vlba')
            else:
                os.system('curl -f ' + url + ' > ./tables.vlba')             
            retrieved_urls.append(good_url)
        
    if os.path.exists('./tables.vlba') == False:
        # try the old format... letter by letter
        for i in range(1):
            # no letter
            url = normal + 'cal.vlba'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba')  
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.Z'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba.Z')  
                os.system('zcat ./tables.vlba.Z > ./tables.vlba')
                retrieved_urls.append(good_url)
                break
            url = normal + 'cal.vlba.gz'
            r = requests.get(url)
            if r.status_code != 404:
                good_url = url
                os.system('curl -f ' + url + ' > ./tables.vlba.gz')  
                os.system('zcat ./tables.vlba.gz > ./tables.vlba')
                retrieved_urls.append(good_url)
                break
                  
            # try all letters
            for s in alc:
                url = normal + s +'cal.vlba'
                r = requests.get(url)
                if r.status_code != 404:
                    good_url = url
                    os.system('curl -f ' + url + ' > ./tables' + s + '.vlba') 
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
                    os.system('curl -f ' + url + ' > ./tables.vlba.Z')  
                    os.system('zcat ./tables.vlba.Z > ./tables' + s +'.vlba')
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
                    os.system('curl -f ' + url + ' > ./tables.vlba.gz')  
                    os.system('zcat ./tables.vlba.gz > ./tables' + s +'.vlba')
                    letters.append(s)
                    retrieved_urls.append(good_url)
        
            
    # Extract FG information from tables.vlba into flags.vlba
    
    
    # If there are no letters:
    if len(letters) == 0:
        
        input_file = open("tables.vlba", "r") 
        cal_table = input_file.read() 
        cal_list = cal_table.split("\n")
        
        # If produced by TSM:
        if 'Produced by: TSM' in cal_list[0]:
            for n, lines in enumerate(cal_list):
                if 'Edit data' in lines:
                    start = n
                    break
            for n, lines in enumerate(cal_list[start:]):
                if '! For antenna(s): ' in lines:
                    end = start+n-1
                    break
                end = n
            with open(r'./flags.vlba', 'w') as fp:
                for item in cal_list[start:end]:
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
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
            
            with open(r'./flags.vlba', 'w') as fp:
                for item in clean_list[start:end]:
                    # write each item on a new line
                    fp.write("%s\n" % item)
                    
        if 'Produced by:' not in cal_list[0]:
            print('\n\n ERROR WHILE READING THE CAL.VLBA FILE,' \
                  + ' UNRECOGNIZED FORMAT \n')
                
        
    # If there are letters:
    else:
        for s in letters:
            input_file = open("tables" + s + ".vlba", "r") 
            cal_table = input_file.read() 
            cal_list = cal_table.split("\n")
         
            # If produced by TSM:
            if 'Produced by: TSM' in cal_list[0]:
                for n, lines in enumerate(cal_list):
                    if 'Edit data' in lines:
                        start = n
                        break
                for n, lines in enumerate(cal_list[start:]):
                    if '! For antenna(s): ' in lines:
                        end = start+n-1
                        break
                    end = n
                with open(r'./flags.vlba', 'a') as fp:
                    for item in cal_list[start:end]:
                        # write each item on a new line
                        fp.write("%s\n" % item)
                     
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
             
                with open(r'./flags.vlba', 'a') as fp:
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
    uvflg.intext = './flags.vlba'
    # We might need to add SELBAND and SELFREQ here...
    uvflg.msgkill = -4
    
    uvflg.go()

    return(retrieved_urls)

def load_gc_tables(data): # , bk_antennas):
    """Retrieve and load GC tables from an external file.

    Look for relevant gain curves from an external file, edit them in a suitable format, \
    and then load it into AIPS using ANTAB. 

    Final gain curve table is stored as 'gaincurves.vlba'
    
    A MORE EXTENSIVE DOCSTRING IS NEEDED.

    :param data: visibility data
    :type data: AIPSUVData
    :param log: pipeline log
    :type log: file
    """
    # Read data
    good_url = 'http://www.vlba.nrao.edu/astro/VOBS/astronomy/vlba_gains.key'
    inputfile = open("./catalogues/vlba_gains.key", "r") 
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
        a = gc_entry()
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
    # I NEED TO COMMENT THIS PART A BIT BETTER
    # Read information from our dataset
    YYYY = int(data.header.date_obs[:4])
    MM = int(data.header.date_obs[5:7])
    DD = int(data.header.date_obs[8:])
    date_obs = datetime(YYYY, MM, DD)
    
    #try:
    antennas = data.antennas
    # except SystemError:
    #     antennas = AIPSList(bk_antennas)   
    
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
        return 404
            
    with open(r'./gaincurves.vlba', 'w') as fp:
        for item in gain_curves:
            # write each item on a new line
            fp.write("%s\n" % item)
            
    # Run ANTAB
    antab = AIPSTask('antab')
    antab.inname = data.name
    antab.inclass = data.klass
    antab.indisk = data.disk
    antab.inseq = data.seq
    antab.calin = './gaincurves.vlba'
    # We might need to add SELBAND and SELFREQ here...
    antab.msgkill = -4
    
    antab.go()
    return 0
    
def tborder(data, log):
    """Sort data in Time - Baseline order (TB)

    :param data: visibility data
    :type data: AIPSUVData
    """    
    
    uvsrt = AIPSTask('uvsrt')
    uvsrt.inname = data.name
    uvsrt.inclass = data.klass
    uvsrt.indisk = data.disk
    uvsrt.inseq = data.seq
    uvsrt.outname = data.name
    uvsrt.outclass = data.klass
    uvsrt.outdisk = data.disk
    uvsrt.outseq = data.seq
    
    uvsrt.sort = 'TB'
    uvsrt.msgkill = -4
        
    uvsrt.go()

def remove_ascii_antname(data,filepath):
    """Remove non-ASCII characters from antenna names.

    Recovers the antenna names from the uvifts/idifits files, then runs the TABED \
    task to edit the AN table in AIPS

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
        ant = ant.encode()[:2].decode()
        backup_names.append(ant)
        
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
        
        tabed_antname.msgkill = -4
        tabed_antname.go()
    
def remove_ascii_poltype(data, value = ''):
    """Remove non-ASCII characters from polarization types.

    Uses TABED to modify the antenna table. WARNING: it effectively empties the \
    polarization field, which might not always be desirable.

    :param data: visibility data
    :type data: AIPSUVData
    :param value: polarization type, defaults to ''
    :type value: str, optional
    """    """ """
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
        
        tabed_poltype.keystrng = AIPSList(value)  # Replace value
        
        tabed_poltype.msgkill = -4
        tabed_poltype.go()