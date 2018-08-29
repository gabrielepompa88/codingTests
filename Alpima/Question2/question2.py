#import sys
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
 

def plot_dr_ratio(portfolio_index, dr, figure_file_path=None):
    """
	:param portfolio_index: pandas Dataframe object of the portfolio index
	:param dr: pandas Dataframe object of the DR ratio
    :param figure_file_path: path to the figure file (default=None). 
                             If None, the figure is printed on screen.

    
    :return: None.
	"""
	
    fig, ax1 = plt.subplots(figsize=(9,6))
    
    idx = portfolio_index.index

    ax1.plot(idx, dr.values, 'b-')
    ax1.set_xlabel('Date')
    
    # Make the y-axis label, ticks and tick labels match the line color.
    ax1.set_ylabel('Diversification Ratio', color='b')
    ax1.tick_params('y', colors='b')
    
    ax2 = ax1.twinx()
    ax2.plot(idx, portfolio_index.values, 'r-')
    ax2.set_ylabel('Portfolio Index', color='r')
    ax2.tick_params('y', colors='r')
    
    fig.tight_layout()
    
    if figure_file_path:
        fig.savefig(figure_file_path, dpi=fig.dpi)
    else:
        plt.show()

def rolling_dr_ratio(df, rolling_window_size=200, figure_file_path=None):
    """
	calculates and plots the dr ratio.
	
    :param df: the dataframe contains the daily total return price change, the weights and the portfolio index.
    :param rolling_window_size: default to 200 days.
    :param figure_file_path: path to the figure file (default=None). 
                             If None, the figure is only printed on screen.
    
    :return: None.
    """
    
    # compute rolling asset std-dev
    rollingStdDev = df['TR_Change'][:].rolling(rolling_window_size).std()
    
    df = df.join(pd.DataFrame(rollingStdDev.values, 
                              columns=pd.MultiIndex.from_product([['Rolling_StdDev'],['Asset_1', 'Asset_2', 'Asset_3', 'Asset_4']]), 
                              index=df.index))

    # compute rolling asset covariance matrix
    rollingCov = df['TR_Change'][:].rolling(rolling_window_size).cov()

    # compute rolling weighted average of asset std-dev
    df['Rolling_StdDev','weightedAverage'] = [np.dot(df.loc[t,'Weight'].values, 
                                                     df.loc[t,'Rolling_StdDev'].values)
                                              for t in df.index]
    # compute rolling portfolio std-dev
    df['Rolling_StdDev','Portfolio'] = [np.sqrt(np.dot(df.loc[t,'Weight'].values, 
                                                       np.dot(rollingCov.loc[t,:].values, df.loc[t,'Weight'].values))) 
                                        for t in df.index]


    # calculate the rolling DR ratio (source: http://www.tobam.fr/wp-content/uploads/2014/12/TOBAM-JoPM-Maximum-Div-2008.pdf)
    dr = df['Rolling_StdDev','weightedAverage'] / df['Rolling_StdDev','Portfolio']

    # plot index and the rolling dr
    plot_dr_ratio(df["Portfolio_Index"], dr, figure_file_path)


if __name__ == "__main__":
    
    df = pd.read_csv("./dr.csv", header=[0,1], index_col=0, parse_dates=True)
    
    rolling_dr_ratio(df, figure_file_path="./DR_with_PortfolioIndex.png")