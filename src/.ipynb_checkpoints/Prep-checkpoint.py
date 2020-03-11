import numpy as np
import pandas as pd
import cpi
import sys
import matplotlib.pyplot as plt

file_path_1 = '/Users/jenniferpaige/Desktop/TTS_10-Dec-2019_p1.csv'
file_path_2 = '/Users/jenniferpaige/Desktop/TTS_10-Dec-2019_p2.csv'

def prep():
    
    print("1 of 11 |    Reading in first dataset. \n             Using 4/60 features/columns: 'Installation Date', 'System Size', 'Total Installed Price' , 'Customer Segment' \n             Changing -9999 values to null")
    dfMod1 = pd.read_csv(file_path_1,
                    encoding='iso-8859-1',
                    parse_dates=['Installation Date'], 
                    usecols=['Installation Date', 'System Size','Total Installed Price' , 'Customer Segment'], 
                    na_values=(-9999, '-9999'))

    print("2 of 11 |    Reading in second dataset. \n             Using 4/60 features/columns: 'Installation Date', 'System Size', 'Total Installed Price' , 'Customer Segment' \n             Changing -9999 values to null")
    dfMod2 = pd.read_csv(file_path_2,
                    encoding='iso-8859-1',
                    parse_dates=['Installation Date'], 
                    usecols=['Installation Date', 'System Size', 'Total Installed Price' , 'Customer Segment'], 
                    na_values=(-9999, '-9999'))
    
    print('3 of 11 |    Concatenating datasets together')
    # concat together  
    dfMod = pd.concat([dfMod1,dfMod2], ignore_index=True)

    # Create initial copy 
    df = dfMod.copy()

    print('4 of 11 |    Cleaning up column names')
    # Lowercase and replace all spaces with underscores
    df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('(', '').str.replace(')', '')
    
    print('5 of 11 |    Sorting values by installation_date')
    #sort by date
    df.sort_values('installation_date', inplace=True)
    
    print('6 of 11 |    Assigning installation_date as index')
    #Assign the date as the index
    df.set_index('installation_date', drop=True, inplace=True)
    
    print('7 of 11 |    Refining to only RES customer_segment')
    # Residential is 95% of the data. 
    # Focus on those to eliminate any irregularity  
    df = df.loc[df['customer_segment']=='RES']
    
    print('8 of 11 |    Replacing all null values with median values from same year')
    # The Number of null price cells / total number of price cells
    # 356171/1543831 = more than 20% 
    # Replace all -9999/null values with the median from that year 
    [df['total_installed_price'].replace(np.nan, 
                                         round(df.loc[(df['total_installed_price'] != np.nan) & 
                                        (df.index.year == i)]['total_installed_price'].median(),2), 
                                        inplace=True) for i in range(1998,2019)] 
    
    print('9 of 11 |    Adusting prices for inflation')
    #adjust all prices to reflect inflation of the current year(2019)
    df['date'] = df.index.date
    df['adj_installed_price'] = round(df.apply(lambda x: cpi.inflate(x.total_installed_price, x.date), axis=1),2)
    

    print('10 of 11|    Creating target variable: cost_per_watt')
    # create target variable, cost_per_watt 
    df['cost_per_watt'] = round(df['adj_installed_price']/ df['system_size']/1000,2)
    
    
    print("11 of 11|    Removing > 1600 outliers above $25 per watt") 
    # remove > 1600 outlier observations
    df = df.loc[df.cost_per_watt < 25]

    
    print('Prep complete \n ------------------------------------------------------------')
    
    print('MAX PRICE \n total            $',  df['adj_installed_price'].max(), '\n cost per watt    $',  df['cost_per_watt'].max())
    print('MEAN PRICE \n total            $', round( df['adj_installed_price'].mean(),2), '\n cost per watt    $', round( df['cost_per_watt'].mean(),2))
    print('MEDIAN PRICE \n total            $',  df['adj_installed_price'].median(), '\n cost per watt    $',  df['cost_per_watt'].median())
    print('MODE PRICE \n total            $',  df['adj_installed_price'].mode()[0], '\n cost per watt    $',  df['cost_per_watt'].mode()[0])
    print('MIN PRICE \n total            $',  df['adj_installed_price'].min(), '\n cost per watt    $',  df['cost_per_watt'].min())
    
    df.cost_per_watt.plot(title=('Cost per Watt'))
    plt.show()
    df.adj_installed_price.plot(title=('Total Installed Price (Adjusted for Inflation)'))
    return df