from . import app_diff, app_error_dashboard
from flask import jsonify, render_template, request


@app_error_dashboard.route('/')
def index():
    errors = app_error_dashboard.aggr_error.return_json_errors()
    lang = app_error_dashboard.aggr_error.lang.lang[0]
    return render_template('error_index.html', errors=errors, lang=lang)