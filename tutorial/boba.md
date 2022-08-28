# Boba

Boba has a domain specific language (Boba DSL) for writing multiverse specifications.
Boba comes with a command line tool to parse your DSL specification and generate universe scripts, execute all scripts with a single command.

This document outlines the rules for the available syntax in boba and basic commands. 

## Script Template
Script template is an annotated script that will be used as the template to
derive executable universes. It can contain two types of annotations: placeholder
variables and code blocks.

### Placeholder Variable
A placeholder variable is a decision point, where the variable will be substituted
by one of the possible options. The placeholder variable declaration is
in the script template via the following syntax:

```
{{variable_name}}
```

It requires exactly two pairs of curly braces enclosing a `variable_name`.
A variable name must start with a letter and can contain an arbitrary number 
of letter, number and the special character `_` (we will reuse this rule
for all identifiers). Between the curly braces and
the variable name, no space is allowed.

The alternative values might be defined in Boba config. The variable name must
match one in the config block, otherwise an error will be raised. 

An option must be either a number or a string in double quotes. Currently,
Boba do not support inline definition that spans multiple lines.

Any valid pattern will be recognized as a template variable, even if you do not
intend to. Any non-valid pattern will be dropped silently, even if you intend
it to be a template variable. All recognized variable will be in `summary.csv`.

Boba also has a few reserved variables, all starting with an underscore. These
variables represent predefined values and you do not need to supply options for
them in the Boba config:
1. `{{_n}}` represents the universe number, namely the number attached to the
generated universe file. It's useful for creating a separate filename for
outputting a separate file in each universe.

### Code Block
A code block declaration breaks the template script into blocks. All lines
following this declaration until the next code block declaration or the end of
file will be counted as inside this block. The syntax is:

```python
# --- (ID) option
```

It starts with `# ---` which is followed by a block identifier inside a pair of
`()`. A block identifier must satisfy the identifier naming rule. After the
block identifier, you might write an option, which also follows the
identifier naming rule. If you provide an option, the block will act like a
decision point, namely boba will substitute different options in different
universes and properly cross with other decisions.

The block identifier will be used to denote a node in the graph in Boba config.
If the Boba config cannot find a corresponding block in the script template, an
error will be raised. However, if the script template contains a block that
does not appear in the graph, only a warning will be raised and the block will
not appear in any generated universes.

You may also write a procedural dependency constraint when declaring a block,
using the following syntax:


## Boba Config
Boba config is code block written in JSON, which contains a number of fields. For us, that is mainly the options of all placeholder variables.

### Options for Placeholder Variables

Another top-level array, `decisions`, contains possible values of placeholder
variables. It is also optional, as long as you do not use any placeholder
variables or provide inline definitions. The syntax is:

```json
{
  "decisions": [
    {"var": "decision_1", "options": [1, 2, 3]},
    {"var": "decision_2", "options": ["1", "2", "3"]}
  ]
}
```
`decisions` is an array of individual decision. Each decision is a dictionary
that contains a `var` string and a `options` array. `var` must match the
corresponding placeholder variable name in the script template.
`options` is an array of all possible values the placeholder
variable can take. An item in the `options` array can be any valid JSON type, as
long as the entire `options` array can be successfully cast into a python list.

Note that if the item is a string, for example "1", the quotes will not appear
in the generated script. For example, if the script template is 
`a={{decision_2}}` and the JSON spec is as above, one generated universe will
be `a=1` instead of `a="1"`.

### Other Top-Level Fields

1. `before_execute` is a string of a single-line bash script. It will be
executed every time prior to executing any universe, when `execute.sh` is
invoked. This field is optional.

2. `after_execute` is a string of a single-line bash script. it will be 
executed every time after executing all universes, when `execute.sh` is invoked.
This field is optional.


## Boba Project Folder Layout
 ```
 boba_project_folder
 ┣ 🟧 multiverse
 ┃ ┣ 🟦 boba_logs
 ┃ ┃ ┣ log_1.txt
 ┃ ┃ ┣ log_2.txt
 ┃ ┃ ┣ log_3.txt
 ┃ ┃ ┣ log_4.txt
 ┃ ┃ ┣ log_5.txt
 ┃ ┃ ┣ log_6.txt
 ┃ ┃ ┗ logs.csv
 ┃ ┣ 🟧 code
 ┃ ┃ ┣ universe_1.py
 ┃ ┃ ┣ universe_2.py
 ┃ ┃ ┣ universe_3.py
 ┃ ┃ ┣ universe_4.py
 ┃ ┃ ┣ universe_5.py
 ┃ ┃ ┗ universe_6.py
 ┃ ┣ lang.json
 ┃ ┣ overview.json
 ┃ ┣ post_exe.sh
 ┃ ┣ pre_exe.sh
 ┃ ┗ 🟧 summary.csv
 ┣ 🟩 data.csv
 ┗ 🟩 template.py
 ```
As a multiverse involves many files, it is beneficial to go over the folder structure.
Before running anything there should be a template file (`template.py`) in which the multiverse is built from and potentially a dataset file (`dataset.csv`). These are shown in 🟩.

We run the following command to compile our template file into universes. 
```
boba compile -s template.py 
```
This command creates the `multiverse` folder which contains a `code` folder containing each generated analysis script and some additional metadata. The `summary.csv` that is generated contains each universe and the instantiated decision options that make up that universe. These are shown in 🟧.

After compilation we can choose to run the multiverse. In the boba_project_folder we can run all universes with
```
boba run --all
```
As universes are ran there stdout and stderr outputs are saved in the `boba_logs` folder which is shown in 🟦.

We can also run individual universes with
```
boba run 4
```
which will run universe #4.