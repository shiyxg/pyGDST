import sys
import glob
sys.path.append('../src/')

from pygdst import test, bins2h5,bins2sac

test()

bin_files_aday = glob.glob(f'./A0000102/240530*.BIN')
sac_file = './P107.Z.240530.sac'
bins2sac(bin_files_aday,sac_file, N_CHN=1,dt=0.002, name='P107', DOWNSAMPLE_RATE=5)

h5_file = './P107.Z.240530.h5'
bins2h5(bin_files_aday,h5_file,dt=0.002)