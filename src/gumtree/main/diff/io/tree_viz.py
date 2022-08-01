



import graphviz
from src.gumtree.main.trees.tree import Tree

SCALE = 2
FONT = 'courier'
SHAPE = 'none'
TERMINAL_COLOR = '#800040'
NONTERMINAL_COLOR ='#004080'


def get_graphviz_graph(tree: Tree) -> graphviz.Graph:
    graph = graphviz.Graph(format='svg')
    attach_to_parent(tree, None, graph)
    graph.node_attr.update(dict(
        fontname=FONT,
        shape=SHAPE,
    ))
    return graph
    
    
def attach_to_parent(t: Tree, 
                     parent: str, 
                     graph: graphviz.Graph):
    def _bold(label):
        return '<<B>{}</B>>'.format(label)
    node_name = str(id(t))
    if len(t.children) > 0:
        font_color = NONTERMINAL_COLOR
        bold = True
    else:
        font_color = TERMINAL_COLOR
        bold = False
    label = f"Type: {t.node_type}" + (f", Label: {t.label}" if t.label else "")
    graph.node(name=node_name, 
               label=_bold(label) if bold else label,
               fontcolor=font_color)
    if parent is not None:
        graph.edge(parent, node_name, sametail='t{}'.format(parent))
        
    for child in t.children:
        attach_to_parent(child, str(id(t)), graph)