from .gdst import read_bin,read_bin_multiple_chn
from .convert import bins2h5,bins2sac
import numpy as np
from pylab import *

def test():
    dt = 0.002
    test_name = './24070101.BIN'
    a = np.zeros([3601,512], dtype='int32')
    a[1:, 100]=2**31
    a[1:, 200]=2**31
    a[1:, 250:450]=2**31*np.sin(np.linspace(0,10,200))
    a.tofile(test_name)

    # H, data, hs = read_bin(test_name, dt=dt*1000)
    H, data, hs = read_bin_multiple_chn(test_name, dt=dt*1000)
    
    fig = figure(figsize=[4,4],dpi=600)
    t1 = np.arange(500)*dt
    t2 = np.arange(3600)

    T1,T2 = np.meshgrid(t1,t2)
    pcolormesh(T1,T2, data.reshape([3600,500]), cmap='seismic')
    xlabel('t_each_blocks(s)')
    ylabel('t_in_block(s)')
    fig.tight_layout()
    savefig('./test_bin.png')
    

    bins2h5([test_name],'./test.h5',dt=dt)
    bins2sac([test_name],'./test_{CHN}.sac', N_CHN=1,dt=dt, name='test',DOWNSAMPLE_RATE=5)

if __name__ =='__main__':
    test()