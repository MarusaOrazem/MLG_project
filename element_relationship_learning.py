import pandas as pd
import itertools
import networkx as nx
import os

def get_households( data ):
    '''Gets the ids of all the households.
    :param data: pandas dataframe
    :return: list of all ids
    '''
    return data[ 'household_key' ].unique()

def get_basket_for_id( data, id ):
    '''
    Gets basket ids for specific household.
    :param data: pandas dataframe
    :param id: household id
    :return: list of basket ids
    '''

    return data.where(data['household_key'] == id)['BASKET_ID'].dropna().unique()


def get_basket_ids( data ):
    '''
    Gets basket ids for every household id.
    :param data: pandas dataframe
    :return: dict, where keys are household ids and values are list of basket ids
    '''
    house_ids = get_households( data )
    out = {}
    for id in house_ids:
        baskets = data.where( data[ 'household_key' ] == id )[ 'BASKET_ID' ].dropna().unique()
        out[id] = baskets
    return out

def get_products_for_basket( data, id ):
    '''
    Gets the products purchased in the basket id
    :param data: pandas dataframe
    :param id: basket id
    :return: dict, where keys are product ids and values are integers that represents the quantity
    '''

    basket = data.where( data[ 'BASKET_ID' ] == id )[ ['PRODUCT_ID', 'QUANTITY' ] ].dropna()
    out = {}
    for index, row in basket.iterrows():
        out[ row[ 'PRODUCT_ID' ] ] = row[ 'QUANTITY' ]
    return out

def generate_pairs( elements ):
    '''
    Generates pairs of every two element in the list.
    TODO: A mormo tuki upoštevat količino idelkou ali ne???
    :param list: list of elements
    :return: list of tuples
    '''

    return list( itertools.product( elements, elements ) )

def get_unique_pairs(elements):
    '''
    Gets unique pairs and adds its frequency, also adds self-connection
    :param elements: list of tuples that represents pairs of products
    :return: dict, where keys are element ids (tuple) and value is its frequency
    '''
    el_unique = list( set( elements ) )
    out = {}
    for el in el_unique:
        count = elements.count( el )
        out[ el ] = count

        # add self connection
        for id in el:
            out[ (id, id) ] = 1

    return out

def normalize_pairs(elements):
    '''
    Normalize the value of each pair between 0 and 1
    :param elements: dict, keys are pairs and value is its frequency
    :return: dict, just normalized values
    '''
    max_value = elements[ max(elements, key= elements.get ) ]
    out = { key: elements[key]/max_value for key in elements.keys() }
    return out

def construct_graph(pairs):
    '''
    Constructs weighted graph.
    TODO: A bomo mel grafe v networkx al v čem drugem?
    :param pairs: dict, keys are pairs and value is the weight of an edge between elements in pairs
    :return: nx.graph
    '''
    G = nx.Graph()
    for pair in pairs.keys():
        G.add_edge( pair[0], pair[1], weight = pairs[ pair ] )
    return G

def construct_graphs_for_user( data, id ):
    '''
    Constructs T graphs for user id.
    :param data: pandas dataframe
    :param id: user (household) id
    :return: list of T nx.Graphs
    '''
    baskets = get_basket_for_id( data, id )
    products = []
    for basket in baskets:
        p = get_products_for_basket( data, basket )
        products.append( list(p.keys()) )

    all_pairs = []
    for prod in products:
        pairs = generate_pairs( prod )
        all_pairs.append(pairs)


    unique_pairs = get_unique_pairs( list(itertools.chain(*all_pairs)) ) # flatten
    pairs_norm = normalize_pairs( unique_pairs )

    # construct graphs for belonging edges, need to look up the weights
    graphs = []
    for i in range( len( baskets ) ):
        G = nx.Graph()
        current_prod = all_pairs[ i ]
        for pair in current_prod:
            edge_value = pairs_norm[ pair ]
            G.add_edge( pair[0], pair[1], weight = edge_value )
        # adds products that are not in this specific basket ( in every graph we have all the products )
        for p in products:
            for prod in p:
                if prod not in G:
                    G.add_node( prod )
        graphs.append( G )

    return graphs

def write_pajek( graphs, id ):
    '''
    Writes pajek files for all the graphs in list.
    :param graphs: list of nc.graphs
    :return: /
    '''

    if not os.path.exists(f"graphs/{id}"):
        os.makedirs( f"graphs/{id}" )
    for i, G in enumerate(graphs):
        nx.write_pajek(G, f"graphs/{id}/{i}.net" )




if __name__ == '__main__':
    path = 'data/dunnhumby_The-Complete-Journey/dunnhumby - The Complete Journey CSV/transaction_data.csv'
    data = pd.read_csv("transaction_data.csv")
    #products = get_products_for_basket(data, 26984851516 )
    households = get_households(data)

    # test
    id = households[0]
    gs = construct_graphs_for_user( data, id )
    write_pajek(gs, id)
