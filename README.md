# pyGDST

转换中科深源仪器产生的BIN文件为SAC,H5文件的工具包，支持1C/3C/4C仪器

A toolkit to read and convert seismic data of GDST (https://www.geodeepsensing.com/) sensors to H5 and SAC file format 

## 依赖(Dependencies)

* glob
* numpy
* obspy
* h5py
* tqdm

### 读取GDST仪器二进制文件 (Reading)

eg:
```python
from pygdst import read_bin

dt = 0.002# sampling interval, s
file_header, data, block_headers = read_bin('./P320LINE/A0000102/24052808.BIN', dt=dt*1000)
# file_header : 512 x int32
# data        : recording of 1h
# block_headers : 每500个采样点的数据块头文件
```


### 转换单一仪器的文件为h5文件 (Convert recordings of a sensor to .H5)

eg:
```python
from pygdst import bins2h5

dt = 0.002# sampling interval, s

bin_files = glob.glob(f'./P320LINE/A0000102/*.BIN')
new_file = './test.h5'
bins2h5(bin_files, new_file, dt=dt)

'''
f.create_dataset('data', data=data)
f.create_dataset('headers', data=headers)
f.create_dataset('Times',data=t_all)
f.create_dataset('dt',data=dt)
f.create_dataset('N_hours',data=nh)
f.create_dataset('chns',data=CHN_DEF[nc])
f.create_dataset('raw_files',data=np.array(bins_file, dtype='S'))
'''

```

### 将一天的记录转换为h5文件 (Convert recordings of all sensors in a day to .H5)

eg:
```python
from pygdst import bins2h5

dt = 0.002# sampling interval, s

bins2h5_day('./root', './out/test_240620.h5', date='240620', header_file_pattern='./out/{name}_{date}.csv')

'''
把所有台站同一天的文件转成一个统一格式的,大H5文件

    './root': 原始文件根目录
    './out/test_240620.h5'    : 生成的h5文件名
    
    date       : 指定日期
    header_file_pattern: 头文件信息的写入位置， eg: 'path/{date}_{name}.csv'
    
    N_CHN      : 通道数
    dt         : 采样间隔, 单位ms， 
    DOWNSAMPLE_RATE：降采样率， 整数
    PATH_MARKER: 路径分割符号
    sn2name    : 仪器号转名称
'''

```


### 转换文件为sac文件 (Convert to .sac)

eg:
```python
from pygdst import bins2sac

dt = 0.002# sampling interval, s
DW = 5 # 降采样5倍到0.01s采样

# files in a day
bin_files_aday = glob.glob(f'./P320LINE/A0000102/240528*.BIN')
sac_file = './test.sac'

bins2sac(bin_files_aday,sac_file,dt=dt, name='my_stat_name', DOWNSAMPLE_RATE=DW)

```

### 测试 test

eg:
```python
from pygdst import test

test()

```

![](./tests/test_bin.png)