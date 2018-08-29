import pandas as pd
import numpy as np

if __name__ == "__main__":
    
    import h5py
    import matplotlib.pylab as plt
    
    #x = pd.read_hdf("./X.h5")    
    #y = pd.read_hdf("./Y.h5")
    
    # import dataset
    x = h5py.File('./X.h5','r')
    y = h5py.File('./Y.h5','r')
    
    # convert to pandas DataFrame
    df_x = pd.DataFrame(x['X'][:])
    df_y = pd.DataFrame(y['Y'][:])
    
    # rename columns for readability
    df_x.columns = ['x'+str(i+1) for i in df_x.columns]
    df_y.columns = ['y'+str(i+1) for i in df_y.columns]
    
    print(1)