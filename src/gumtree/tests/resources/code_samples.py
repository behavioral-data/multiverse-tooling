

TEMPLATE_CODE = """
cl = df.last_period_start - df.period_before_last_start 
df.cycle_day = np.clip(df.cycle_day, 1, 28)
df.loc[df.relationship <= {{relationship_bounds}}[0],
                'relationship_status'] = 'Single'
df.loc[df.relationship >= {{relationship_bounds}}[1],
                'relationship_status'] = 'Relationship'
    """
    
    
    
PYTHON_CODE = """
df.cycle_day = np.clip(df.cycle_day, 1, 280 + 12)
df.loc[df.relationship <= 2 + [2, 5][0],
                'relationship_status'] = 'Single'
df.loc[df.relationship >= [2, 3][1],
                'relationship_status'] = 'Relationship'
    """
    
FUNC1 = """
class Best:
    def foo(self, i):
        if i == 0:
            return "Foo!"
"""

FUNC2 = """
class Test:
    def  foo(self, i, j):
        if i == j:
            return "Bar"
        elif i == -1:
            return "Foo!"
"""


BOBA_JSON_CODE = """#!/usr/bin/env python3
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
# --- (BOBA_CONFIG)
{
  "graph": [
    "NMO1->ECL1->A",
    "NMO2->ECL2->A",
    "NMO1->A",
    "NMO2->A",
    "A->B",
    "A->EC->B"
  ],
  "decisions": [
    {"var": "fertility_bounds", "options": [
      [[7, 14], [17, 25], [17, 25]],
      [[6, 14], [17, 27], [17, 27]],
      [[9, 17], [18, 25], [18, 25]],
      [[8, 14], [1, 7], [15, 28]],
      [[9, 17], [1, 8], [18, 28]]
    ]},
    {"var": "relationship_bounds",
      "options": [[2, 3], [1, 2], [1, 3]]}
  ],
  "before_execute": "cp ../durante_etal_2013_study1.txt ./code/"
}
# --- (END)
"""