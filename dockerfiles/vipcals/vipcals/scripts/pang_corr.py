from AIPSTask import AIPSTask

AIPSTask.msgkill = -8

def pang_corr(data):
    """Correct phases for parallactic angles.
    
    Runs the CLCOR task in AIPS to the data.
    Creates CL#4

    :param data: visibility data
    :type data: AIPSUVData
    """     
    clcor = AIPSTask('clcor')
    clcor.inname = data.name
    clcor.inclass = data.klass
    clcor.indisk = data.disk
    clcor.inseq = data.seq
    clcor.opcode = 'PANG'
    clcor.clcorprm[1] = 1 # add corrections, remove them if < 0
    
    clcor.go()