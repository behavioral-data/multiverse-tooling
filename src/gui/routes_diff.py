from . import app_diff, app_error_dashboard
from flask import jsonify, render_template, request
import os.path as osp
from src.gui.monaco_diff import TemplateDiffView

@app_diff.route('/')
def index():
    if not hasattr(app_diff, 'diff_view') or app_diff.diff_view is None:
        return app_diff.send_static_file('monaco.html')
    diff_view: TemplateDiffView = app_diff.diff_view
    univese_file_name = 'New ' + osp.basename(diff_view.dst_file)
    template_file_name = osp.basename(diff_view.template_diff.boba_parser.fn_script)
    old_template_name = 'Old ' + template_file_name
    new_template_name = 'New ' + template_file_name
    return render_template('index.html', 
                           new_universe_fname=univese_file_name,
                           old_template_name=old_template_name,
                           new_template_name=new_template_name,
                           js_config=diff_view.get_all_config())
    
@app_diff.route('/save-editor', methods=['GET', 'POST'])
def save_editor():
    print(request.form)
    if not hasattr(app_diff, 'diff_view'):
        print(f"Editor Text:\n{request.form.get('editor_text')}")
        ret_text = 'Testing so nothing is saved'
    else:
        diff_view: TemplateDiffView = app_diff.diff_view
        save_path = diff_view.template_diff.boba_parser.fn_script
        with open(save_path, 'w') as f:
            f.write(request.form.get('editor_text'))
        ret_text = 'Saved new template to ' + save_path
            
    return jsonify({'result': 'OK', 'returnText': ret_text})  


@app_diff.route('/old_universe')
def old_universe():
    diff_view: TemplateDiffView = app_diff.diff_view
    return diff_view.template_diff.src_code

@app_diff.route('/new_universe')
def new_universe():
    diff_view: TemplateDiffView = app_diff.diff_view
    return diff_view.template_diff.dst_code

@app_diff.route('/old_template')
def old_template():
    diff_view: TemplateDiffView = app_diff.diff_view
    return diff_view.template_diff.template_code

@app_diff.route('/new_template')
def new_template():
    diff_view: TemplateDiffView = app_diff.diff_view
    return diff_view.template_diff.template_builder.new_template_code_pos.template_code_str

@app_diff.route('/editor')
def editor():
    diff_view: TemplateDiffView = app_diff.diff_view
    return diff_view.template_diff.template_builder.new_template_code_pos.template_code_str


@app_diff.route('/test_new_universe')
def test_new_universe():
    return '#!/usr/bin/env python3\n\nimport numpy as np\nimport statsmodels.api as sm2\nimport statsmodels.formula.api as smf\n\nif __name__ == \'__main__\':\n\t# read data file\n\tdf = pd.read_csv(\'/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/fertility/durante_etal_2013_study1.txt\', delimiter=\'\\t\')\n\n\t# remove NA\n\tdf = df.dropna(subset=[\'rel1\', \'rel2\', \'rel3\', \'rel4\'])\n\n\t# create religiosity score\n\tdf[\'rel_comp\'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)\n\n\t# next menstrual onset (nmo) assessment\n\tdf.last_period_start = pd.to_datetime(df.last_period_start)\n\tdf.period_before_last_start = pd.to_datetime(df.period_before_last_start)\n\tdf.date_testing = pd.to_datetime(df.date_testing)\n\n\t# first nmo option: based on computed cycle length\n\tnext_onset = df.last_period_start + cl\n\tdf[\'computed_cycle_length\'] = (cl / np.timedelta64(1, \'D\')).astype(int)\n\n\t# compute cycle day\n\tdf[\'cycle_day\'] = pd.Timedelta(\'28 days\') - (next_onset - df.date_testing)\n\tdf.cycle_day = (df.cycle_day / np.timedelta64(1, \'D\')).astype(int)\n\tdf.cycle_day = np.clip(df.cycle_day, 1, 28)\n\n\t# relationship status assessment\n\t# single = response options 1 and 2; relationship = response options 3 and 4\n\tdf.loc[df.relationship <= "[2, 4]"[0],\n\t\t\'relationship_status\'] = \'Single\'\n\tdf.loc[df.relationship >= "[2, 5]"[1],\n\t\t\'relationship_status\'] = \'Relationship\'\n\t\n\t# fertility assessment\n\thigh_bounds = [[9, 17], [13, 25], [18, 25], [4,1]][0]\n\tlow_bounds1 = [[9, 17], [13, 25], [18, 25], [4,1]][1]\n\tlow_bounds2 = [[9, 17], [13, 25], [18, 25], [4,1]][2]\n\tdf.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),\n\t\t\'fertility\'] = \'High\'\n\tdf.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),\n\t\t\'fertility\'] = \'Low\'\n\tdf.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),\n\t\t\'fertility\'] = \'Low\'\n\n\n\n\t# exclusion based on certainty ratings\n\tdf = df[(df.sure1 >= 6) & (df.sure2 >= 6)]\n\n\t# perform an ANOVA on the processed data set\n\tlm = smf.ols(\'rel_comp ~ relationship_status "[2, 3]" * fertility\', data=df).fit()\n\ttable = sm.stats.anova_lm(lm, typ=2)\n\tprint(table)\n'

@app_diff.route('/test_old_template')
def test_old_template():
    return '#!/usr/bin/env python3\n\nimport numpy as np\nimport pandas as pd\nimport statsmodels.api as sm\nimport statsmodels.formula.api as smf\n# --- (BOBA_CONFIG)\n{\n  "graph": [\n\t"NMO1->ECL1->A",\n\t"NMO2->ECL2->A",\n\t"NMO1->A",\n\t"NMO2->A",\n\t"A->B",\n\t"A->EC->B"\n  ],\n  "decisions": [\n\t{"var": "fertility_bounds", "options": [\n\t  [[7, 14], [17, 25], [17, 25]],\n\t  [[6, 14], [17, 27], [17, 27]],\n\t  [[9, 17], [18, 25], [18, 25]],\n\t  [[8, 14], [1, 7], [15, 28]],\n\t  [[9, 17], [1, 8], [18, 28]]\n\t]},\n\t{"var": "relationship_bounds",\n\t  "options": ["\\"[2, 3]\\"", "[1,4]", "[3,5]"]}\n  ],\n  "before_execute": "cp ../durante_etal_2013_study1.txt ./code/"\n}\n# --- (END)\n\nif __name__ == \'__main__\':\n\t# read data file\n\tdf = pd.read_csv(\'/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/fertility/durante_etal_2013_study1.txt\', delimiter=\'\\t\')\n\n\t# remove NA\n\tdf = df.dropna(subset=[\'rel1\', \'rel2\', \'rel3\'])\n\n\t# create religiosity score\n\tdf[\'rel_comp\'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)\n\n\t# next menstrual onset (nmo) assessment\n\tdf.last_period_start = pd.to_datetime(df.last_period_start)\n\tdf.period_before_last_start = pd.to_datetime(df.period_before_last_start)\n\tdf.date_testing = pd.to_datetime(df.date_testing)\n\n\t# --- (NMO1)\n\t# first nmo option: based on computed cycle length\n\tcl = df.last_period_start - df.period_before_last_start\n\tnext_onset = df.last_period_start + cl\n\tdf[\'computed_cycle_length\'] = (cl / np.timedelta64(1, \'D\')).astype(int)\n\n\t# --- (NMO2)\n\t# second nmo option: based on reported cycle length\n\tdf = df.dropna(subset=[\'reported_cycle_length\'])\n\tnext_onset = df.last_period_start + df.reported_cycle_length.apply(\n\t lambda a: pd.Timedelta(days=a))\n\n\t# --- (ECL1)\n\t# exclusion based on computed cycle length\n\tdf = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]\n\n\t# --- (ECL2)\n\t# exclusion based on reported cycle length\n\tdf = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]\n\n\t# --- (A)\n\t# compute cycle day\n\tdf[\'cycle_day\'] = pd.Timedelta(\'28 days\') - (next_onset - df.date_testing)\n\tdf.cycle_day = (df.cycle_day / np.timedelta64(1, \'D\')).astype(int)\n\tdf.cycle_day = np.clip(df.cycle_day, 1, 28)\n\n\t# relationship status assessment\n\t# single = response options 1 and 2; relationship = response options 3 and 4\n\tdf.loc[df.relationship <= {{relationship_bounds}}[0],\n\t\t\'relationship_status\'] = \'Single\'\n\tdf.loc[df.relationship >= {{relationship_bounds}}[1],\n\t\t\'relationship_status\'] = \'Relationship\'\n\t\n\t# fertility assessment\n\thigh_bounds = {{fertility_bounds}}[0]\n\tlow_bounds1 = {{fertility_bounds}}[1]\n\tlow_bounds2 = {{fertility_bounds}}[2]\n\tdf.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),\n\t\t\'fertility\'] = \'High\'\n\tdf.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),\n\t\t\'fertility\'] = \'Low\'\n\tdf.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),\n\t\t\'fertility\'] = \'Low\'\n\n\n\n\t# --- (EC)\n\t# exclusion based on certainty ratings\n\tdf = df[(df.sure1 >= 6) & (df.sure2 >= 6)]\n\n\t# --- (B)\n\t# perform an ANOVA on the processed data set\n\tlm = smf.ols(\'rel_comp ~ relationship_status {{relationship_bounds}} * fertility\', data=df).fit()\n\ttable = sm.stats.anova_lm(lm, typ=2)\n\tprint(table)\n'

@app_diff.route('/test_new_template')
def test_new_template():
    return '#!/usr/bin/env python3\n\nimport numpy as np\nimport statsmodels.api as sm2\nimport statsmodels.formula.api as smf\n# --- (BOBA_CONFIG)\n{\n  "graph": [\n\t"NMO1->ECL1->A",\n\t"NMO2->ECL2->A",\n\t"NMO1->A",\n\t"NMO2->A",\n\t"A->B",\n\t"A->EC->B"\n  ],\n  "decisions": [\n\t{"var": "fertility_bounds", "options": [\n\t  [[7, 14], [17, 25], [17, 25]],\n\t  [[6, 14], [17, 27], [17, 27]],\n\t  [[9, 17], [13, 25], [18, 25], [4, 1]],\n\t  [[8, 14], [1, 7], [15, 28]],\n\t  [[9, 17], [1, 8], [18, 28]]\n\t]},\n\t{"var": "relationship_bounds",\n\t  "options": ["[2, 5]", "[1,4]", "[3,5]"]}\n  ],\n  "before_execute": "cp ../durante_etal_2013_study1.txt ./code/"\n}\n# --- (END)\n\nif __name__ == \'__main__\':\n\t# read data file\n\tdf = pd.read_csv(\'/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/fertility/durante_etal_2013_study1.txt\', delimiter=\'\\t\')\n\n\t# remove NA\n\tdf = df.dropna(subset=[\'rel1\', \'rel2\', \'rel3\', \'rel4\'])\n\n\t# create religiosity score\n\tdf[\'rel_comp\'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)\n\n\t# next menstrual onset (nmo) assessment\n\tdf.last_period_start = pd.to_datetime(df.last_period_start)\n\tdf.period_before_last_start = pd.to_datetime(df.period_before_last_start)\n\tdf.date_testing = pd.to_datetime(df.date_testing)\n\n\t# --- (NMO1)\n\t# first nmo option: based on computed cycle length\n\tnext_onset = df.last_period_start + cl\n\tdf[\'computed_cycle_length\'] = (cl / np.timedelta64(1, \'D\')).astype(int)\n\n\t# --- (NMO2)\n\t# second nmo option: based on reported cycle length\n\tdf = df.dropna(subset=[\'reported_cycle_length\'])\n\tnext_onset = df.last_period_start + df.reported_cycle_length.apply(\n\t lambda a: pd.Timedelta(days=a))\n\n\t# --- (ECL1)\n\t# exclusion based on computed cycle length\n\tdf = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]\n\n\t# --- (ECL2)\n\t# exclusion based on reported cycle length\n\tdf = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]\n\n\t# --- (A)\n\t# compute cycle day\n\tdf[\'cycle_day\'] = pd.Timedelta(\'28 days\') - (next_onset - df.date_testing)\n\tdf.cycle_day = (df.cycle_day / np.timedelta64(1, \'D\')).astype(int)\n\tdf.cycle_day = np.clip(df.cycle_day, 1, 28)\n\n\t# relationship status assessment\n\t# single = response options 1 and 2; relationship = response options 3 and 4\n\tdf.loc[df.relationship <= {{relationship_bounds}}[0],\n\t\t\'relationship_status\'] = \'Single\'\n\tdf.loc[df.relationship >= {{relationship_bounds}}[1],\n\t\t\'relationship_status\'] = \'Relationship\'\n\t\n\t# fertility assessment\n\thigh_bounds = {{fertility_bounds}}[0]\n\tlow_bounds1 = {{fertility_bounds}}[1]\n\tlow_bounds2 = {{fertility_bounds}}[2]\n\tdf.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),\n\t\t\'fertility\'] = \'High\'\n\tdf.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),\n\t\t\'fertility\'] = \'Low\'\n\tdf.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),\n\t\t\'fertility\'] = \'Low\'\n\n\n\n\t# --- (EC)\n\t# exclusion based on certainty ratings\n\tdf = df[(df.sure1 >= 6) & (df.sure2 >= 6)]\n\n\t# --- (B)\n\t# perform an ANOVA on the processed data set\n\tlm = smf.ols(\'rel_comp ~ relationship_status "[2, 3]" * fertility\', data=df).fit()\n\ttable = sm.stats.anova_lm(lm, typ=2)\n\tprint(table)\n'

@app_diff.route('/test_editor')
def test_editor():
    return '#!/usr/bin/env python3\n\nimport numpy as np\nimport statsmodels.api as sm2\nimport statsmodels.formula.api as smf\n# --- (BOBA_CONFIG)\n{\n  "graph": [\n\t"NMO1->ECL1->A",\n\t"NMO2->ECL2->A",\n\t"NMO1->A",\n\t"NMO2->A",\n\t"A->B",\n\t"A->EC->B"\n  ],\n  "decisions": [\n\t{"var": "fertility_bounds", "options": [\n\t  [[7, 14], [17, 25], [17, 25]],\n\t  [[6, 14], [17, 27], [17, 27]],\n\t  [[9, 17], [13, 25], [18, 25], [4, 1]],\n\t  [[8, 14], [1, 7], [15, 28]],\n\t  [[9, 17], [1, 8], [18, 28]]\n\t]},\n\t{"var": "relationship_bounds",\n\t  "options": ["[2, 5]", "[1,4]", "[3,5]"]}\n  ],\n  "before_execute": "cp ../durante_etal_2013_study1.txt ./code/"\n}\n# --- (END)\n\nif __name__ == \'__main__\':\n\t# read data file\n\tdf = pd.read_csv(\'/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/fertility/durante_etal_2013_study1.txt\', delimiter=\'\\t\')\n\n\t# remove NA\n\tdf = df.dropna(subset=[\'rel1\', \'rel2\', \'rel3\', \'rel4\'])\n\n\t# create religiosity score\n\tdf[\'rel_comp\'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)\n\n\t# next menstrual onset (nmo) assessment\n\tdf.last_period_start = pd.to_datetime(df.last_period_start)\n\tdf.period_before_last_start = pd.to_datetime(df.period_before_last_start)\n\tdf.date_testing = pd.to_datetime(df.date_testing)\n\n\t# --- (NMO1)\n\t# first nmo option: based on computed cycle length\n\tnext_onset = df.last_period_start + cl\n\tdf[\'computed_cycle_length\'] = (cl / np.timedelta64(1, \'D\')).astype(int)\n\n\t# --- (NMO2)\n\t# second nmo option: based on reported cycle length\n\tdf = df.dropna(subset=[\'reported_cycle_length\'])\n\tnext_onset = df.last_period_start + df.reported_cycle_length.apply(\n\t lambda a: pd.Timedelta(days=a))\n\n\t# --- (ECL1)\n\t# exclusion based on computed cycle length\n\tdf = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]\n\n\t# --- (ECL2)\n\t# exclusion based on reported cycle length\n\tdf = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]\n\n\t# --- (A)\n\t# compute cycle day\n\tdf[\'cycle_day\'] = pd.Timedelta(\'28 days\') - (next_onset - df.date_testing)\n\tdf.cycle_day = (df.cycle_day / np.timedelta64(1, \'D\')).astype(int)\n\tdf.cycle_day = np.clip(df.cycle_day, 1, 28)\n\n\t# relationship status assessment\n\t# single = response options 1 and 2; relationship = response options 3 and 4\n\tdf.loc[df.relationship <= {{relationship_bounds}}[0],\n\t\t\'relationship_status\'] = \'Single\'\n\tdf.loc[df.relationship >= {{relationship_bounds}}[1],\n\t\t\'relationship_status\'] = \'Relationship\'\n\t\n\t# fertility assessment\n\thigh_bounds = {{fertility_bounds}}[0]\n\tlow_bounds1 = {{fertility_bounds}}[1]\n\tlow_bounds2 = {{fertility_bounds}}[2]\n\tdf.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),\n\t\t\'fertility\'] = \'High\'\n\tdf.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),\n\t\t\'fertility\'] = \'Low\'\n\tdf.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),\n\t\t\'fertility\'] = \'Low\'\n\n\n\n\t# --- (EC)\n\t# exclusion based on certainty ratings\n\tdf = df[(df.sure1 >= 6) & (df.sure2 >= 6)]\n\n\t# --- (B)\n\t# perform an ANOVA on the processed data set\n\tlm = smf.ols(\'rel_comp ~ relationship_status "[2, 3]" * fertility\', data=df).fit()\n\ttable = sm.stats.anova_lm(lm, typ=2)\n\tprint(table)\n'
