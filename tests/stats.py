import sys
import glob
import numpy as np
from obspy.core.utcdatetime import UTCDateTime
sys.path.append('../src/')

from pygdst import read_bin, bheader2csv, bins2h5_day


dt=0.002
DW=2
# H,d,hs = read_bin('./A0000449/24062013.BIN', dt=dt*1000)

# bheader2csv(hs[0,:],'test.csv',interval=60)

bins2h5_day('./root', './out/test_240528.h5', date='240528', header_file_pattern='./out/{name}_{date}.csv',
            dt=dt,
            DB=12,
            DOWNSAMPLE_RATE=DW)


