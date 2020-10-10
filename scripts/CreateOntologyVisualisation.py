import networkx as nx
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pronto
import pydot_ng as pydot

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

from pygosemsim import graph
SimG = graph.from_resource("/Users/hastingj/Work/Onto/addiction-ontology/addicto")
similarity.precalc_lower_bounds(SimG)

def addSubclassesToGraph(term, graph):
    print(term)
    subclasses = [sc for sc in term.subclasses(distance=1)]
    for sc in subclasses:
        if sc.id == term.id:
            continue
        else:
            graph.add_node(sc.name)
            graph.add_edge(term.name,sc.name)
            addSubclassesToGraph(sc,graph)


def createImageSubTree(termId, outFileName):
    term = onto[termId]
    print(term)

    G = nx.DiGraph()
    addSubclassesToGraph(term, G)

    pdot = nx.drawing.nx_pydot.to_pydot(G)
    png_path = outFileName
    pdot.write_png(png_path)
    return (pdot)


def colourForSimilarity(pdot, onto, similarityFrom, outFileName):
    colors = ['seashell1','seashell2','papayawhip','palegoldenrod','palegreen','palegreen2','mediumspringgreen','olivedrab3','limegreen','green3','green4']

    for i, node in enumerate(pdot.get_nodes()):
        node_name = str(node).replace("\"","").replace(";","")
        node_id = [t.id for t in onto.terms() if t.name == node_name]
        if len(node_id) > 0:
            node_id = node_id[0]
            simvalue = int( ( similarity.lin(SimG,similarityFrom,node_id) * 10)-1)
            if simvalue < 10:
                col = colors[simvalue]
                node.set_fillcolor(col)
                node.set_style('rounded, filled')
            else:
                print("Got similarity value ",simvalue)

    pdot.write_png(outFileName)


onto = pronto.Ontology("addicto.obo")


termId = "ADDICTO:0000279" # root -- product

pdot = createImageSubTree(termId,'addicto_products.png')

colourForSimilarity(pdot , onto, "ADDICTO:0000240", 'addicto_products_coloured.png' )










