from . import app_diff, app_error_dashboard
from flask import jsonify, render_template, request


@app_error_dashboard.route('/')
def index():
    errors = app_error_dashboard.aggr_error.return_json_errors(is_warning=False)
    lang = app_error_dashboard.aggr_error.lang.lang[0]
    print(errors)
    if len(errors) == 0:
        return render_template('error_no_errors.html')
    else:
        return render_template('error_index.html', errors=errors, lang=lang)

@app_error_dashboard.route('/warnings')
def warnings():
    errors = app_error_dashboard.aggr_error.return_json_errors(is_warning=True)
    lang = app_error_dashboard.aggr_error.lang.lang[0]
    if len(errors) == 0:
        return render_template('warning_no_errors.html')
    else:
        return render_template('warning.html', errors=errors, lang=lang)