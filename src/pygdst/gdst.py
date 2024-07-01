import numpy as np
from .paras import FHEADER_DEF, BHEADER_DEF,F_KEYS, B_KEYS
from .paras import COUNT2V, BLOCK_SIZE, DATA_SIZE


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


def bheader_get_def(M=',', wanted=[]):
    '''
    把block_header头文件定义转换为CSV文件的头文件, eg:"lat,lon,..."
    M: , for csv
    wanted: 所需的参数名称, 不提供则使用全部定义
    '''

    r = ''

    keys =  B_KEYS if len(wanted)==0 \
            else wanted
    for i, name in keys:
        r += f'{name}{M}'
    return r


def bheader_bin2txt(data:np.array, M=',', wanted=[]):
    '''
    把block_header 中的data中的有效信息转换出来,默认输出CSV文件的一行 "par1,par2,..."

    data: np.array(int32)
    M: , for csv
    wanted: 所需的参数名称
    '''

    r = ''
    keys =  B_KEYS if len(wanted)==0 \
            else wanted
    for i, name in keys:
        i = BHEADER_DEF[name]
        r += f'{data[i]}{M}'
    return r

    
def read_bin(file_name, dt=1,
             dtype=np.float32,FTYPE=np.int32,
             block_size = BLOCK_SIZE, data_size = DATA_SIZE, header_size=BLOCK_SIZE-DATA_SIZE)-> tuple:
    '''
    读取GDST仪器二进制文件

    file_name: 文件名
    dt       : 采样率，单位ms
    dtype    : 输出数据流的格式
    FTYPE    : 文件内部格式
    block_size :  单个数据块尺寸，默认512 # float32
    data_size  :  单个数据块数据尺寸，默认500 # float32
    header_size:  单个数据块头文件尺寸，默认12 # float32

    output:(头文件（1D）, 数据流（1D, mv）, 内部头文件（2D）)
    '''

    with open(file_name, 'rb') as f:
        data_int = np.fromfile(f, dtype=FTYPE)
    # data_float = np.zeros(data_int.shape, dtype=dtype)
    
    BS,DS, HS = block_size,data_size,header_size

    N_BLOCK = len(data_int)//BS
    N_DATA = int(7200/dt)
    assert DS*dt/1000*N_DATA==3600 # 一小时

    data_int = data_int.reshape([N_BLOCK, HS+DS])

    # 头文件
    f_header = data_int[0,:]
    
    # 数据流
    data_float = data_int[1:N_DATA+1,HS:HS+DS]*COUNT2V
    data_float = data_float.astype(dtype)

    # block头文件
    headers = data_int[1:N_DATA+1,:HS]
    
    return f_header, data_float.flatten(), headers

def read_header(file_name, dt=1,
             dtype=np.float32,FTYPE=np.int32,
             block_size = BLOCK_SIZE)-> np.array:
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
    