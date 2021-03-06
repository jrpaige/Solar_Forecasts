# Time Series Forecasting of Solar Panel Costs 
--- 

The project’s model employs univariate ARIMA time series analysis and multiple regressors to generate a forecast for a cost_per_watt target variable of solar panel installations. The exploratory aspect of the project provided an opportunity to understand time series analysis on a granular level.  

<img  src="https://www.ecmag.com/sites/default/files/solar-energy-city.jpg" align="center"  >

---
# Tech Stack

`Python`<br>
`Numpy`<br>
`Pandas`<br>
`Scikit-Learn`<br>
`Matplotlib`<br>
`SciPy`<br>
`StatsModels`<br>
`PMDarima`<br>
`CPI`<br>
`Seaborn`<br>
`sktime`<br>
`fireTS`

---
# Scripts
`Prep.py`
- This class incorporates 11 steps to prep the data for the Time Series and Regression models. 

`Model.py`
- This class takes the dataframe created from the Prep script and employs three types of regression and two types of ARIMA models. It then outputs five plots representing the outcome of each, notating the resulting MSE score as well. 

--- 
# Notebooks

`EDA`
- Exploratory Data Analysis on Data focused on Costs, States, System Sizes, and Customer Segments. 

`Model`
- Implementation of model on data 

`Time_Series_Dilligence`
- Basic time series progression functions to look at data 

---
# Data 

### Variable Creation
- Total adjusted installed  cost = 
total installed cost with adjustments made for inflation<br> 
- cost per watt<img src="https://latex.codecogs.com/gif.latex?\dpi{100}&space;\fn_phv&space;\small&space;=\frac&space;{\textup{total&space;adjusted&space;installed&space;costs}}{\textup{system&space;size}}" />


### EDA

This model uses data collected through Berkeley Lab's [Tracking the Sun](https://emp.lbl.gov/tracking-the-sun/) initiative. 

The data includes over 1.6 million observations of solar panel installations collected over twenty years and includes over 60 features/columns related to price, taxes/rebate programs, technology, location, manufacturing, and installation. 

Between 1998 and 2018, individual installation observations were provided by 28 different states to Berkeley Lab who compliled and published the data. 

[EDA Notebook](https://github.com/jrpaige/Solar_Forecasts/blob/master/EDA.ipynb)

##### Decisions made based on EDA:
- Only use RES sector data
- Use median vs mean as average

### Data Transformation
Using the mean average on the data was too volitile and proved un-useful. Based on the high deviation of each time period's max point, it became more prudent to instead use the median, which points to the exact middle data point.

While determining if any parameters should be in place to limit outliers, I looked into how limiting different amounts on the cost_per_watt variable had on the data.

| Model | No limit | \$ 25  limit | \$ 20 limit | \$ 15 limit | \$10 limit| \$5 limit |
|-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
|| ||MSE      | |    | |
| Random Forest | 0.01571|  0.01738| 0.019 | 0.01681 | 0.01558 | 0.01122|
| OLS Linear | 0.0114 |  0.01278|  0.01271| 0.01315 | 0.01254 |0.00418 |
| OLS SMF    | 0.01265 |  0.01345| 0.01309 | 0.01327 | 0.01259 | 0.00804|

While the best scores did result from the $5 limit and $10 limit, this is not going to work in the real world, as prices have not and will not always fall within that range. The next best scores occur when the amounts were not limited to a dollar amount. As such, data transformation has been changed to remove the limit. 

Moving forward, it could be argued to only use data after the solar panel prices became lower than $10/per watt, given the effect innovation had on the market.

For the purposes of this model, I have not added any limits on cost_per_watt. 




### Null Handling
- Nulls were replaced with median values from same year
---
# Time Series 

#### DECOMPOSITION 
Data did not show any signs of seasonality, cyclicality, or trends. <br>
white noise<br>
However, data was not initially stationary. 

 #### STATIONARITY
- ACF and PACF plots 
- Rolling mean, median, and std
- Augmented Dickey Fuller Test


Within this data, stationarity had to be achieved by taking the change in cost_per_watt from one week to the next, aka differencing the data. 
Differencing can help stabilize the mean of a time series by removing changes in the level of a time series, and therefore eliminating (or reducing) any trend and seasonality.

Initially, I simply used the `.diff()` method for a first order difference between consecutive observations. Next I tried second order differencing, which takes the difference of the difference via `.diff().diff()`. I also tried two period differencing `.diff(periods=2)` which takes the difference of a data point and the data point from two weeks prior. 

A critical value of .05 was used to determine if I would reject or fail to reject the ADF null hypothesis. After differencing, the P-value for the data reached less than 0.000000 and stationarity was decidedly achieved. 

---
# Models

#### TIME SERIES MODEL
##### ARIMA 
Used AutoArima to identify p,d,q parameters


#### REGRESSION MODELS
Regression was used as a means to reference how ARIMA was performing on the data when compared to basic regressors. 
##### Random Forest Regressor
##### OLS Linear 
##### OLS 
---
#  Performance 

#### ANALYSIS

| Model | No limit | \$ 25  limit | \$ 20 limit | \$ 15 limit | \$10 limit| \$5 limit |
|-----:|:-----:|:-----:|:-----:|:-----:|:-----:|:-----:|
|| ||MSE      | |    | |
| Random Forest | 0.01571|  0.01738| 0.019 | 0.01681 | 0.01558 | 0.01122|
| OLS Linear | 0.0114 |  0.01278|  0.01271| 0.01315 | 0.01254 |0.00418 |
| OLS SMF    | 0.01265 |  0.01345| 0.01309 | 0.01327 | 0.01259 | 0.00804|

While the best scores did result from the $5 limit and $10 limit, this is not going to work in the real world, as prices have not and will not always fall within that range. The next best scores occur when the amounts were not limited to a dollar amount. As such, data transformation has been changed to remove the limit. 

Moving forward, it could be argued to only use data after the solar panel prices became lower than $10/per watt, given the effect innovation had on the market.


#### EVALUTATION
I chose to use Mean Squared Error as the evaluation metric to score both the regression and the ARIMA models. ACF was also taken into consideration in some initial time series dilligence and trials.

As I trialed out different versions of the data on the regression models, the more I limited the cost per watt, the worse the regression models did.

Initially, I limited the cost per watt to 25 dollars to remove outliers, however when further limiting the cost per watt down to 10, 15, and 20 dollars, the more I limited the variable, the worse all the models did. My final verison of the data does not limit cost per watt and the scores of the regression models improved. 

Upon trialing out the second order differenced data set (`.diff().diff()`) and the two period differenced data set (`.diff(periods=2`), I came to find that the best 
ARIMA order parameters on both sets were `p` = 3 and `q`=1, which seems to align with the ACF(`q`) and PACF(`p`) plots for the second order differenced data.

![](imgs/two_differ_plots.png)

The `d` parameter of 0 was used given that the data didn't need to be made further stationary within the ARIMA model (both sets acheived at least a 0.0e-10 p-value). Infact, using a 1 for `d` caused errors in the ARIMA model. 

Using the ARIMA order of (3,0,1): <br>
The two period differenced set produced an MSE score of 0.01187 <br>
The second order differenced set produced an MSE score of 0.01173

While using second order differencing for the ARIMA model resulted in improved MSE scores, using the second order differencing on the regression models resulted in worse scores. 

While I would like to be able to use both for the model, it would not be accurate to compare two different data sets. 

#### RESULTS

![](imgs/model_plots.png)




---
#  Insights

#### Annomoloy Detection 
- There is a seemingly random jump in cost_per_watt around 2016. This can likely be attributed to the political lanscape, as politics have a major influence in the US on renewable energy progress. 
- Studies have shown that, historically, renewable energy progress slows when there is a larger Republican influence in both congress and the executive branch. [include citation]
- I hypothesize that residential customers were likely trying to take advantage of any renewable energy incentives programs available before they were gone. The increased demand likely drove the costs up. 

---
#  Next Steps

Use Reinforcement learning of a LSTM RNN Model to utilize multiple variables.<br>
Potential significant variables:
- income
- political landscape
- global energy trends
- temperature/climate change
- national generation and useage
- innovations

