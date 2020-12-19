import itertools
import networkx as nx
from collections import defaultdict
import matplotlib


def dep_graph(requires, provides):
    g = nx.MultiDiGraph()
    for edge_key in requires:
        for u, v in itertools.product(
            requires[edge_key], provides[edge_key]):
            g.add_edge(u, v, label=(edge_key))

    var_providers = {v:k for k, vars in provides.items() for v in vars}

    sameness = defaultdict(list, {})
    node_to_bunch = {}
    for n in g.nodes:
        # nodes with same identity will be merged
        identity = (
            tuple(g.predecessors(n)),
            tuple(g.successors(n)),
            var_providers.get(n)
        )
        sameness[identity].append(n)
        node_to_bunch[n] = sameness[identity]

    dep_merged = nx.MultiDiGraph()
    for edge_key in requires:
        for u, v in itertools.product(
            requires[edge_key], provides[edge_key]):
            U, V = [tuple(node_to_bunch[x]) for x in (u, v)]
            U, V = [x if len(x)>1 else x[0] for x in (U, V)]

            dep_merged.add_edge(U, V, label=(edge_key))

    return dep_merged

def draw_dependency_graph(depg, **kwargs):
    edge_labels = {(u,v):str(data['label'].__name__) for u, v, data in depg.edges.data()}
    if kwargs.get('pos_s') is None:
        try:
            pos = nx.nx_agraph.graphviz_layout(depg)
        except:
            pos_s = nx.fruchterman_reingold_layout(depg, k=2)
            #pos_s = nx.circular_layout(depg)
            pos_k = nx.kamada_kawai_layout(depg)
            pos = {}
            # ratio of string to shell layout
            beta = .7
            for key in pos_s:
                pos[key] = beta*pos_k[key] + (1-beta)*pos_s[key]

    else:
        pos = kwargs.get('pos')

    # -- Colors for nodes
    if kwargs.get('node_color') is None:
        color_map = []
        for n in depg:
            if len(list(depg.predecessors(n)))==0:
                color_map.append('magenta')
            elif len(list(depg.successors(n)))==0:
                color_map.append('cyan')
            else:
                color_map.append('yellow')

        legend_colors = {
            'magenta':'source'
            , 'cyan':'sink'
        }
    else:
        legend_colors = None
        color_map = kwargs.get('node_color')
    # --
    kwargs['node_color'] = kwargs.get('node_color', color_map)
    kwargs['arrowsize'] = kwargs.get('arrowsize', 15)
    kwargs['pos'] = kwargs.get('pos', pos)
    kwargs['font_size'] = kwargs.get('font_size', 8)
    kwargs['arrowsize'] = kwargs.get('arrowsize', 15)
    edge_labels = kwargs.get('edge_labels', edge_labels) # dirty patch
    del kwargs['edge_labels'] # dirty patch

    nx.draw_networkx(depg, with_labels=False, **kwargs)
    del kwargs['node_color']
    del kwargs['arrowsize']
    nx.draw_networkx_labels(depg, **kwargs)
    kwargs['edge_labels'] = kwargs.get('edge_labels', edge_labels)
    kwargs['rotate'] = kwargs.get('rotate', False)
    nx.draw_networkx_edge_labels(depg, **kwargs)
    if legend_colors:
        patches = [matplotlib.patches.Patch(color=x) for x in legend_colors]
        labels = legend_colors.values()
        matplotlib.pyplot.legend(patches, labels)

def draw_dependency_graph_graphviz(depg, **kwargs):
    import pygraphviz as pgv
    edge_labels = {(u,v):str(data['label'].__name__) for u, v, data in depg.edges.data()}

    # -- Colors for nodes
    if kwargs.get('node_color') is None:
        color_map = []
        for n in depg:
            if len(list(depg.predecessors(n)))==0:
                color_map.append('magenta')
            elif len(list(depg.successors(n)))==0:
                color_map.append('cyan')
            else:
                color_map.append('yellow')

        legend_colors = {
            'magenta':'source'
            , 'cyan':'sink'
        }
    else:
        legend_colors = None
        color_map = [kwargs.get('node_color')]*depg.number_of_nodes()
    # --
    node_props = { n: {'shape':'box', 'color':color} for n, color in zip(depg.nodes, color_map)}
    depg = nx.DiGraph(depg)
    nx.set_edge_attributes(depg, edge_labels, name='label')
    nx.set_node_attributes(depg, node_props)

    G = nx.nx_agraph.to_agraph(depg)
    G.layout()
    G.draw('/tmp/caex_dep_graph.png')
    img = matplotlib.image.imread('/tmp/caex_dep_graph.png')
    matplotlib.pyplot.imshow(img)
    matplotlib.pyplot.axis('off')
    if legend_colors:
        patches = [matplotlib.patches.Patch(color=x) for x in legend_colors]
        labels = legend_colors.values()
        matplotlib.pyplot.legend(patches, labels, loc='lower right')
