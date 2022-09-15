import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

df = pd.read_csv('boba/example/hurricane/multiverse/data_cleaned.csv')
formula= 'log_death ~ feminity + damage + zcat + feminity:damage + feminity:zcat + year:damage'
model = smf.ols(formula=formula, data=df).fit()

sigma = np.sqrt(model.scale)
dof_resid = model.df_resid
pred_summary_df = model.get_prediction(df).summary_frame()[['mean', 'mean_se']]
se_residual = np.sqrt(model.scale)

print('here')