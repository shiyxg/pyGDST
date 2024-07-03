import numpy as np
from .paras import FHEADER_DEF, BHEADER_DEF,F_KEYS, B_KEYS
from .paras import COUNT2V, BLOCK_SIZE, DATA_SIZE, DB_FACTOR


def fheader_get_def(M=',', wanted=[]):
    '''
    glds仪器输出的bin文件的2KB头文件
    NAME_DEF:{'par1':idx_1}
    把头文件定义转换为CSV文件的头文件, eg:"lat,lon,..."

    M: , for csv
    wanted: 所需的参数名称, 不提供则使用全部定义
    '''
    r = ''

    keys =  F_KEYS if len(wanted)==0 \
            else wanted
    for i, name in keys:
        r += f'{name}{M}'
    return r


def fheader_bin2txt(data:np.array, M=',', wanted=[]):
    '''
    把data中的有效信息转换出来,默认输出CSV文件的一行 "par1,par2,..."
    
    data: np.array(int32)
    M: , for csv
    wanted: 所需的参数名称
    '''

    r = ''
    keys =  F_KEYS if len(wanted)==0 \
            else wanted
    for i, name in keys:
        i = FHEADER_DEF[name]
        r += f'{data[i]}{M}'
    return r

def bheader_decode(header) -> tuple:
    '''
    把block_header 中有效信息解码出来,

    out: date_UTC,time_UTC, lat, lon, seq1, seq2
    '''

    H = header.tobytes()
    
    y =  int.from_bytes(H[18:19],'little')
    m =  int.from_bytes(H[19:20],'little')
    d =  int.from_bytes(H[20:21],'little')
    h =  int.from_bytes(H[21:22],'little')
    s1 = int.from_bytes(H[22:23],'little')
    s2 = int.from_bytes(H[23:24],'little')
    date_UTC = y*10000+m*100+d
    time_UTC = h*10000+s1*100+s2

    lat = int.from_bytes(H[24:28],'little')
    lat = lat%2**28
    lat = lat//1e6 + (lat%1e6)/1e4 / 60.0

    lon = int.from_bytes(H[28:32],'little')
    lon = lon%2**28
    lon = lon//1e6 + (lon%1e6)/1e4 / 60.0

    seq1 = int.from_bytes(H[32:36],'little')
    seq2 = int.from_bytes(H[36:39],'little')
    
    return date_UTC,time_UTC, lat, lon, seq1, seq2

 
def read_bin_multiple_chn(file_name, dt=1, DB=0,
             dtype=np.float32,FTYPE=np.int32,
             block_size = BLOCK_SIZE, data_size = DATA_SIZE, header_size=BLOCK_SIZE-DATA_SIZE)-> tuple:
    '''
    读取GDST仪器二进制文件, 多通道文件

    file_name: 文件名
    dt       : 采样率，单位ms
    DB       : 增益率,仅 0, 6 18,24可选
    dtype    : 输出数据流的格式
    FTYPE    : 文件内部格式
    block_size :  单个数据块尺寸，默认512 # float32
    data_size  :  单个数据块数据尺寸，默认500 # float32
    header_size:  单个数据块头文件尺寸，默认12 # float32

    output:[头文件 1d, 数据流([N_CHN, NB, data_size]), 内部头文件[N_CHN,header_size]]
    '''

    with open(file_name, 'rb') as f:
        data_int = np.fromfile(f, dtype=FTYPE)
    # data_float = np.zeros(data_int.shape, dtype=dtype)
    
    BS,DS, HS = block_size,data_size,header_size

    N_BLOCK = len(data_int)//BS
    N_DATA = int(7200/dt)
    assert DS*dt/1000*N_DATA==3600 # 一小时
    N_CHN = N_BLOCK//N_DATA #通道数检测

    # print(N_CHN)

    data_int = data_int.reshape([N_BLOCK, HS+DS])
    # 头文件
    f_header = data_int[0,:]
    # 数据流
    data_float = data_int[1:N_DATA*N_CHN+1,HS:HS+DS]*COUNT2V*DB_FACTOR[DB]
    data_float = data_float.astype(dtype)
    data_float = data_float.reshape([N_DATA, N_CHN,DS])
    data_float = np.transpose(data_float,[1,0,2])

    # block头文件
    headers = data_int[1:N_DATA*N_CHN+1,:HS]
    headers = headers.reshape([N_DATA, N_CHN,HS])
    headers = np.transpose(headers,[1,0,2])
    
    return f_header, data_float, headers

def fill_empty_block(data_float:np.array, headers:np.array,
                     fill_value=0
                    )-> tuple:
    '''
    data_float: 3D data, N_CHN*N_block*data_size
    headers   : 3D data, N_CHN*N_block*header_size
    fill_value: 对未采样部分的填充数值

    output    : 2D data_float filled with 0, N_CHN*(N_block*data_size)
    '''

    nc, nb, nd = data_float.shape
    _,  _,  nh = headers.shape
    print('not finished')
    
    return data_float

def read_bin(file_name, dt=1, DB=0,
             IS_Z_CHN = False,
             fill_value=None, 
             dtype=np.float32,FTYPE=np.int32,
             block_size = BLOCK_SIZE, data_size = DATA_SIZE, header_size=BLOCK_SIZE-DATA_SIZE)-> tuple:
    '''
    读取GDST仪器二进制文件

    file_name: 文件名
    dt       : 采样率，单位ms
    DB       : 增益率,仅 0, 6 18,24可选
    fill_value: 关机没采集部分的填充格式
    IS_Z_CHN : 是否为单分量仪器,是则数据维度不再有CHN维度

    dtype    : 输出数据流的格式
    FTYPE    : 文件内部格式
    block_size :  单个数据块尺寸，默认512 # float32
    data_size  :  单个数据块数据尺寸，默认500 # float32
    header_size:  单个数据块头文件尺寸，默认12 # float32

    output:(头文件, 数据流, 内部头文件)
    '''

    f_header, data_float, headers = \
        read_bin_multiple_chn(file_name, dt, DB,
             dtype=dtype,FTYPE=FTYPE,
             block_size = block_size, data_size = data_size, header_size=header_size)

    # 对没采集状态填充
    if fill_value is not None:
        data_float = fill_empty_block(data_float, headers,fill_value=fill_value)
        
    nc,nb,nd = data_float.shape
    data_float = data_float.reshape([nc, nb*nd])

    if IS_Z_CHN:
        data_float = np.squeeze(data_float)
        headers = np.squeeze(headers)

    return    f_header, data_float, headers

def read_header(file_name, dt=1,
             dtype=np.float32,FTYPE=np.int32,
             block_size = BLOCK_SIZE
             )-> np.array:
    '''
    只读取GDST仪器二进制文件的头文件

    file_name: 文件名
    dt       : 采样率，单位ms
    dtype    : 输出数据流的格式
    FTYPE    : 文件内部格式
    block_size :  单个数据块尺寸，默认512 # float32

    output:头文件（1D）
    '''

    with open(file_name, 'rb') as f:
        data_int = np.fromfile(f, count=block_size, dtype=FTYPE)
    
    return data_int
    