# pyGDST

转换中科深源仪器产生的BIN文件为SAC,H5文件的工具包

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


### 转换文件为h5文件 (Convert to .H5)

eg:
```python
from pygdst import bins2h5

dt = 0.002# sampling interval, s

bin_files = glob.glob(f'./P320LINE/A0000102/*.BIN')
new_file = './test.h5'
bins2h5(bin_files, new_file, dt=dt)

'''
H5 文件内部定义
f.create_dataset('data', data=data)
f.create_dataset('headers', data=headers)
f.create_dataset('Times',data=t_all)
f.create_dataset('dt',data=dt)
f.create_dataset('NF',data=len(data))
f.create_dataset('raw_files',data=np.array(bins_file, dtype='S'))
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