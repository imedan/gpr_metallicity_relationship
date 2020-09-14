from sklearn.externals import joblib
import pickle
import numpy as np
import pandas as pd





def estimate_metals_gpr(data,regr_file,ss_cuts_file,regr_type):
    '''
        This predicts the average metallicity, [M/H], for stars in two temperature regimes;
        regr_type 'K' (3500 < T < 5280 K) and regr_type 'M' (2850 < T < 3500 K).
        
        Parameters
        ----------
        data (Pandas Dataframe): data in the form of a Pandas Dataframe. The columns in this dataframe must match
                                 the column names from the cross match by Medan, Lepine and Hartman (2020).
        regr_file (str): The file name that stores the sklearn Gaussian Process Regressor for a particular
                          temperature regime
        ss_cuts_file (str): The file name single star cuts used to indentify possible unresolved binaries in a dataset
                            that would have innacurate metallicity estimates
        regr_type (str): Specifying which temperature regime this regressor covers, where regr_type 'K' (3500 < T < 5280 K)
                         and regr_type 'M' (2850 < T < 3500 K)
        Returns
        -------
        M_H (numpy array): Estimate metallicities from Gaussian Process Regressor. All entries with 99.0 either have estimated
                           values outside the bounds or did not pass single star cuts.
        M_H_std (numpy array): Estimate confidence on metallicities from Gaussian Process Regressor. All entries with 99.0
                                either have estimated values outside the bounds or did not pass single star cuts.
    '''
    regr = joblib.load(regr_file)
    if regr_type=='M':
        #create the colors and absolute magntiudes needed for the regression and single star cuts
        data['M_r']=data['rmag_PS1']+5*np.log10(1e-3*data['PLX_GaiaDR2'])+5
        data['r-W1']=data['rmag_PS1']-data['W1mag_AllWISE']
        data['i-K']=data['imag_PS1']-data['Ksmag_2MASS']
        data['g-W1']=data['gmag_PS1']-data['W1mag_AllWISE']
        data['M_W1']=data['W1mag_AllWISE']+5*np.log10(1e-3*data['PLX_GaiaDR2'])+5

        #mean and standard deviation of the training subset used to normalzie the data
        y_mean=-0.02778879031644286
        y_std=0.27765320864865234
        std_norm=0.125

        regr_columns=['M_r', 'r-W1', 'i-K']
        ss_color='g-W1'
        ss_mag='M_W1'
    elif regr_type=='K':
        #create the colors and absolute magntiudes needed for the regression and single star cuts
        data['M_g']=data['gmag_PS1']+5*np.log10(1e-3*data['PLX_GaiaDR2'])+5
        data['g-y']=data['gmag_PS1']-data['ymag_PS1']
        data['y-W2']=data['ymag_PS1']-data['W2mag_AllWISE']
        data['J-W2']=data['Jmag_2MASS']-data['W2mag_AllWISE']
        data['W1-W2']=data['W1mag_AllWISE']-data['W2mag_AllWISE']
        data['M_K']=data['Ksmag_2MASS']+5*np.log10(1e-3*data['PLX_GaiaDR2'])+5
        data['g-W1']=data['gmag_PS1']-data['W1mag_AllWISE']

        #mean and standard deviation of the training subset used to normalzie the data
        y_mean=-0.07309052889859481
        y_std=0.30552923628469836
        std_norm=0.05

        regr_columns=['M_g', 'g-y', 'y-W2', 'J-W2', 'W1-W2']
        ss_color='g-W1'
        ss_mag='M_K'
    else:
        print("Incorrect Regressor Type!")
        return 0,0


    #estimate metallicity and confidence on estimates
    M_H=np.zeros(len(data))+99.
    M_H_std=np.zeros(len(data))+99.
    for i in range(0,round(len(data)/10000)*10000,10000):
        M_H[i:i+10000],M_H_std[i:i+10000]=regr.predict(data[regr_columns][i:i+10000],return_std=True)

    M_H=M_H*y_std+y_mean
    M_H_std=(M_H_std+std_norm/y_std)*y_std

    #remove estimates out of bounds of training subset
    M_H[M_H<-2.3]=99.
    M_H[M_H>0.5]=99.

    #upload single star cuts
    with open(ss_cuts_file,'rb') as f:
        ss_cuts=pickle.load(f)

    #remove stars that don't pass single star cuts
    mhs=np.arange(-0.8,0.6,0.1)

    for i in range(len(mhs)-1):
        evl=eval("(M_H>mhs[i]) & (M_H<=mhs[i+1])")
        
        p=ss_cuts[0][0][i]
        
        dist=p(data[ss_color])-np.array(data[ss_mag])
        
        M_H[evl & ((dist>ss_cuts[1][0][i][0]) | (dist<ss_cuts[1][0][i][1]) | (data[ss_color]<ss_cuts[2][0][i]) | (data[ss_color]>ss_cuts[3][0][i]))]=99.
        

    M_H[(M_H<=-0.8) & ((dist>0)| (data[ss_color]<ss_cuts[2][0][i]) | (data[ss_color]>ss_cuts[3][0][i]))]=99.

    M_H_std[M_H==99.]=99.

    return M_H, M_H_std
