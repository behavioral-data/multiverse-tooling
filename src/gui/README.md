## Files
* `routes_diff.py` and `routes_error.py` contains the flask URLs to the diff and error interfaces. These are used by cli.py in `src/boba/cli.py`.
* `index.html` in the s`rc/gui/resources/templates` folder contains the html jinja template for the diff interface
* `error_index.html`, `error_no_errors.html`, `warning_no_errors.html`, and `warning.html` contain the jinja templates for the error aggregate interface
* monaco.js and monaco.css  in `src/gui/resources` contains the files for the monaco editor. We also use `prism.js` and `prism.css` for the prism editor. 
