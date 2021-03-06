import numpy as np
import pandas as pd
import sys
import datetime
from datetime import datetime

# MATH
from math import sqrt
from scipy import signal
from fireTS.models import NARX
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression, Ridge, LassoLars
from sklearn.metrics import r2_score, mean_squared_error, make_scorer, mean_absolute_error
from sklearn.model_selection import TimeSeriesSplit, cross_val_score, KFold, GridSearchCV
from sklearn.pipeline import Pipeline,  make_pipeline, FeatureUnion
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from scipy import stats
from scipy.stats import normaltest

#TIME
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.formula.api import ols
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.regression.rolling import RollingOLS
from statsmodels.regression import *
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tools.tools import add_constant
from statsmodels.tsa import stattools
from statsmodels.tsa.arima.model import ARIMA, ARIMAResults
from statsmodels.tsa.arima_model import *
from statsmodels.tsa.arima_process import ArmaProcess
from statsmodels.tsa.holtwinters import *
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.stattools import adfuller, acf, arma_order_select_ic, pacf_ols, pacf
import pyramid
from pmdarima.arima import auto_arima

#VISUALIZATION 
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.pylab import rcParams
rcParams['figure.figsize'] = 10, 6
plt.style.use('ggplot')

class Model():
    
    '''
    ==Function==
    Run ARIMA and Regression Models
    
    ==Output==
     4 Models - ARIMA
        - Random Forest Regression
        - OLS Linear Regression
        - OLS smf Regression 
    8 subplots 
        [4] Forecast Plots, each entitled with associated MSE score
        [4] Residual Distribution Plots entitled with NormalTest Result Scores
        
        
    ==Parameters==
    |order_method| - selection of various methods of looking for/selecting an ARIMA order
        options:
            - 'predetermined': uses predetermined (2,0,0) as ARIMA order
            - 'auto': uses auto_arima method to look for ARIMA order
            - 'laborious': uses best_order function (COMPUTATIONALLY EXPENSIVE)
            - 'select': allows for user to input order
            DEFAULT= 'predetermined'

    ==Included Functions==
    +train_test
    +lag_train_test
    +multiple_regressors
    +regres_dfs
    +regression
    +evaluate_arima_model
    +best_order
    +auto_pdq
    +ARIMA_predict
    +all_models
    +show_model
    
    
   '''
    
    def __init__(self,order_method='predetermined'):
        self.self = self
        self.order_method=order_method
    
    def train_test(self, df):
        '''
        ==Function==
        Split data into train(80%) and test(20%) dataframes 
        
        ==Returns==
        Train dataframe, test dataframe 
        
        '''
        idx = round(len(df)*.8)
        return df[:idx],df[idx:]

    def lag_train_test(self,df, Xy=True, lag_len=3):
        '''
         ==Function==
        Split data into train(80%) and test(20%) dataframes and 
        Adds 3 lags to each as separate columns
        
        ==Parameters==
        |Xy| (default=True)
            if True:
                splits train and test dataframes into two parts each:
                an X df which contain the original series 
                a y df which contains the lag columns
        ==Returns==
        if Xy==True:
            X_train, y_train, X_test, y_test
        if Xy==False:
            train, test
        '''
        lag_df = (pd.concat([df.shift(i) for i in range(lag_len+1)], axis=1, keys=['y'] + ['Lag%s' % i for i in range(1, lag_len+1)])).dropna() 
        idx = round(len(lag_df)*.8)
        if Xy==False:
            train, test = lag_df[:idx], lag_df[idx:]
            return train, test
        elif Xy==True:
            lag_y, lag_X  = lag_df.y, lag_df.drop(columns='y')    
            X_train, y_train, X_test, y_test = lag_X[:idx], lag_y[:idx], lag_X[idx:], lag_y[idx:]
            return X_train, y_train, X_test, y_test
        
    
    def regressor_fits(self,df, lag_len=3):
        '''
        ==Function==
        applies 3 different regression models .fit() method to the data
        - Random Forest 
        - OLS Linear
        - OLS
        
        ==Returns==
        fitted results of each
            rf, ols_lin, ols
        '''
        X_train, y_train, X_test, y_test = self.lag_train_test(df)
        rf= RandomForestRegressor(n_jobs=-1).fit(X_train,y_train)
        ols_lin = sm.OLS(y_train, X_train).fit()
        ols_train, ols_test= self.lag_train_test(df, lag_len=lag_len, Xy=False)
        ols_str = 'y ~ ' +" + ".join([f"Lag{i}" for i in range(1,lag_len+1)])
        ols = smf.ols(ols_str, data=ols_train).fit()
        return rf, ols_lin, ols
    
    def regressor_predicts(self,df):
        '''
         ==Function==
        applies 3 different regression models .predict() method to the data
        - Random Forest 
        - OLS Linear
        - OLS
        
        ==Returns==
        prediction/forecast results of each model
        rf, ols_lin, ols       
        '''
        
        X_train, y_train, X_test, y_test = self.lag_train_test(df)
        ols_train, ols_test= self.lag_train_test(df, Xy=False)
        rff, ols_linf, olsf = self.regressor_fits(df)
        rf= rff.predict(X_test)
        ols_lin = ols_linf.predict(X_test)  
        ols = olsf.predict(ols_test)
        return rf, ols_lin, ols 
    
    def regressor_resids(self,df):
        '''
        ==Function==
        Extract residuals from regressor_fits function for each model
        
        ==Returns==
        3 dataframes/arrays for each regression model 
        RandomForest_resid, OLS_lin_resid, OLS_resid
        
        '''
        X_train, y_train, X_test, y_test = self.lag_train_test(df)
        rf, ols_lin, ols = self.regressor_fits(df)
        OLS_resid = pd.DataFrame(ols.resid)
        OLS_lin_resid = pd.DataFrame(ols_lin.resid)
        RandomForest_resid = (y_test.cost_per_watt - rf.predict(X_test)).rename(columns={'cost_per_watt':''})
        return RandomForest_resid, OLS_lin_resid, OLS_resid
    
    def regres_dfs(self, df):
        '''
        ==Function==
        Takes the predictions from regressor_predicts function
        Concats all together as different columns within a dataframe
        first column in actual data, followed by 'randomforest', 'olslinear', 'ols'
        
        ==Returns==
        Single dataframe "y_preds" with 4 columns 
        '''
        y_preds = self.lag_train_test(df)[3]
        rf, ols_lin, ols = self.regressor_predicts(df)
        y_preds.rename(columns={'cost_per_watt':'actual'}, inplace=True)
        y_preds['randomforest'], y_preds['olslinear'],y_preds['ols'] = rf, ols_lin, ols
        return y_preds
    
    def formastr(self,str):
        '''
        ==Function==
        Turns a proper model name and formats it to what is shown in the y_preds dataframe columns
        i.e. formast('Random Forest')
        
        ==Returns== 
        'randomforest'
        
        '''
        return str.replace(" ","").lower()
    
    def regression(self, df):   
        '''
        ==Function==
        Compiles training and prediction data +
        beginning and end dates of those +
        model names 
        
        ==Returns==
        y_train,y_preds, [train_s, train_e, pred_s, pred_e], model_type

        y_train:    training data df with 3 lag columns
        y_preds:    prediction df for all regression
        train_s:    start date of training data
        train_e:    end date of training data
        pred_s:     start date of prediction data
        pred_e:     end date of prediction data
        model_type: list of strings of model types
        '''
        y_preds = self.regres_dfs(df)
        y_train = self.lag_train_test(df, Xy=True)[1]
        pred_s, pred_e = y_preds.index.date[0], y_preds.index.date[-1]
        train_s, train_e = y_train.index.date[0], y_train.index.date[-1]
        model_type = ['ARIMA','Random Forest', 'OLS Linear', 'OLS']
        return  y_preds, y_train, [train_s, train_e, pred_s, pred_e], model_type
        
    def evaluate_arima_model(self,X, arima_order):
        '''
        ==Function ==
        Splits data into training/test
        Pushes through ARIMA models 

        ==Returns==
        MSE

        ==Note==
        Only used in arima_order_mses function
        '''
        # prepare training dataset
        train_size = int(len(X) * 0.8)
        train, test = X[0:train_size], X[train_size:]
        history = [x for x in train]
        # make predictions
        predictions = list()
        for t in range(len(test)):
            model = ARIMA(history, order=arima_order, missing='drop')
            model_fit = model.fit(disp=0)
            yhat = model_fit.forecast()[0]
            predictions.append(yhat)
            history.append(test[t])
        # calculate error
        error = mean_squared_error(test, predictions)
        return error

    def best_order(self,df):
        '''
        ==Function==
        Uses various p,d,qs within below range
        Tests out each combination 

        ==Prints== 
        Params with the best cfg + best MSE

        ==Returns==
        best order in format: (p,d,q)
        
        ==Input Suggestion==
        Use [evaluate_models(df.values.dropna(), p_values, d_values, q_values)]

        ==Note==
        Computationally expensive! 
        '''
        df = df.dropna().values
        p_values = [0, 1, 2, 3, 4]
        d_values = range(0, 3)
        q_values = range(0, 3)
        best_score, best_cfg = float("inf"), None
        for p in p_values:
            for d in d_values:
                for q in q_values:
                    order = (p,d,q)
                    try:
                        mse = self.evaluate_arima_model(df, order)
                        if mse < best_score:
                            best_score, best_cfg = mse, order
                        #print('ARIMA%s MSE=%.4f' % (order,mse))
                    except:
                        continue
        return best_cfg

    def auto_pdq(self, df):
        '''
        ==Function==
        Uses Auto ARIMA to obtain best parameters for data
        
        ==Returns==
        auto_arima variable to use in other functions
        
        ==Set Parameters==
        out_of_sample_size=750
        stepwise=False
        n_jobs=-1
        start_q=0 
        stationary=True
        test='adf'
        seasonal=False 
        information_criterion='oob'
        
        '''
        #return auto_arima(df, seasonal=False,stationary=True,start_p=0, start_q=0, max_order=8, stepwise=False).order
        #return auto_arima(df, test='adf', out_of_sample_size=750,stationary=True,seasonal=False,n_jobs=-1, start_p=2,start_q=0,stepwise=False, max_q=0,max_order=2).order
    
        return auto_arima(df, out_of_sample_size=750,stepwise=False,n_jobs=-1,start_q=0, stationary=True, test='adf', seasonal=False, information_criterion='oob').order
    
    def ARIMA_predict(self, df):
        '''
        ==Function== 
        Attain user inputs to decide ARIMA order 
        
        ==Returns==
        res = .fit()
        atrain, atest = train and test set used for ARIMA
        arima_title = title to be used in a plot
        a_pred = predictions from ARIMA model
        order = order used in ARIMA
        '''
        if self.order_method.lower() == 'predetermined':
            order=(2,0,0)
        elif self.order_method.lower() == 'auto':
            order=self.auto_pdq(df)
        elif self.order_method.lower() == 'manual':
            print('CAUTION: MANUAL IS VERY COMPUTATIONALLY EXPENSIVE (~20 minutes) \nPlease enter "ok" to proceed')
            confirmation = input()
            if confirmation.lower() =='ok': 
                print('Please hold')
                order = self.best_order(df)
            else:
                print('Changing to Auto')
                order=self.auto_pdq(df)
        elif self.order_method.lower() == 'select':
            print('Please input each parameter')
            ord_p= int(input('p:'))
            ord_d= int(input('d:')) 
            ord_q=int(input('q:'))
            order = (ord_p,ord_d,ord_q)

        atrain, atest = self.train_test(df)
        atest_s, atest_e = atest.index.date[0], atest.index.date[-1]
        atrain_s, atrain_e = atrain.index.date[0], atrain.index.date[-1]
        res = ARIMA(df, order=order).fit()
        a_pred = res.predict(atest_s, atest_e)
        arima_title = f'ARIMA {order}         MSE={round(mean_squared_error(atest,a_pred),5)}'
        return res, atrain, atest, arima_title, a_pred, order    
    
    def all_models(self,df):
        '''
        ==Function==
        Combines all regression models and ARIMA to create 8 subplots:
            [4] depicting forecasts
            [4] associated residual distribution plots
        '''
        y_preds, y_train, [train_s, train_e, pred_s, pred_e], model_type = self.regression(df)
        res, atrain, atest, arima_title, a_pred, order = self.ARIMA_predict(df)        
        RandomForest_resid, OLS_lin_resid, OLS_resid = self.regressor_resids(df)
        resid_list = [res.resid,RandomForest_resid, OLS_lin_resid, OLS_resid]
        idx = round(len(df)*.8)
        fig, axs = plt.subplots(4,2, figsize=(30,20), constrained_layout=True)
        #===Titles and text
        fig.suptitle('\n \n \n', fontsize=40)
        fig.text(.05,.95, 'Forecast Models'.center(60,'_'),fontsize=28)
        fig.text(.565,.95, 'Residual Distribution'.center(60,'_'),fontsize=28)
        fig.text(.115,.91,"Trained on Data from    {} - {}".format(' '.join([train_s.strftime("%b"), str(train_s.year)]),' '.join([train_e.strftime("%b"), str(train_e.year)])).center(60),fontsize=22) 
        fig.text(.115,.89, "Data Forecasted for    {} - {}".format(' '.join([pred_s.strftime("%b"), str(pred_s.year)]),(' '.join([pred_e.strftime("%b"), str(pred_e.year)]))).center(60),fontsize=22)
        #===ARIMA Forecast Plot===
        axs[0,0].plot(a_pred, label='ARIMA Forecast')
        axs[0,0].plot(atest.index, atest, label='Actual')
        axs[0,0].plot(atrain.index[-30:], atrain[-30:], label='Train', color='gray')
        axs[0,0].fill_between(a_pred.index, atest.cost_per_watt.values, 0, color='gray', alpha=.3)
        axs[0,0].set_title(arima_title, fontsize=18)
        axs[0,0].legend(loc='best')
        axs[0,0].set_xlim(left=atrain.index.date[-31])
        #===Regression Forecast Plots====
        for i in range(1,4):
            exec(f"axs[{i},0].plot(y_preds['{self.formastr(model_type[i])}'], label='{model_type[i]}', linewidth=2)")
            exec(f"axs[{i},0].plot(y_preds.actual, label= 'Actual')")
            exec(f"axs[{i},0].plot(y_train[-30:], label='Train', color='gray')")
            exec(f"axs[{i},0].fill_between(y_preds.index, y_preds['{self.formastr(model_type[i])}'], y_preds.actual, color='gray', alpha=.3)")
            exec(f"axs[{i},0].set_title('{model_type[i]} Regression        MSE={round(mean_squared_error(y_preds.actual, y_preds[self.formastr(model_type[i])]),5)}', fontsize=18)")
            exec(f"axs[{i},0].legend(loc='best')")
            exec(f"axs[{i},0].set_xlim(left=y_train.index.date[-31])")
        #===Residual Plots===
        for i in range(4):
            exec(f"axs[{i},1] = sns.distplot(resid_list[i], fit=stats.norm, ax=axs[i,1])")
            (mu,sigma)= stats.norm.fit(resid_list[1])
            exec(f"axs[{i},1].legend([f'Normal dist. ($\mu=$ {round(mu,2)} and $\sigma=$ {round(sigma,2)})'], loc='best')")
        #===ARIMA + RF Residuals Plot Titles===   
        for i in range(2):
            exec(f"axs[{i},1].set_title('Normal Test for {model_type[i]} Model        statistic={round(normaltest(resid_list[i])[0],4)} | pvalue={round(normaltest(resid_list[i])[1],4)}',fontsize=18)")    
        #===OLS Lin + OLS Residuals Plot Titles===
        for i in range(2,4):   
            exec(f"axs[{i},1].set_title('Normal Test for {model_type[i]} Model        statistic={round(normaltest(resid_list[i])[0][0],4)} | pvalue={round(normaltest(resid_list[i])[1][0],4)}',fontsize=18)")           
        plt.savefig(f'model_plots_{self.order_method}.png')
        plt.show()
        
    def show_model(self,df):
        return self.all_models(df)

if __name__ == "__main__":
    Model().show_model(df)