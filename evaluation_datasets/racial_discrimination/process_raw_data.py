"""
Quick script that follows '(1) Bertrand Mullainathan - Getting data ready - 2015 02 18.do'
to process the raw "lakisha_aer.dta".

Original code from: https://osf.io/9rvps/ 
"""
import pandas as pd
import statsmodels.formula.api as smf


def get_predictions(df_first_half, df_second_half, formula):
    # predict 2nd half with first half
    model = smf.probit(formula=formula, data=df_first_half)
    probit_model = model.fit()

    qall2 = probit_model.predict(df_second_half)
    # Predict 1st half with 2nd half
    model = smf.probit(formula=formula, data=df_second_half)
    probit_model = model.fit()

    qall1 = probit_model.predict(df_first_half)
    
    return pd.concat([qall1, qall2])

def get_predictions_race(df_first_half_race, df_second_half_race, df_first_half, df_second_half, formula):
    # predict 2nd half with first half
    model = smf.probit(formula=formula, data=df_first_half_race)
    probit_model = model.fit()

    qall2 = probit_model.predict(df_second_half)
    # Predict 1st half with 2nd half
    model = smf.probit(formula=formula, data=df_second_half_race)
    probit_model = model.fit()

    qall1 = probit_model.predict(df_first_half)
    
    return pd.concat([qall1, qall2])

if __name__ == "__main__":
    df = pd.read_stata('lakisha_aer.dta')

    # *1) Dummies for black, female, administrative, boston, college

    df['black'] = df['race'].apply(lambda x: 1 if x == "b" else 0)
    df["female"] = df["sex"].apply(lambda x: 1 if x == "f" else 0)
    df["adm"] = df["kind"].apply(lambda x: 1 if x == "a" else 0)
    df["boston"] = df["city"].apply(lambda x: 1 if x == "b" else 0)
    df["college"] = df["education"].apply(lambda x: 1 if x == "4" else 0)

    # *2) Standardize years of experience

    df["zyearsexp"] = (df["yearsexp"] - df["yearsexp"].mean()) / df["yearsexp"].std()
    df["zofjobs"] = (df["ofjobs"] - df["ofjobs"].mean()) / df["ofjobs"].std()


    #*3) Refer to all predictors for the 1st stage with a single macro: $xb
    predictors_1st_stage = ["female", "boston", "occupbroad", "req", "expreq", 
                            "comreq", "educreq", "compreq", "orgreq"]

    #*4) Simple Sum of quality indicators 
    cols = ["college", "zyearsexp", "volunteer", "military", 
            "email", "empholes", "workinschool", "honors", "computerskills", "specialskills"]
    df["sumq"] = df[cols].sum(axis=1)
    df["zsumq"] = (df["sumq"] - df["sumq"].mean()) / df["sumq"].std()

    #*5) Median split on sumq
    median = df["sumq"].median()
    df["sumq_med"] = df["sumq"].apply(lambda x: 1 if x > median else 0)

    #*6) Create quality_ based on subsets
    df_first_half = df.sample(frac = 0.5, random_state=5)
    df_second_half = df.drop(df_first_half.index)

    df_first_half["half"] = 1
    df_second_half["half"] = 2


    df = pd.concat([df_first_half, df_second_half])
    
    
    # *6.1) Using All (blacks and whites) without covariates

    formula = 'call ~ yearsexp + empholes + email + computerskills + specialskills + honors + volunteer + military + workinschool'
    df['qall'] = get_predictions(df_first_half, df_second_half, formula)
    df['qall'].describe() 
    
    # *6.2) Using All (blacks and whites) WITH covariates
    formula2 = formula + ' + ' + ' + '.join(predictors_1st_stage)
    df['qallxb'] = get_predictions(df_first_half, df_second_half, formula)
    df['qallxb'].describe()
    
    
    #*(6.3) Using Blacks only without covariates
    #*(6.4) Using Blacks only WITH covariates
    #*(6.5) Using whites only without covariates
    #*(6.6) Using whites only WITH covariates


    df_black = df[(df.black == 1)]
    df_white = df[(df.black == 0)]
    df_black_first_half = df_black[df.half == 1]
    df_black_second_half = df_black[df.half == 2]
    df_white_first_half = df_white[(df.half == 1)]
    df_white_second_half = df_white[df.half == 2]

    len1 = len(df_black_first_half) + len(df_black_second_half) + len(df_white_first_half) + len(df_white_second_half)
    assert(len1 == len(df))

    df['qblack'] = get_predictions_race(df_black_first_half, df_black_second_half, df_first_half, df_second_half, formula)
    df['qblackxb'] = get_predictions_race(df_black_first_half, df_black_second_half, df_first_half, df_second_half, formula2)
    df['qwhite'] = get_predictions_race(df_white_first_half, df_white_second_half, df_first_half, df_second_half, formula)
    df['qwhitexb'] = get_predictions_race(df_white_first_half, df_white_second_half, df_first_half, df_second_half, formula2)
    
    #*7) Create median splits for q-hat
    qall_med = df['qall'].median()
    qallxb_med = df['qallxb'].median()
    qblack_med = df['qblack'].median()
    qblackxb_med = df['qblackxb'].median()
    qwhite_med = df['qwhite'].median()
    qwhitexb_med = df['qwhitexb'].median()

    df['qall_med'] = df['qall'].apply(lambda x: 1 if x > qall_med else 0)
    df['qallxb_med'] = df['qallxb'].apply(lambda x: 1 if x > qallxb_med else 0)
    df['qblack_med'] = df['qblack'].apply(lambda x: 1 if x > qblack_med else 0)
    df['qblackxb_med'] = df['qblackxb'].apply(lambda x: 1 if x > qblackxb_med else 0)
    df['qwhite_med'] = df['qwhite'].apply(lambda x: 1 if x > qwhite_med else 0)
    df['qwhitexb_med'] = df['qwhitexb'].apply(lambda x: 1 if x > qwhitexb_med else 0)
    
    
    # Write df to file
    df.to_csv('processed_racial_discrimination.csv')