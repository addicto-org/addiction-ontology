

import os
from pygosemsim import graph


os.chdir('/Users/hastingj/Work/Onto/addiction-ontology')


import networkx as nx

G = graph.from_resource("/Users/hastingj/Work/Onto/addiction-ontology/addicto")

nx.ancestors(G, "ADDICTO:0000212")

"ADDICTO:0000239" # Flavoured E-liquid
"ADDICTO:0000201" # Cigarette
"ADDICTO:0000212" # E-Cigarette
"ADDICTO:0000240" # Fruit flavoured e-liquid


from pygosemsim import similarity

similarity.precalc_lower_bounds(G)

# How similar are Cigarette and E-cigarette?

similarity.resnik(G, "ADDICTO:0000201", "ADDICTO:0000212")
# 2.87

similarity.wang(G, "ADDICTO:0000201", "ADDICTO:0000212")
#0.436
similarity.lin(G, "ADDICTO:0000201", "ADDICTO:0000212")
#0.45
similarity.pekar(G, "ADDICTO:0000201", "ADDICTO:0000212")
#0.455

# How similar are E-cigarette and Flavoured E-liquid?

similarity.resnik(G, "ADDICTO:0000239", "ADDICTO:0000212")
# 4.257
similarity.wang(G, "ADDICTO:0000239", "ADDICTO:0000212")
# 0.595
similarity.lin(G, "ADDICTO:0000239", "ADDICTO:0000212")
# 0.7
similarity.pekar(G, "ADDICTO:0000239", "ADDICTO:0000212")
#0.778

# How similar is fruit flavoured e-liquid and flavoured e-liquid
similarity.resnik(G, "ADDICTO:0000239", "ADDICTO:0000240")
# 7.372
similarity.wang(G, "ADDICTO:0000239", "ADDICTO:0000240")
# 0.882
similarity.lin(G, "ADDICTO:0000239", "ADDICTO:0000240")
#0.903
similarity.pekar(G, "ADDICTO:0000239", "ADDICTO:0000240")
#0.875


