import obspy as ob
from obspy.core.trace import Stats
from obspy.core.utcdatetime import UTCDateTime
from obspy import Stream, Trace

import numpy as np
import h5py
from glob import glob
import tqdm
from scipy import signal
import os

from .gdst import read_bin
from .gdst import  bheader_decode
from .paras import DATA_SIZE,CHN_DEF

NETWORK = 'GDST'
PATH_SEP = os.path.sep


def bheader2list(header, start=0, interval=60) -> list:

    '''
    把block_header 中的data中的有效信息转换出来,默认输出一个list of
    (date_UTC,time_UTC, lat, lon, seq1, seq2)

    header: np.array(int32), 2D
    start : 开始的数据块 
    interval : 数据块间隔， 默认60个

    out: a list of (date_UTC,time_UTC, lat, lon, seq1, seq2)
    '''

    ns,nh = header.shape
    inf_list = []
    for i in range(start, ns, interval):
        date_UTC,time_UTC, lat, lon, seq1, seq2 = bheader_decode(header[i,:])

        inf_list.append([date_UTC,time_UTC, lat, lon, seq1, seq2])

    return inf_list

def bheader_list2csv(inf_list:list, file_name:str,M=',',REMOVE_ZERO=False, date=None):
    '''
    把block_header 转换出的list保存为csv
    "date_UTC,time_UTC,lat,lon,seq1,seq2,"
    ...,...,...,...

    inf_list: list of information
    file_name: 文件名
    M: , for csv
    REMOVE_ZERO: 去除授时中的点
    date: 控制头文件不输出上一次采样结果
    '''

    lines = []
    lines.append( 'date_UTC,time_UTC,lat,lon,seq1,seq2,\n')
    for date_UTC, time_UTC, lat, lon, seq1, seq2 in inf_list:

        if REMOVE_ZERO and (lat==0 or lon==0):
            continue
        
        if date is not None and date_UTC!=date:
            continue

        line_i = f'{date_UTC:06d}{M}{time_UTC:06d}{M}{lat:>2.7f}{M}{lon:>3.7f}{M}{seq1}{M}{seq2}{M}'
    
        lines.append(line_i+'\n')

    f = open(file_name,'w')
    f.writelines(lines)
    f.close()
    
    return 1

def bheader2csv(header, file_name, start=0, interval=60, REMOVE_ZERO=False):
    '''
    把block_header 转换为csv

    header: np.array(int32), 2D
    file_name: csv 文件名
    '''
    inf_lines = bheader2list(header, start=start, interval=interval)
    return bheader_list2csv(inf_lines, file_name,M=',',REMOVE_ZERO=REMOVE_ZERO)
    

def create_sac_1h_1C(data:np.array, name:str,dt:float, time_s:str,  NET=NETWORK, CHN='Z')->ob.Trace:
    
    stats = Stats()
    stats.network = NET
    stats.station = name
    stats.channel = CHN

    y = int(time_s[0:2])+2000
    m = int(time_s[2:4])
    d = int(time_s[4:6])
    h = int(time_s[6:8])


    stats.starttime = UTCDateTime(year=y,month=m,day=d,hour=h)
    # print(stats.starttime)

    stats.delta = dt
    stats.npts = int(3600/dt)

    assert stats.npts*stats.delta==3600

    trace = ob.Trace(data, header=stats)

    return trace

def bin2sac(bin_file:str,sac_file:str, time_s:str, dt:float,name:str, NET=NETWORK) -> any:
    '''
    binary file to sac (1h)

    bin_file: file name of binary
    sac_file: file name of sac file[s], use '{CHN}' as placeholder for 3C/4C sensor
    time_s  : start time of the bin_file
    dt      : sampling rate (s)
    
    name    : station name
    NET     : network name
    '''

    H, data, hs = read_bin(bin_file, dt=dt/1000)

    if data.shape[0]==1 and '{CHN}' not in sac_file:
        trace = create_sac_1h_1C(data, name,dt, time_s,  NET=NETWORK,CHN='Z')
        trace.write(sac_file)

    else:

        nc = data.shape[0]
        chn_names = CHN_DEF[nc]
        for i, chn_i in enumerate(chn_names):
            trace = create_sac_1h_1C(data[i,:], name,dt, time_s,  NET=NETWORK,CHN=chn_i)
            sac_file_i = sac_file.format(CHN=chn_i)
            trace.write(sac_file_i)
        

def bins2sac_Z(bins_file:list,sac_file:str, dt:float,name:str, DOWNSAMPLE_RATE=1, NET=NETWORK,PATH_MARKER='/') -> any:
    '''
    merge binary files to a sac, 单通道 Z

    bin_file        : file names of binary, list[str], eg: [./P320LINE/A0000102/24052808.BIN]
    sac_file        : file name of sac file
    dt              : sampling rate (s)
    name            : station name

    DOWNSAMPLE_RATE : 降采样比例

    NET     : network name
    PATH_MARKER: 路径分割符号
    '''
    bins_file.sort()
    
    traces=[]
    for i, file in enumerate(bins_file):

        t_string = file.split(PATH_MARKER)[-1]
        t_s =  t_string[0:8]

        H, data, hs = read_bin(file, dt=dt*1000,IS_Z_CHN=True)
        # print(t_s,data.shape)
        trace = create_sac_1h_1C(data, name,dt, t_s,  NET=NETWORK, CHN='Z')
        traces.append(trace)

    stream = ob.Stream(traces)
    # print('1h',stream[0].data.shape)
    stream = stream.merge(fill_value=0)
    # print('after merge',stream[0].data.shape)

    if DOWNSAMPLE_RATE>1:
        
        stream = stream.decimate(factor=DOWNSAMPLE_RATE)
        # print('after DW',stream[0].data.shape)
    stream.write(sac_file)

def bins2sac(bins_file:list,sac_file:str,dt:float,name:str,
             DB=0,N_CHN=1, DOWNSAMPLE_RATE=1, NET=NETWORK,PATH_MARKER='/',
             header_file=None) -> any:
    '''
    merge binary files to a sac, 多通道

    bin_file        : file names of binary, list[str], eg: [./P320LINE/A0000102/24052808.BIN]
    sac_file        : sac文件名, use '{CHN}' as placeholder for 3C/4C sensor
    dt              : sampling rate (s)
    name            : station name

    DB              : 增益
    N_CHN           : 通道数, num of CHN
    DOWNSAMPLE_RATE : 降采样比例
    
    NET     : network name
    PATH_MARKER: 路径分割符号
    '''
    bins_file.sort()
    
    if N_CHN>1:
        assert '{CHN}' in sac_file
    if N_CHN==1 and '{CHN}' in sac_file:
        sac_file = sac_file.format(CHN='Z')
    
    
    traces    = [[]]*N_CHN
    chn_names = CHN_DEF[N_CHN]

    header_list = []
    NT_amin   =  int(60/dt)

    for i, file in enumerate(bins_file):

        t_string = file.split(PATH_MARKER)[-1]
        t_s =  t_string[0:8]

        H, data, hs = read_bin(file, dt=dt*1000,IS_Z_CHN=False, DB=DB)
        # print(t_s,data.shape)
        assert data.shape[0]==N_CHN
        # print(data.max())
        #头文件
        inf_lines = bheader2list(hs[0,:,:], start=0, interval=int(60/dt/DATA_SIZE))
        header_list+=inf_lines

        #健康度
        health_i = np.ones([1,60,1])
        health_i[0,:,0] = (np.array(inf_lines)[:,0]==int(t_s[:6]))
        data = data.reshape([N_CHN, 60,NT_amin])*health_i
        data = data.reshape([N_CHN,-1])
        # print(data.max())
        for j in range(N_CHN):
            data_ij = data[j,:]
            trace = create_sac_1h_1C(data_ij.flatten(), name,dt, t_s,  NET=NETWORK, CHN=chn_names[j])
            traces[j].append(trace)

    # 写头文件
    if header_file is not None:
        bheader_list2csv(header_list,header_file, REMOVE_ZERO=False, date=None)

    for i in range(N_CHN):
        stream = ob.Stream(traces[i])
        # print('1h',stream[0].data.shape)
        stream = stream.merge(fill_value=0)
        # print('after merge',stream[0].data.shape)

        if DOWNSAMPLE_RATE>1:
            
            stream = stream.decimate(factor=DOWNSAMPLE_RATE)
            # print('after DW',stream[0].data.shape)
        
        if N_CHN>1:
            sac_file_i = sac_file.format(CHN=chn_names[i])
        else:
            sac_file_i = sac_file

        stream.write(sac_file_i)


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

    nh, nc, nt = data.shape
    
    print(f'write {headers.shape[0]} files to {h5_name}')
    with h5py.File(h5_name,'w') as f:
        f.create_dataset('data', data=data)
        f.create_dataset('headers', data=headers)
        f.create_dataset('Times',data=t_all)
        f.create_dataset('dt',data=dt)
        f.create_dataset('N_hours',data=nh)
        f.create_dataset('chns',data=CHN_DEF[nc])
        f.create_dataset('raw_files',data=np.array(bins_file, dtype='S'))


def bins2h5_day(ROOT_folder, h5_name,date, header_file_pattern='./{date}_{name}.csv',
                N_CHN=1, DB=0,
                dt=0.002, PATH_MARKER=PATH_SEP, DOWNSAMPLE_RATE=5, 
                sn2name={}) -> any:
    '''
    把所有台站同一天的文件转成一个统一格式的,大H5文件

    ROOT_folder: 原始文件根目录
    h5_name    : 生成的h5文件名
    date       : 指定日期
    header_file_pattern: 头文件信息的写入位置， eg: 'path/{date}_{name}.csv'
    
    N_CHN      : 通道数
    DB         : 增益率
    dt         : 采样间隔, 单位s， 
    DOWNSAMPLE_RATE：降采样率， 整数
    PATH_MARKER: 路径分割符号
    sn2name    : 仪器号转名称
    '''
    if len(sn2name.keys())==0: 
        sns = os.listdir(f"{ROOT_folder}/")
    else:
        sns = sn2name.keys()


    hours=[f'{i:02d}' for i in range(24)]

    NT_aday   =  int(3600*24/dt)
    NT_ahour  =  int(3600/dt)
    NT_amin   =  int(60/dt)
    NT_aday_DW = int(3600*24/dt/DOWNSAMPLE_RATE)
    # print(NT_aday,NT_ahour,NT_aday_DW)

    h5file = h5py.File(h5_name,'w')

    h5file.create_group('data')
    # t = np.arange(NT_aday_DW)*dt*DOWNSAMPLE_RATE/1000
    # print(t, len(t))
    h5file.create_dataset('nt', data=NT_aday_DW)
    h5file.create_dataset('dt', data=dt*DOWNSAMPLE_RATE)
    h5file.create_dataset('ns', data=len(sns))

    names = []
    health = np.ones([len(sns),len(hours)*60], dtype='float32')
    for i, sn_i in enumerate(sns):
        path_sn = f"{ROOT_folder}/{sn_i}"
        sn_i = path_sn.split(PATH_SEP)[-1]
        if sn_i in sn2name.keys():
            name_i = sn2name[sn_i]
        else:
            name_i = sn_i

        data_day = np.zeros([N_CHN, NT_aday],dtype='float32')
        health_i = np.ones(len(hours)*60, dtype='float32')

        # 读数据
        header_list = []
        for j, hour in enumerate(hours):

            file_ij = f'{path_sn}/{date}{hour}.BIN'
            if not os.path.exists(file_ij):
                health_i[j*60:(j+1)*60]=0
                continue

            H, data_ij, hs = read_bin(file_ij, dt=dt*1000,IS_Z_CHN=False, DB=DB)
            # print(t_s,data.shape)
            assert data_ij.shape[0]==N_CHN

            # 头文件每分钟采样
            inf_lines = bheader2list(hs[0,:,:], start=0, interval=int(60/dt/DATA_SIZE))
            header_list+=inf_lines

            # 为分钟值的健康度赋值
            health_i[j*60:(j+1)*60] = (np.array(inf_lines)[:,0]==int(date))

            # 不健康采样置零
            data_ij = data_ij.reshape([N_CHN, 60,NT_amin])*health_i[j*60:(j+1)*60].reshape([1,60,1])
            # print(data_ij.shape)

            sp = j*NT_ahour
            ep = (j+1)*NT_ahour

            data_day[:,sp:ep] = data_ij.reshape([N_CHN, -1])


        # 写头文件
        if health_i.sum()>=1 and header_file_pattern is not None:
            file_name = header_file_pattern.format(date=date, name=name_i)
            bheader_list2csv(header_list,file_name, REMOVE_ZERO=True, date=int(date))
    
        # 降采
        if DOWNSAMPLE_RATE>1:

            data_day_DW = np.zeros([N_CHN, NT_aday_DW],dtype='float32')
            for k in range(N_CHN):
                trace = Trace(data_day[k,:])
                trace = trace.decimate(DOWNSAMPLE_RATE)
                data_day_DW[k,:] = trace.data
        else:
            data_day_DW=data_day
            
        # print(data_day_DW.mean(),data_day_DW.max())
        # 写入
        health[i,:] = health_i
        h5file.create_dataset(f'data/{name_i}', data=data_day_DW)
        
        print(i,len(sns),date, path_sn, name_i)
        names.append(name_i)
    h5file.create_dataset(f'health', data=health)
    h5file.create_dataset(f'names', data=np.array(names, dtype='S'))
    h5file.close()



        





