from sklearn.externals import joblib
import pickle
import numpy as np
import pandas as pd





def estimate_metals_gpr(data,regr_file,ss_cuts_file,regr_type):
    regr = joblib.load(regr_file)
    if regr_type=='M':
        #create the colors and absolute magntiudes needed for the regression and single star cuts
        data['M_g']=data['g_PS1']+5*np.log10(1e-3*data['PLX'])+5
        data['M_H_2MASS']=data['H_2MASS']+5*np.log10(1e-3*data['PLX'])+5
        data['M_W1']=data['W1_ALLWISE']+5*np.log10(1e-3*data['PLX'])+5
        data['g-y']=data['g_PS1']-data['y_PS1']
        data['g-W2']=data['g_PS1']-data['W2_ALLWISE']
        data['r-W2']=data['r_PS1']-data['W2_ALLWISE']
        data['r-W1']=data['r_PS1']-data['W1_ALLWISE']
        data['M_r']=data['r_PS1']+5*np.log10(1e-3*data['PLX'])+5

        #mean and standard deviation of the training subset used to normalzie the data
        y_mean=-0.06339634364228897
        y_std=0.27671029005449393
        std_norm=0.125

        regr_columns=['M_g', 'M_H_2MASS', 'M_W1', 'g-y', 'g-W2', 'r-W2']
        ss_color='r-W1'
        ss_mag='M_r'
    elif regr_type=='K':
        #create the colors and absolute magntiudes needed for the regression and single star cuts
        data['M_z']=data['z_PS1']+5*np.log10(1e-3*data['PLX'])+5
        data['g-J']=data['g_PS1']-data['J_2MASS']
        data['z-y']=data['z_PS1']-data['y_PS1']
        data['y-W2']=data['y_PS1']-data['W2_ALLWISE']
        data['W1-W2']=data['W1_ALLWISE']-data['W2_ALLWISE']
        data['M_W2']=data['W2_ALLWISE']+5*np.log10(1e-3*data['PLX'])+5
        data['g-H']=data['g_PS1']-data['H_2MASS']

        #mean and standard deviation of the training subset used to normalzie the data
        y_mean=-0.061195682830781147
        y_std=0.28095342168889686
        std_norm=0.05

        regr_columns=['M_z', 'g-J', 'z-y', 'y-W2', 'W1-W2']
        ss_color='g-H'
        ss_mag='M_W2'
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
        
        if i==0 and regr_type=='M':
            dist=1.797*data[ss_color]+3.859-np.array(data[ss_mag])
            M_H[(M_H<=-0.8) & ((dist>0))]=99.

        if i==0 and regr_type=='K':
            M_H[(M_H<=-0.8) & ((dist>0)| (data[ss_color]<ss_cuts[2][0][i]) | (data[ss_color]>ss_cuts[3][0][i]))]=99.

    M_H_std[M_H==99.]=99.

    return M_H, M_H_std