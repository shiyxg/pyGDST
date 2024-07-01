import obspy as ob
from obspy.core.trace import Stats
from obspy.core.utcdatetime import UTCDateTime
from obspy import Stream, Trace

import numpy as np
import h5py
from glob import glob
import tqdm
from .gdst import read_bin, read_header

NETWORK = 'GDST'

def header2csv():
    pass

def write_sac(file_names:str) -> any:
    pass

def merge_sac(file_names:str) -> any:
    pass

def create_sac_1h_CZ(data:np.array, name:str,dt:float, time_s:str,  NET=NETWORK)->ob.Trace:
    
    stats = Stats()
    stats.network = NET
    stats.station = name
    stats.station = 'Z'

    y = int(time_s[0:2])+2000
    m = int(time_s[2:4])
    d = int(time_s[4:6])
    h = int(time_s[6:8])


    stats.starttime = UTCDateTime(year=y,month=m,day=d,hour=h)
    # print(stats.starttime)

    stats.sampling_rate = 1/dt
    stats.npts = int(3600/dt)

    assert stats.npts/stats.sampling_rate==3600

    trace = ob.Trace(data, header=stats)

    return trace

def bin2sac(bin_file:str,sac_file:str, time_s:str, dt:float,name:str, NET=NETWORK) -> any:
    '''
    binary file to sac (1h)

    bin_file: file name of binary
    sac_file: file name of sac file
    time_s  : start time of the bin_file
    dt      : sampling rate (s)
    
    name    : station name
    NET     : network name
    '''

    H, data, hs = read_bin(bin_file, dt=dt/1000)

    trace = create_sac_1h_CZ(data, name,dt, time_s,  NET=NETWORK)

    trace.write(sac_file)

def bins2sac(bins_file:list,sac_file:str, dt:float,name:str, DOWNSAMPLE_RATE=1, NET=NETWORK,PATH_MARKER='/') -> any:
    '''
    merge binary files to a sac

    bin_file        : file names of binary, list[str], eg: [./P320LINE/A0000102/24052808.BIN]
    sac_file        : file name of sac file
    dt              : sampling rate (s)
    DOWNSAMPLE_RATE : 降采样比例
    
    name    : station name
    NET     : network name
    PATH_MARKER: 路径分割符号
    '''
    bins_file.sort()
    
    traces=[]
    for i, file in enumerate(bins_file):

        t_string = file.split(PATH_MARKER)[-1]
        t_s =  t_string[0:8]

        H, data, hs = read_bin(file, dt=dt*1000)
        # print(t_s,data.shape)
        trace = create_sac_1h_CZ(data, name,dt, t_s,  NET=NETWORK)
        traces.append(trace)

    stream = ob.Stream(traces)
    # print('1h',stream[0].data.shape)
    stream = stream.merge(fill_value=0)
    # print('after merge',stream[0].data.shape)

    if DOWNSAMPLE_RATE>1:
        
        stream = stream.decimate(factor=DOWNSAMPLE_RATE)
        # print('after DW',stream[0].data.shape)
    stream.write(sac_file)

def bins2h5(bins_file:list, h5_name, dt=0.002, PATH_MARKER='/') -> any:
    '''
    把所有文件转成h5格式

    bins_file: 文件名
    file_name: h5文件名
    dt       : 采样率
    PATH_MARKER: 路径分割符号

    '''
    bins_file.sort()

    headers = []
    data = []
    t_all = []
    for file in tqdm.tqdm(bins_file):
    # for file in files:
        t_string = file.split(PATH_MARKER)[-1]
        y = int(t_string[0:2])
        m = int(t_string[2:4])
        d = int(t_string[4:6])
        h = int(t_string[6:8])
        t_s =  int(t_string[0:8])

        f_header, data_i, _ = read_bin(file, dt=dt*1000)
        
        headers.append(f_header)
        data.append(data_i)
        t_all.append(t_s)
    headers = np.array(headers)
    data = np.array(data)
    t_all = np.array(t_all)
    print(f'write {headers.shape[0]} files to {h5_name}')
    with h5py.File(h5_name,'w') as f:
        f.create_dataset('data', data=data)
        f.create_dataset('headers', data=headers)
        f.create_dataset('Times',data=t_all)
        f.create_dataset('dt',data=dt)
        f.create_dataset('NF',data=len(data))
        f.create_dataset('raw_files',data=np.array(bins_file, dtype='S'))

        





