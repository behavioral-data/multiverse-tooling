"""
Quick script to convert the nlsw88.dta file to csv file 
"""

import pandas as pd

if __name__ == "__main__":
    df = pd.read_stata('nlsw88.dta')
    df.to_csv('union_wage.csv', index=False)