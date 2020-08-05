import networkx as nx
import matplotlib
#matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
import pronto

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")


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



onto = pronto.Ontology("addicto.obo")


termId = "ADDICTO:0000279"

createImageSubTree(termId,'addicto_products.png')





