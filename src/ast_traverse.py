from dataclasses import dataclass
import ast
from ast import (
    iter_fields, 
    iter_child_nodes, 
    _const_node_type_names, 
    AST
)
from ast import NodeVisitor as ASTNodeVisitor

@dataclass(init=False)
class NodeData:
    name: str
    lineno: int
    col_offset: int
    end_lineno: int
    end_col_offset: int
    def __init__(self, node):
        self.name = node.__class__.__name__
        if isinstance(node, ast.stmt) or isinstance(node, ast.expr):
            self.lineno = node.lineno
            self.col_offset = node.col_offset
            self.end_lineno = node.end_lineno
            self.end_col_offset = node.end_col_offset
        else:
            self.lineno = None
            self.col_offset = None
            self.end_lineno = None 
            self.end_col_offset = None

class NodeVisitor(object):
    """
    A node visitor base class that walks the abstract syntax tree and calls a
    visitor function for every node found.  This function may return a value
    which is forwarded by the `visit` method.

    This class is meant to be subclassed, with the subclass adding visitor
    methods.

    Per default the visitor functions for the nodes are ``'visit_'`` +
    class name of the node.  So a `TryFinally` node visit function would
    be `visit_TryFinally`.  This behavior can be changed by overriding
    the `visit` method.  If no visitor function exists for a node
    (return value `None`) the `generic_visit` visitor is used instead.

    Don't use the `NodeVisitor` if you want to apply changes to nodes during
    traversing.  For this a special visitor exists (`NodeTransformer`) that
    allows modifications.
    """
    def __init__(self):
        self.visited = []

    def visit(self, node, path=[]):
        """Visit a node."""
        method = 'visit_' + node.__class__.__name__
        self.visited.append(node.__class__.__name__)
        path.append(NodeData(node))
        visitor = getattr(self, method, self.generic_visit)
        res = visitor(node, path)
        path.pop()
        return res
        
    def generic_visit(self, node, path):
        """Called if no explicit visitor function exists for a node."""
        for field, value in iter_fields(node):
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, AST):
                        self.visit(item, path)
            elif isinstance(value, AST):
                self.visit(value, path)

    def visit_Constant(self, node, path):
        value = node.value
        type_name = _const_node_type_names.get(type(value))
        if type_name is None:
            for cls, name in _const_node_type_names.items():
                if isinstance(value, cls):
                    type_name = name
                    break
        if type_name is not None:
            method = 'visit_' + type_name
            try:
                visitor = getattr(self, method)
            except AttributeError:
                pass
            else:
                import warnings
                warnings.warn(f"{method} is deprecated; add visit_Constant",
                              DeprecationWarning, 2)
                res = visitor(node, path)
                return res
        res = self.generic_visit(node, path)
        return res


class NodeVisitorStack(object):
    def __init__(self):
        self.stack = []
        self.visited = []
    
    def add_children_to_stack(self, node):
        method = 'visit_' + node.__class__.__name__
        if method == 'visit_Constant':
            value = node.value
            type_name = _const_node_type_names.get(type(value))
            if type_name is None:
                for cls, name in _const_node_type_names.items():
                    if isinstance(value, cls):
                        type_name = name
                        break
            if type_name is not None:
                method = 'visit_' + type_name
                try:
                    visitor = getattr(self, method)
                except AttributeError:
                    pass
                else:
                    import warnings
                    warnings.warn(f"{method} is deprecated; add visit_Constant",
                                DeprecationWarning, 2)
                    visitor(node)
            else:
                self.generic_visit(node)
        else:
            visitor = getattr(self, method, self.generic_visit)
            visitor(node)
    
    def pop_stack(self):
        node = self.stack[-1]
        self.stack.pop()
        return node
    
    def visit_iter(self):
        node = self.pop_stack()
        self.visited.append(node.__class__.__name__)
        self.add_children_to_stack(node)
        return node
            
    def visit(self, node):
        self.stack.append(node)
        self.visited = []
        while (len(self.stack)):
            # Pop a vertex from stack and print it
            self.visit_iter()
    
    def generic_visit(self, node):
        """Called if no explicit visitor function exists for a node."""
        for field, value in reversed(list(iter_fields(node))):
            if isinstance(value, AST):
                self.stack.append(value)
            elif isinstance(value, list):
                for item in reversed(value):
                    if isinstance(item, AST):
                        self.stack.append(item)

    
class NodeTransformer(NodeVisitor):
    """
    A :class:`NodeVisitor` subclass that walks the abstract syntax tree and
    allows modification of nodes.

    The `NodeTransformer` will walk the AST and use the return value of the
    visitor methods to replace or remove the old node.  If the return value of
    the visitor method is ``None``, the node will be removed from its location,
    otherwise it is replaced with the return value.  The return value may be the
    original node in which case no replacement takes place.

    Here is an example transformer that rewrites all occurrences of name lookups
    (``foo``) to ``data['foo']``::

       class RewriteName(NodeTransformer):

           def visit_Name(self, node):
               return Subscript(
                   value=Name(id='data', ctx=Load()),
                   slice=Constant(value=node.id),
                   ctx=node.ctx
               )

    Keep in mind that if the node you're operating on has child nodes you must
    either transform the child nodes yourself or call the :meth:`generic_visit`
    method for the node first.

    For nodes that were part of a collection of statements (that applies to all
    statement nodes), the visitor may also return a list of nodes rather than
    just a single node.

    Usually you use the transformer like this::

       node = YourTransformer().visit(node)
    """

    def generic_visit(self, node, path):
        for field, old_value in iter_fields(node):
            if isinstance(old_value, list):
                new_values = []
                for value in old_value:
                    if isinstance(value, AST):
                        value = self.visit(value, path)
                        if value is None:
                            continue
                        elif not isinstance(value, AST):
                            new_values.extend(value)
                            continue
                    new_values.append(value)
                old_value[:] = new_values
            elif isinstance(old_value, AST):
                new_node = self.visit(old_value, path)
                if new_node is None:
                    delattr(node, field)
                else:
                    setattr(node, field, new_node)
        return node
    
class OurNodeTransformer(NodeTransformer):
    def visit_Set(self, node, path):
        def node_set_and_length_one(node):
            return len(node.elts) == 1 and isinstance(node.elts[0], ast.Set)
        def node_name_and_length_one(node):
            return len(node.elts) == 1 and isinstance(node.elts[0], ast.Name)
        if node_set_and_length_one(node) and node_name_and_length_one(node.elts[0]): # {{boba_var}}
            return ast.copy_location(ast.Constant(ast.unparse(node)), node)
        else:
            self.generic_visit(node, path)
            return node



if __name__ == '__main__':
    nv1 = NodeVisitorStack()
    nv2 = NodeVisitor()
    
    code = """#!/usr/bin/env python3

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

if __name__ == '__main__':
    # read data file
    df = pd.read_csv('/projects/bdata/kenqgu/Research/MultiverseProject/boba_tea/boba/example/fertility/durante_etal_2013_study1.txt', delimiter='\t')

    # remove NA
    df = df.dropna(subset=['rel1', 'rel2', 'rel3'])

    # create religiosity score
    df['rel_comp'] = np.around((df.rel1 + df.rel2 + df.rel3) / 3, decimals=2)

    # next menstrual onset (nmo) assessment
    df.last_period_start = pd.to_datetime(df.last_period_start)
    df.period_before_last_start = pd.to_datetime(df.period_before_last_start)
    df.date_testing = pd.to_datetime(df.date_testing)

    # --- (NMO1)
    # first nmo option: based on computed cycle length
    cl = df.last_period_start - df.period_before_last_start
    next_onset = df.last_period_start + cl
    df['computed_cycle_length'] = (cl / np.timedelta64(1, 'D')).astype(int)

    # --- (NMO2)
    # second nmo option: based on reported cycle length
    df = df.dropna(subset=['reported_cycle_length'])
    next_onset = df.last_period_start + df.reported_cycle_length.apply(
        lambda a: pd.Timedelta(days=a))

    # --- (ECL1)
    # exclusion based on computed cycle length
    df = df[(df.computed_cycle_length >= 25) & (df.computed_cycle_length <= 35)]

    # --- (ECL2)
    # exclusion based on reported cycle length
    df = df[(df.reported_cycle_length >= 25) & (df.reported_cycle_length <= 35)]

    # --- (A)
    # compute cycle day
    df['cycle_day'] = pd.Timedelta('28 days') - (next_onset - df.date_testing)
    df.cycle_day = (df.cycle_day / np.timedelta64(1, 'D')).astype(int)
    df.cycle_day = np.clip(df.cycle_day, 1, 28)

    # fertility assessment
    high_bounds = {{fertility_bounds}}[0]
    low_bounds1 = {{fertility_bounds}}[1]
    low_bounds2 = {{fertility_bounds}}[2]
    df.loc[(high_bounds[0] <= df.cycle_day) & (df.cycle_day <= high_bounds[1]),
           'fertility'] = 'High'
    df.loc[(low_bounds1[0] <= df.cycle_day) & (df.cycle_day <= low_bounds1[1]),
           'fertility'] = 'Low'
    df.loc[(low_bounds2[0] <= df.cycle_day) & (df.cycle_day <= low_bounds2[1]),
           'fertility'] = 'Low'

    # relationship status assessment
    # single = response options 1 and 2; relationship = response options 3 and 4
    df.loc[df.relationship <= {{relationship_bounds}}[0],
           'relationship_status'] = 'Single'
    df.loc[df.relationship >= {{relationship_bounds}}[1],
           'relationship_status'] = 'Relationship'

    # --- (EC)
    # exclusion based on certainty ratings
    df = df[(df.sure1 >= 6) & (df.sure2 >= 6)]

    # --- (B)
    # perform an ANOVA on the processed data set
    lm = smf.ols('rel_comp ~ relationship_status {{relationship_bounds}} * fertility', data=df).fit()
    table = sm.stats.anova_lm(lm, typ=2)
    print(table)
"""

    nv1.visit(ast.parse(code))
    nv2.visit(ast.parse(code))
    assert(nv1.visited == nv2.visited)
    print('here')
    
    
