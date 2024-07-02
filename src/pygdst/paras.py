
# 每小时文件中, 前2048字节的定义
# 实际中以4B为单位输出

FHEADER_DEF={
    'time' : 0,
    'npts' : 1,
    'lat'  : 2,
    'lon'  : 3,

}
F_KEYS=FHEADER_DEF.keys()

# 每小时文件中, 每2048字节数据块中,前48字节中有效信息的定义
BHEADER_DEF={
    'time' : 0,
    'npts' : 1,
    'lat'  : 2,
    'lon'  : 3,
}
B_KEYS=BHEADER_DEF.keys()


# count 2 电压
COUNT2V = 2.5* 1000/2**31 

# DB定义
DB_FACTOR = {
    0:1,
    6:2,
    12:4,
    24:8,
}

# 通道定义
CHN_DEF={
    1:'Z',
    3:'ENZ',
    4:'ENZH',
}

# 数据块大小
BLOCK_SIZE = 512 # int32
DATA_SIZE = 500 # int32

