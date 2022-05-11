"""
Quick script to convert the migration.dta file to csv file
"""

import pandas as pd

if __name__ == "__main__":
    df = pd.read_stata('migration.dta')
    df.to_csv('tax_induced_migration.csv', index=False)