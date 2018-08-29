import numpy as np
import pandas as pd

def same_timeseries(ts1, ts2):
    """
    return True if timeseries ts1 == timeseries ts2.

    :param ts1: pandas Series object
    :param ts2: pandas Series object
    
    :return: True if ts1 and ts2 are at least identical (Allowed Difference - 0.00001).
    """
    
    if len(ts1) == len(ts2):
        # this will skip from the counting dates in which one (or both) ts are NaN
        return np.nansum(ts1.values - ts2.values) < 10**-5
    else:
        return False

    
def find_differences(bbg_df, quandl_df, quandl_to_bbg_ticker_map, csv_file_path=None,
                     equalOverCommonDateRange=False):
    """
    prints or saves to csv the differences between two timeseries files.

    :param bbg_df: pandas Dataframe object
    :param quandl_df: pandas Dataframe object
    :param quandl_to_bbg_ticker_map: dictionary {key: Quandl ticker; value: BBG ticker}
    :param csv_file_path: path to save the output csv file (default=None)
        If csv_file_path is not None, will save the output to a csv file.
    :param equalOverCommonDateRange: bool. If true, also a commonEndDate is considered 
        and equality of the two time series is evaluated over the common date range [commonStartDate, commonEndDate]

    :return: None.

    for each ticker find the start date of data from both sources,
    and prints True/False if prices series match since the common start date.

    Compare (BBG 'price' to quandl 'close price')

    CSV output example:
    
        Ticker, Quandl Start Date, BBG Start Date, Match since common start date?
        DOC US Equity ,2000-01-01, 1990-01-01, True
        ABO US Equity ,1999-01-01, 1990-01-01, False
        ...
        ...
        ...
        ABO US Equity ,1999-01-01, 1990-01-01, False
    
    """
    
    # write your code here.
      
    # set desired fields as columns of the result pd.DataFrame
    columns = ['Ticker', 'Quandl Start Date', 'BBG Start Date', 
               'Match since common start date?']
    
    # if the equality is checked over [commonStartDate, commonEndDate], 
    # the two end dates are added as additional informations
    if equalOverCommonDateRange:
        tmp = columns.pop()
        columns += ['Quandl End Date', 'BBG End Date', tmp]
        
    result = pd.DataFrame(columns=columns)
    
    # fill the Ticker column with Quandls tickers
    result['Ticker'] = quandl_df.columns.levels[0] #quandl_to_bbg_ticker_map.keys()
    
    # convert string index to datetime index to ease the comparison
    quandl_df.index = pd.to_datetime(quandl_df.index, format = '%Y-%m-%d')
    bbg_df.index = pd.to_datetime(bbg_df.index, format = '%Y-%m-%d')
    
    # fill the other columns
    for quandlTicker in result['Ticker']:
        
        # find Quandl start date
        quandlStartDate = quandl_df[quandlTicker]['Close'].first_valid_index()
        
        # find BBG ticker and check whether BBG data are avialable
        bbgTicker = quandl_to_bbg_ticker_map[quandlTicker]
        
        # if BBG provides data for the considered ticker, then check ts difference
        if bbgTicker in bbg_df.columns.levels[0]:
            
            bbgStartDate = bbg_df[bbgTicker]['price'].first_valid_index() 
            
            # update result file
            result.loc[result['Ticker'] == quandlTicker, ['Quandl Start Date', 'BBG Start Date']] = [quandlStartDate.strftime('%Y-%m-%d'), bbgStartDate.strftime('%Y-%m-%d')]
           
            # find commond start date
            commonStartDate = max(quandlStartDate, bbgStartDate)
            
            # check equality of the two series between commonStartDate and commonEndDate
            if equalOverCommonDateRange:
                
                # find Quandl and BBG end dates
                quandlEndDate = quandl_df[quandlTicker]['Close'].last_valid_index()
                bbgEndDate = bbg_df[bbgTicker]['price'].last_valid_index() 

                # update result file
                result.loc[result['Ticker'] == quandlTicker, ['Quandl End Date', 'BBG End Date']] = [quandlEndDate.strftime('%Y-%m-%d'), bbgEndDate.strftime('%Y-%m-%d')]

                # find common start date
                commonEndDate = min(quandlEndDate, bbgEndDate)
                
                # Quandl and BBG time series
                tsQuandl = quandl_df[quandlTicker]['Close'][commonStartDate:commonEndDate]
                tsBbg = bbg_df[bbgTicker]['price'][commonStartDate:commonEndDate]
                
                # align time series over the union of their indexes (filling with NaN when needed)
                tsQuandl, tsBbg = tsQuandl.align(tsBbg)
                                   
            # check equality of the two series from the commonStartDate
            else:
                
                tsQuandl = quandl_df[quandlTicker]['Close'][commonStartDate:]
                tsBbg = bbg_df[bbgTicker]['price'][commonStartDate:]
            
            # check equality
            result.loc[result['Ticker'] == quandlTicker, 'Match since common start date?'] = same_timeseries(tsQuandl, tsBbg) 
        
                
        # if BBG doesn't provide any data for the considered ticker, then skip it.         
        else:

            result.loc[result['Ticker'] == quandlTicker, 
                       ['Quandl Start Date', 'BBG Start Date', 'Match since common start date?']] = \
                       [quandlStartDate.strftime('%Y-%m-%d'), "No data available for BBG ticker "+bbgTicker, "NA"]
            
    # save csv if file path was specified:
    if csv_file_path:
        result.to_csv(csv_file_path, index=False)
    
    else:
        print(result)

if __name__== "__main__":
    
    import csv 
    
    bbg_df = pd.read_csv("./bbg_data_final.csv", header=[0,1], index_col=0)
    quandl_df = pd.read_csv("./quandl_data_final.csv", header=[0,1], index_col=0)
    
    # read the mapping table which maps each Quandls ticker into the corresponding bbg one
    with open("./match_final.csv", 'r') as infile:
        quandl_to_bbg_ticker = {rows[0]: rows[1] for rows in csv.reader(infile)} 
        
    # check equality of the two time-series from the common starting date
    outputFile = "./output.csv" #"./output_commonDateRange.csv"        
    find_differences(bbg_df, quandl_df, quandl_to_bbg_ticker, outputFile,
                     equalOverCommonDateRange=False)
    