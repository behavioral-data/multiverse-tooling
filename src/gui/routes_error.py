from . import app_diff, app_error_dashboard
from flask import jsonify, render_template, request
import os.path as osp
import pandas as pd
@app_error_dashboard.route('/')
def index():
    errors = app_error_dashboard.aggr_error.return_json_errors(is_warning=False)
    lang = app_error_dashboard.aggr_error.lang.lang[0]
    file_watch = app_error_dashboard.aggr_error.file_log
    progress = len(pd.read_csv(file_watch))
    total = len(app_error_dashboard.aggr_error.summary_df)
    if len(errors) == 0:
        return render_template('error_no_errors.html',
                               progress_val=(progress/total) * 100, 
                               progress_str=f"Ran {progress} out of {total} universes")
    else:
        return render_template('error_index.html', errors=errors, lang=lang,
                               progress_val=(progress/total) * 100, progress_str=f"Ran {progress} out of {total} universes")

@app_error_dashboard.route('/warnings')
def warnings():
    errors = app_error_dashboard.aggr_error.return_json_errors(is_warning=True)
    lang = app_error_dashboard.aggr_error.lang.lang[0]
    file_watch = app_error_dashboard.aggr_error.file_log
    progress = len(pd.read_csv(file_watch))
    total = len(app_error_dashboard.aggr_error.summary_df)
    if len(errors) == 0:
        return render_template('warning_no_errors.html',
                               progress_val=(progress/total) * 100, 
                               progress_str=f"Ran {progress} out of {total} universes")
    else:
        return render_template('warning.html', errors=errors, lang=lang,
                               progress_val=(progress/total) * 100, 
                               progress_str=f"Ran {progress} out of {total} universes")