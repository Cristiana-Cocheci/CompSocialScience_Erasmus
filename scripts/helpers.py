import pandas as pd
import networkx as nx
from scipy.stats import binned_statistic
import matplotlib.pyplot as plt
from tqdm import tqdm
from collections import Counter
import numpy as np
import json
from networkx.readwrite import json_graph

def create_network_org(df, year="all"):
    '''
    Creates a directed graph from mobility data
    Nodes: organizations, each node has an attribute country (from extra data file each country has language family, economic family, geographical cultural region, lat, lon)
    Edges: directed from sending country to receiving country, weighted by number of participants (edge weight = sum of participants for all mobilities from sending to receiving organization) 
    Edge metadata: sender organization, receiver organization, start month, activity type, special needs, fewer opportunities, disadvantaged background (all as counts: how many mobilities from sending to receiving country had this attribute)
    
    examples:
    node: 'sekundarschule friedrich ludwig jahn freyburg': {'country': 'DE - Germany'}
    edge: Edge from 'sekundarschule friedrich ludwig jahn freyburg' to 'colegio san pelayo':  {'weight': 7}
   '''
    
    if year != "all":
        df = df[df['Mobility Year'] == year]
    
    G = nx.DiGraph()
    # add nodes
    nodes = dict(zip(df['Sending Organization'], df['Sending Country']))
    nodes.update(dict(zip(df['Receiving Organization'], df['Receiving Country'])))
    G.add_nodes_from(nodes.keys())
    nx.set_node_attributes(G, nodes, name="country")
    
    for _, row in tqdm(df.iterrows()):
        sending_node = row['Sending Organization']
        receiving_node = row['Receiving Organization']
        participants = row['Actual Participants (Contracted Projects)']

        
        if G.has_edge(sending_node, receiving_node):
            G[sending_node][receiving_node]['weight'] += participants

        else:
            G.add_edge(sending_node, receiving_node, weight=participants, 
                       #metadata=empty_data
                      )
    
    return G


def read_ka2_graphml(years=list, graph_dir=str, fname_prefix=str, selfloops=True):
    '''
    Helper function to 
    - load and prepare KA2 networks from graphml files based on year(s)
    - print out basic components of the loaded network
    '''
    if len(years) == 0:
        print('ValueError: no input for variables "years"')
    if len(years) == 1:
        G = nx.read_graphml(f'{graph_dir}{fname_prefix}{years[0]}.graphml')
    else:
        G = nx.DiGraph()
        for year in years:
            G.update(nx.read_graphml(f'{graph_dir}{fname_prefix}{year}.graphml'))
    
    if not selfloops:
        # remove self loops
        selfloops = nx.selfloop_edges(G)
        G.remove_edges_from(selfloops)
    
    # remove isolates
    isolates = [v for v in nx.isolates(G)]
    G = G.subgraph([v for v in G.nodes if v not in isolates])
    
    # get basic info
    directed = 'directed' if G.is_directed() else 'undirected'
    weighted = 'weighted' if nx.is_weighted(G) else 'unweighted'
    
    print(f'Y{"-".join([str(year) for year in years])} graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} {directed}, {weighted} edges. ')
    print(f'The total number of participants is {sum(nx.get_edge_attributes(G, name="weight").values())}.') 
    return G

def read_ka2_json(years=list, graph_dir=str, fname_prefix=str, selfloops=True):
    '''
    Helper function to 
    - load and prepare KA2 networks from json files based on year(s)
    - print out basic components of the loaded network
    '''
    G = nx.DiGraph()
    if len(years) == 0:
        print('ValueError: no input for variables "years"')
    if len(years) == 1:
        with open(f'{graph_dir}{fname_prefix}{years[0]}.json', 'r') as f:
            data = json.load(f)
            G.update(json_graph.node_link_graph(data, source='source', target='target', edges='edges'))
    else:
        for year in years:
            with open(f'{graph_dir}{fname_prefix}{year}.json', 'r') as f:
                data = json.load(f)
                G.update(json_graph.node_link_graph(data, source='source', target='target', edges='edges'))
    
    if not selfloops:
        # remove self loops
        selfloops = nx.selfloop_edges(G)
        G.remove_edges_from(selfloops)
    
    # remove isolates
    isolates = [v for v in nx.isolates(G)]
    G = G.subgraph([v for v in G.nodes if v not in isolates])
    
    # get basic info
    directed = 'directed' if G.is_directed() else 'undirected'
    weighted = 'weighted' if nx.is_weighted(G) else 'unweighted'
    
    print(f'Y{"-".join([str(year) for year in years])} graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} {directed}, {weighted} edges. ')
    print(f'The total number of participants is {sum(nx.get_edge_attributes(G, name="weight").values())}.') 
    return G

def language_similarity(langs1, langs2):
    '''
    Customized language similarity function for comparing two sets of language families
    '''
    # split string into a set of language families
    set_1 = set([int(x) for x in langs1.split(",")])
    set_2 = set([int(x) for x in langs2.split(",")])

    intersection = set.intersection(set_1, set_2)
    reunion = set_1.union(set_2)
    if len(intersection) == 0:
        # No language family in common
        return 0 
    elif len(intersection) == len(reunion):
        # All language families in common
        return 2
    else:
        # Some language families in common
        return 1
    

def bin_degseq(deg_seq):
    deg_freqs = pd.Series(deg_seq).value_counts().sort_index()
    geo_bins = np.geomspace(1, max(deg_freqs.index))
    bin_counts, bin_edges, _ = binned_statistic(deg_freqs.index, deg_freqs.values,
                                                statistic='mean', 
                                                bins=np.concatenate(([0], geo_bins))
                                               )
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
    return bin_counts, bin_centers


def digraph_config_model(G, weight=None, relabel=True, seed=None):
    '''
    Create a configuration model of the directed graph G
    with additional options to include edge weights 
    and relabel nodes in the configuration network to be consistent with G
    '''
    in_degrees = dict(G.in_degree(weight=weight))
    out_degrees = dict(G.out_degree(weight=weight))
    
    randG = nx.directed_configuration_model(in_degrees.values(), out_degrees.values(),
                                            create_using=nx.MultiDiGraph(), seed=seed)
    
    edges = [(e[0], e[1], w) for e, w in Counter(randG.edges()).items()]
    randG = nx.DiGraph()
    randG.add_weighted_edges_from(edges, weight='weight')
    
    if relabel:
        mapping = {ind: node for ind, node in enumerate(G.nodes())}
        nx.relabel_nodes(randG, mapping, copy=False)
    
    return randG


def weight_attribute_mixing_matrix(G, attribute=str, mapping=None, normalized=True):
    '''
    Attribute mixing matrix with edge weights 
    '''
    
    attr = nx.get_node_attributes(G, name=attribute)
    
    if mapping == None:
        mapping = {l:ind for ind, l in enumerate(set(attr.values()))}
                                                 
    num_categories = len(mapping)
    attr_mix_mat = np.zeros((num_categories, num_categories))

    for s, t, w in G.edges(data='weight'):
        id_s, id_t = mapping.get(attr[s]), mapping.get(attr[t])
        attr_mix_mat[id_s, id_t] += w

    if normalized:
        attr_mix_mat /= attr_mix_mat.sum()
    
    return attr_mix_mat

def obs_config_attribute_mixmat(G, attribute=str, weight=None, niter=50, mapping=None, conf_int=True):
    '''
    Relative mixing matrix between the observed network and a set of niter configuration networks
    '''
    
    attr = nx.get_node_attributes(G, name=attribute)
    
    if mapping == None:
        mapping = {l:ind for ind, l in enumerate(set(attr.values()))}
    
    mat_func = weight_attribute_mixing_matrix if weight else nx.attribute_mixing_matrix
    
    mat = mat_func(G, attribute=attribute, mapping=mapping)
    
    shape = list(mat.shape)
    shape.append(niter)
    shape = tuple(shape)
    rand_mat = np.zeros(shape)
    
    for _ in tqdm(range(niter)):
        
        randG = digraph_config_model(G, weight=weight)
        nx.set_node_attributes(randG, attr, name=attribute)
        rand_mat[:, :, _] += mat_func(randG, attribute=attribute, mapping=mapping)
        
    if conf_int:
        lower = mat/np.quantile(rand_mat, .95, axis=2)
        upper = mat/np.quantile(rand_mat, .05, axis=2)
        return mat/np.mean(rand_mat, axis=2), lower, upper
    else:
        return mat/np.mean(rand_mat, axis=2)



def gini(array):
    """Calculate the Gini coefficient of a numpy array."""
    # implemented by https://github.com/oliviaguest/gini.git
    # based on bottom eq:
    # http://www.statsdirect.com/help/generatedimages/equations/equation154.svg
    # from:
    # http://www.statsdirect.com/help/default.htm#nonparametric_methods/gini.htm
    # All values are treated equally, arrays must be 1d:
    array = array.flatten()
    if np.amin(array) < 0:
        # Values cannot be negative:
        array -= np.amin(array)
    # Values cannot be 0:
    array = array + 0.0000001
    # Values must be sorted:
    array = np.sort(array)
    # Index per array element:
    index = np.arange(1,array.shape[0]+1)
    # Number of array elements:
    n = array.shape[0]
    # Gini coefficient:
    return ((np.sum((2 * index - n  - 1) * array)) / (n * np.sum(array)))