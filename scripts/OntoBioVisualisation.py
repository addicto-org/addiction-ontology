import os

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

from ontobio.io.ontol_renderers import GraphRenderer, OboJsonGraphRenderer
from ontobio.ontol_factory import OntologyFactory

import networkx


# Try to plot the mentions in a subgraph using ontobio
# Note: requires a different version of networkx to the pronto library used above

ofactory = OntologyFactory()
ont = ofactory.create("addicto.obo")

graph = ont.get_graph()

products = True
products_upper = False
organisations = False
psyusers = False
cannabis = False

if products:
    parent_classes = ["OBO:ADDICTO_0000279","OBO:ADDICTO_0001018","OBO:ADDICTO_0001200"]
    products_in_json = ont.traverse_nodes(parent_classes, up=False, down=True) # product
    remove_children_of = ["OBO:ADDICTO_0000292","OBO:ADDICTO_0000752","OBO:ADDICTO_0000733",
                          "OBO:ADDICTO_0000736","OBO:ADDICTO_0000818","OBO:ADDICTO_0000854",
                          "OBO:ADDICTO_0000301","OBO:ADDICTO_0000232","OBO:ADDICTO_0000251",
                          "OBO:ADDICTO_0001139","OBO:ADDICTO_0001120","OBO:ADDICTO_0000919",
                          "OBO:ADDICTO_0000851","OBO:ADDICTO_0000753","OBO:ADDICTO_0000865",
                          "OBO:ADDICTO_0000302","OBO:ADDICTO_0000213"]

    remove_children = ont.traverse_nodes(remove_children_of, up=False, down=True)
    remove_children.add("OBO:ADDICTO_0000269")
    for remid in remove_children:
        products_in_json.remove(remid)
    products_in_json.add("OBO:ADDICTO_0000292")
    products_in_json.add("OBO:ADDICTO_0000232")
    products_in_json.add("OBO:ADDICTO_0000212")
    products_in_json.add("OBO:ADDICTO_0000268")
    products_in_json.add("OBO:ADDICTO_0000205")
    products_in_json.add("OBO:ADDICTO_0000294")
    products_in_json.add("OBO:ADDICTO_0000295")
    products_in_json.add("OBO:ADDICTO_0001203")
    products_in_json.add("OBO:ADDICTO_0000198")
    products_in_json.add("OBO:ADDICTO_0000224")
    products_in_json.add("OBO:ADDICTO_0001199")
    products_in_json.add("OBO:ADDICTO_0000213")
    products_in_json.add("OBO:ADDICTO_0000234")
    products_in_json.add("OBO:ADDICTO_0000219")
    products_in_json.add("OBO:ADDICTO_0001198")
    products_in_json.add("OBO:ADDICTO_0001196")
    products_in_json.add("OBO:CHEBI_18723")

    subont = ont.subontology(products_in_json)

    ojgr = OboJsonGraphRenderer()
    ojgr.outfile = "addicto-products.json"
    ojgr.write(subont)

if products_upper:
    products_in_json = ont.traverse_nodes(["OBO:ADDICTO_0000279",
                                           "OBO:ADDICTO_0000302",
                                           "OBO:ADDICTO_0000827",
                                           "OBO:ADDICTO_0000316",
                                           "OBO:ADDICTO_0000311",
                                           "OBO:ADDICTO_0000303",
                                           "OBO:ADDICTO_0000536",
                                           "OBO:ADDICTO_0000231",
                                           "OBO:ADDICTO_0000212",
                                           "OBO:ADDICTO_0000207",
                                           "OBO:ADDICTO_0000292",
                                           "OBO:ADDICTO_0000201",
                                           "OBO:ADDICTO_0000232"
                                           ], up=False, down=False) # product

    subont = ont.subontology(products_in_json)

    ojgr = OboJsonGraphRenderer()
    ojgr.outfile = "addicto-products-upper.json"
    ojgr.write(subont)

if cannabis:
    products_in_json = ont.traverse_nodes(["OBO:ADDICTO_0000746",
                                           "OBO:ADDICTO_0000302",
                                           "OBO:ADDICTO_0000817",
                                           "OBO:ADDICTO_0000813",
                                           "OBO:ADDICTO_0000300",
                                           "OBO:ADDICTO_0000853",
                                           "OBO:ADDICTO_0000301",
                                           "OBO:ADDICTO_0000854",
                                           "OBO:ADDICTO_0000855",
                                           "OBO:ADDICTO_0000267"], up=False, down=True)
    products_in_json.add("OBO:ADDICTO_0000279")
    subont = ont.subontology(products_in_json)

    ojgr = OboJsonGraphRenderer()
    ojgr.outfile = "addicto-products.json"
    ojgr.write(subont)

if organisations:
    organisations_in_json = ont.traverse_nodes(["OBO:ADDICTO_0000431"], up=False, down=True) # organisation
    subont = ont.subontology(organisations_in_json)
    ojgr = OboJsonGraphRenderer()
    ojgr.outfile = "addicto-organisations.json"
    ojgr.write(subont)

if psyusers:
    psysubsusers = ont.traverse_nodes(["OBO:ADDICTO_0000513","MF:0000016"], up=False, down=True) # psychoactive subs user
    subont = ont.subontology(psysubsusers)
    ojgr = OboJsonGraphRenderer()
    ojgr.outfile = "addicto-suser.json"
    ojgr.write(subont)






# Create the image properties file


import json

image_props_json = ''' 
{
    "style": "filled,rounded",
    "fillcolor":"white",
    "relationProperties": {
        "subClassOf": {
            "color": "black",
            "penwith": 3,
            "arrowhead": "open",
            "label": ""
        },
        "BFO:0000050": {
            "arrowhead": "open",
            "color": "blue",
            "label": "part of"
        },
        "BFO:0000051": {
            "arrowhead":"open",
            "color":"blue",
            "label":"has part"
        },
        "RO:0001019": {
            "arrowhead":"open",
            "color":"green",
            "label":"contains"
        },
        "RO:0001000": {
            "arrowhead":"open",
            "color":"darkgreen",
            "label":"derives from"
        },
        "RO:0000087": {
            "arrowhead":"open",
            "color":"darkgreen",
            "label":"has role"
        },
        "IAO:0000136": {
            "arrowhead": "open",
            "color": "darkgrey",
            "label": "is about"
        },
        "RO:0000091": {
            "arrowhead": "open",
            "color": "darkgrey",
            "label": "has disposition"
        },
        "RO:0000052": {
            "arrowhead": "open",
            "color": "darkgrey",
            "label": "inheres in"
        }
    }, "conditionalProperties": 
'''

# the dynamic part generating the colour based on the lookups
# no fill
conditionalProperties = []
for id in products_in_json:
    conditionalProperties.append({ "conditions": {"id": id} ,
                                   "properties": {"fillcolor": "white"} })

addProps = json.dumps(conditionalProperties) + '}'

with open("imageProps.json", "wt") as text_file:
    text_file.write(image_props_json+addProps)

# After this go to the terminal and type:
# (Terminal) > og2dot.js -s imageProps.json addicto-products.json -t png -o test.png
# (Terminal) > og2dot.js -s imageProps.json addicto-organisations.json -t png -o organisations.png
# (Terminal) > og2dot.js -s imageProps.json addicto-suser.json -t png -o suser.png



#w = GraphRenderer.create('png')
#w.outfile = 'addicto-suser.png'
#w.render(subont, query_ids=psysubsusers)



#w = GraphRenderer.create('png')
#w.outfile = 'addicto-products-literature.png'
#w.render(subont, query_ids=products)
