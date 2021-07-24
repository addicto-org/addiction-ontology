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
    products_in_json = ont.traverse_nodes(["OBO:ADDICTO_0000279",
                                       "OBO:ADDICTO_0000302",
                                       "OBO:ADDICTO_0000817",
                                       "OBO:ADDICTO_0000813"], up=False, down=True) # product
    removeids = ["OBO:ADDICTO_0000818", "OBO:ADDICTO_0000269", "OBO:ADDICTO_0000733",
                 "OBO:ADDICTO_0000736",
                 "OBO:ADDICTO_0000744"]  # energy drinks, over the counter medication,
    for remid in removeids:
        products_in_json.remove(remid)
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
