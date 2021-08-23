import os

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

from Bio import Entrez
#import pronto
import pyhornedowl
import time
import re
import pycountry
import progressbar

# Dealing with countries in affiliations

countrynames = [p.name for p in pycountry.countries]
countrynames[countrynames.index('Iran, Islamic Republic of')] = "Iran"

#countrycodes = [p.alpha_2 for p in pycountry.countries]
countryshortnames = [p.alpha_3 for p in pycountry.countries]
usstates = [s.code.replace("US-","") for s in pycountry.subdivisions.get(country_code='US') ]
usstatenames = [s.name for s in pycountry.subdivisions.get(country_code='US')]


### PUBMED SEARCHING PART

def getCountAndIdList(query, retstart=0, retmax=100):
    Entrez.email = 'janna.hastings@ucl.ac.uk'
    handle = Entrez.esearch(db='pubmed',term=query,retstart=retstart,
                            retmax=retmax,sort='pub+date',
                            reldate=3650,datetype='pdat')  # reldate is in days; 750 is ~ 2 years; 3650 = ~ 10 years
    results = Entrez.read(handle)
    count = int(results['Count'])
    idList = results['IdList']
    return (count,idList)


def fetch_details(id_list):
    ids = ','.join(id_list)
    Entrez.email = 'janna.hastings@ucl.ac.uk'
    handle = Entrez.efetch(db='pubmed',
                           retmode='xml',
                           id=ids)
    results = Entrez.read(handle)
    return results

def getAffiliationCountry(countryString):
    if countryString in countrynames:
        return (countryString)
    if countryString in countryshortnames:
        return(countrynames[countryshortnames.index(countryString)])
    if countryString in usstates or countryString in usstatenames:
        return('United States')
    if countryString == "UK":
        return("United Kingdom")
    #if countryString in countrycodes:
    #    return (countrynames[countrycodes.index(countryString)])
    return None


def getAllAbstracts(query, num_results):
    allAbstracts = {}
    allAuthorAffils = {}
    retstart = 0
    retmax = retstart+10000 if num_results > retstart+10000 else num_results
    while (retstart < num_results):
        (count,idList) = getCountAndIdList(query, retstart=retstart, retmax=retmax)
        print("Got ",count,"records for query",query)
        #print("Got ",idList, "idlist")
        detailResults = fetch_details(idList)

        for result in detailResults:
            resultDetail = detailResults[result]
            for detail in resultDetail:
                if 'MedlineCitation' in detail:
                    PMID = str(detail['MedlineCitation']['PMID'])
                    if 'Article' in detail['MedlineCitation']:
                        if 'Abstract' in detail['MedlineCitation']['Article']:
                            #print(detail['MedlineCitation']['Article'])
                            if 'AbstractText' in detail['MedlineCitation']['Article']['Abstract']:
                                abstractText = str(detail['MedlineCitation']['Article']['Abstract']['AbstractText'])
                                allAbstracts[PMID] = abstractText
                        if "AuthorList" in detail['MedlineCitation']['Article']:
                            allAffils = set()
                            for authorDetail in detail['MedlineCitation']['Article']['AuthorList']:
                                if 'AffiliationInfo' in authorDetail and len(authorDetail['AffiliationInfo'])>0:
                                    if 'Affiliation' in authorDetail['AffiliationInfo'][0]:
                                        affiliation = authorDetail['AffiliationInfo'][0]['Affiliation']
                                        affiliationParts = re.split("\.|,|;|\s",affiliation)
                                        for part in affiliationParts:
                                            result = getAffiliationCountry(part.strip())
                                            if result:
                                                allAffils.add(result)
                                else:
                                    #print("No affiliation info found in ",authorDetail)
                                    continue
                            allAuthorAffils[PMID] = allAffils

        retstart = retmax
        retmax = retstart+10000 if num_results > retstart+10000 else num_results
        print("Updated retstart to",retstart,"and retmax to",retmax,".")
    return(allAbstracts,allAuthorAffils)

# Test
#(allAbstracts, allAuthorAffils) = getAllAbstracts("addiction OR homeless",100)


#### TEXT MINING PART now in ontotexttag.py ... load it


(allAbstracts, allAuthorAffils) =  getAllAbstracts("addiction OR smoking OR vaping OR (behaviour change)",193000)

import pickle
#with open('allAbstracts.pkl', 'wb') as f:
#    pickle.dump(allAbstracts, f)
#with open('allAuthorAffiliations.pkl','wb') as f:
#    pickle.dump(allAuthorAffils, f)

with open('allAbstracts.pkl', 'rb') as f:
    allAbstracts = pickle.load(f)
with open('allAuthorAffiliations.pkl','rb') as f:
    allAuthorAffils = pickle.load(f)

detectedOntologyTerms = {}
i = 0

bar = progressbar.ProgressBar(maxval=len(allAbstracts),
                                      widgets=[progressbar.Bar('=', '[', ']'), ' ', progressbar.Percentage()])
bar.start()

#Consider refactoring to use this:
#texts = ["This is a text", "These are lots of texts", "..."]
##- docs = [nlp(text) for text in texts]
#+ docs = list(nlp.pipe(texts))

for PMID in allAbstracts:
    abstract = allAbstracts[PMID]
    doc = nlp3(abstract)
    for token in doc:
        if token._.is_ontol_term:
            #print(token._.ontol_id, token.text)
            if token._.ontol_id not in detectedOntologyTerms:
                detectedOntologyTerms[token._.ontol_id] = []
            if PMID not in detectedOntologyTerms[token._.ontol_id]:
                detectedOntologyTerms[token._.ontol_id].append(PMID)

    i += 1
    bar.update(i)

bar.finish()

with open('detectedOntologyTerms.pkl', 'wb') as f:
    pickle.dump(detectedOntologyTerms, f)

countryCounts = {}

for PMID in allAuthorAffils:
    authorAffils = allAuthorAffils[PMID]
    for country in authorAffils:
        if country in countryCounts:
            countryCounts[country] = countryCounts[country]+1
        else:
            countryCounts[country] = 1



###
### Just from here for further analysis of existing detections
###
import os
os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
import pandas as pd
import pickle
import pyhornedowl
from urllib.request import urlopen
#import pronto

with open('detectedOntologyTerms.pkl', 'rb') as f:
    detectedOntologyTerms = pickle.load(f)


RDFSLABEL = "http://www.w3.org/2000/01/rdf-schema#label"
SYN = "http://purl.obolibrary.org/obo/IAO_0000118"
PREFIXES = [ ["ADDICTO","http://addictovocab.org/ADDICTO_"],
             ["BFO","http://purl.obolibrary.org/obo/BFO_"],
             ["CHEBI","http://purl.obolibrary.org/obo/CHEBI_"],
             ["UBERON","http://purl.obolibrary.org/obo/UBERON_"],
             ["PATO","http://purl.obolibrary.org/obo/PATO_"],
             ["BCIO","http://humanbehaviourchange.org/ontology/BCIO_"],
             ["SEPIO","http://purl.obolibrary.org/obo/SEPIO_"],
             ["OMRSE","http://purl.obolibrary.org/obo/OMRSE_"],
             ["OBCS","http://purl.obolibrary.org/obo/OBCS_"],
             ["OGMS","http://purl.obolibrary.org/obo/OGMS_"],
             ["ENVO","http://purl.obolibrary.org/obo/ENVO_"],
             ["OBI", "http://purl.obolibrary.org/obo/OBI_"],
             ["MFOEM","http://purl.obolibrary.org/obo/MFOEM_"],
             ["MF","http://purl.obolibrary.org/obo/MF_"],
             ["CHMO","http://purl.obolibrary.org/obo/CHMO_"],
             ["DOID","http://purl.obolibrary.org/obo/DOID_"],
             ["IAO","http://purl.obolibrary.org/obo/IAO_"],
             ["ERO","http://purl.obolibrary.org/obo/ERO_"],
             ["PO","http://purl.obolibrary.org/obo/PO_"],
             ["RO","http://purl.obolibrary.org/obo/RO_"],
             ["APOLLO_SV","http://purl.obolibrary.org/obo/APOLLO_SV_"],
             ["PDRO","http://purl.obolibrary.org/obo/PDRO_"],
             ["GAZ","http://purl.obolibrary.org/obo/GAZ_"],
             ["GSSO","http://purl.obolibrary.org/obo/GSSO_"]
           ]

location = f"https://raw.githubusercontent.com/addicto-org/addiction-ontology/master/addicto-merged.owx"
data = urlopen(location).read()  # bytes
ontofile1 = data.decode('utf-8')
onto = pyhornedowl.open_ontology(ontofile1)
for prefix in PREFIXES:
    onto.add_prefix_mapping(prefix[0], prefix[1])

idents = [i for i in detectedOntologyTerms]
iris = [onto.get_iri_for_id(i) for i in detectedOntologyTerms]
labels = [ onto.get_annotation(i,RDFSLABEL) for i in iris]
labelsnn = [l if l is not None else i for (l,i) in zip(labels,idents)]
counts = [len(detectedOntologyTerms[c]) for c in detectedOntologyTerms]

df = pd.DataFrame(list(zip(idents, labelsnn, counts)),
               columns =['ID', 'Name', 'Count'])
df

# How are the counts distributed?
sns.kdeplot(df['Count'])
plt.show()

# Order them
labels_sorted = [x for _,x in sorted(zip(counts,labelsnn),reverse=True)]
counts_sorted = sorted(counts,reverse=True)

y_pos = np.arange(50)

plt.bar(y_pos, counts_sorted[:50], align='center', alpha=0.5)
plt.subplots_adjust(left=0.1, bottom=0.4, right=0.9, top=0.9)
plt.xticks(y_pos, labels_sorted[:50], rotation='vertical',fontsize=8)
plt.ylabel('Counts')
plt.title('Top 50 Ontology Term Occurrence Counts')

plt.show()

# THE COUNTRIES

keys = countryCounts.keys()
values = countryCounts.values()

labels_sorted = [x for _,x in sorted(zip(values,keys),reverse=True)]
counts_sorted = sorted(values,reverse=True)

y_pos = np.arange(50)

plt.bar(y_pos, counts_sorted[:50], align='center', alpha=0.5)
plt.subplots_adjust(left=0.1, bottom=0.4, right=0.9, top=0.9)
plt.xticks(y_pos, labels_sorted[:50], rotation='vertical',fontsize=8)
plt.ylabel('Counts')
plt.title('Top 50 Country Occurrence Counts')

plt.show()

# Just the tobacco and vaping related products counts?

product = "http://addictovocab.org/ADDICTO_0000279"
stopids = ["http://addictovocab.org/ADDICTO_0000733",
           "http://addictovocab.org/ADDICTO_0000818",
           "http://addictovocab.org/ADDICTO_0000269",
           "http://addictovocab.org/ADDICTO_0000279",
           "http://addictovocab.org/ADDICTO_0000308",
           "http://addictovocab.org/ADDICTO_0000736",
           "http://addictovocab.org/ADDICTO_0000744"]
cons_beh = "http://addictovocab.org/ADDICTO_0000127" # consumption behaviour

products = pyhornedowl.get_descendants(onto,product)
behs = pyhornedowl.get_descendants(onto,cons_beh)
products_iris = [p for p in products.union(behs) if p not in stopids]


users_ids = ["ADDICTO:0000410","ADDICTO:0000941","ADDICTO:0000352","ADDICTO:0000972","GSSO:005301"]
users_ids_found = df[df.ID.isin(users_ids)].ID

products_iris = [p for p in products if p not in stopids]
products_ids = [onto.get_id_for_iri(i) for i in products_iris ]
products_ids = set(products_ids).union(users_ids)

products_ids_found = df[df.ID.isin(products_ids)].ID
products_labels = df[df.ID.isin(products_ids)].Name
products_counts = df[df.ID.isin(products_ids)].Count

labels_sorted = [x for _,x in sorted(zip(products_counts,products_labels),reverse=True)]
counts_sorted = sorted(products_counts,reverse=True)
import math
counts_logged = [math.log(x) for x in counts_sorted]

y_pos = np.arange(len(labels_sorted))

plt.bar(y_pos, counts_sorted, align='center', alpha=0.5, log=True)
#plt.bar(y_pos, counts_logged, align='center', alpha=0.5)
plt.subplots_adjust(left=0.1, bottom=0.4, right=0.9, top=0.9)
plt.xticks(y_pos, labels_sorted, rotation='vertical',fontsize=8)
plt.ylabel('Counts')
plt.title('Top Product Occurrence Counts')

plt.show()

#### Can we do co-occurrence analysis? Ontology terms co-occurring within the same PM article?

idents = [i for i in detectedOntologyTerms for p in detectedOntologyTerms[i] ]
pmids = [p for i in detectedOntologyTerms for p in detectedOntologyTerms[i] ]
iris = [onto.get_iri_for_id(i) for i in idents]
labels = [ onto.get_annotation(i,RDFSLABEL) for i in iris]

df2 = pd.DataFrame(list(zip(idents, pmids, labels)),
               columns =['ADDICTOID', 'PMID', 'LABEL'])
df2

#df2.to_csv("ontotermmentions.csv")
#df2 = pd.read_csv("ontotermmentions.csv",index_col=0)

### TRY: Chord diagram based on shared appearance in PMID

import pandas as pd
import holoviews as hv
from holoviews import opts, dim
hv.extension('bokeh')
hv.output(size=200)

data_chord_plot = pd.merge(df2,df2,on="PMID")

data_chord_plot = data_chord_plot.drop(data_chord_plot[data_chord_plot.LABEL_x == data_chord_plot.LABEL_y].index)
data_chord_plot = data_chord_plot.drop(data_chord_plot[~data_chord_plot.ADDICTOID_x.isin(products_ids)].index)
data_chord_plot = data_chord_plot.drop(data_chord_plot[~data_chord_plot.ADDICTOID_y.isin(products_ids)].index)
#data_chord_plot = data_chord_plot.drop(data_chord_plot[data_chord_plot.ADDICTOID_x.isin(stopids)].index)
#data_chord_plot = data_chord_plot.drop(data_chord_plot[data_chord_plot.ADDICTOID_y.isin(stopids)].index)

dcp = data_chord_plot
dcp.drop_duplicates(inplace=True)

dcp.reindex()

#def get_unique_str(df):
#  return pd.Series([
#    ''.join(sorted([aoidx,aoidy,pmid]))
#    for (aoidx, aoidy, pmid) in zip(df['LABEL_x'], df['LABEL_y'],df['PMID'])
#  ])

#dcp['uniquestr'] = get_unique_str(dcp)
#dcp.drop_duplicates(subset=['uniquestr'],inplace=True)
to_drop = set()
for index, row in dcp.iterrows():  # THIS IS SLOW
    if index % 100 == 0:
        print(".",index)
    if ((dcp['ADDICTOID_x'] == row['ADDICTOID_y'])
        & (dcp['ADDICTOID_y'] == row['ADDICTOID_x'])
        & (dcp['PMID'] == row['PMID'])).any():  # Does the inverse of this row exist in the table?
            to_drop.add(index)
dcp = dcp.drop(to_drop)

data_chord_plot_2 = dcp.groupby(['LABEL_x', 'LABEL_y'], as_index=False)[['PMID']].count()
data_chord_plot_2.columns = ['source','target','value']

links = data_chord_plot_2
node_names = links.source.append(links.target)
node_names = node_names.unique()
node_info = {"index":node_names,"name":node_names,"group":[1]*len(node_names)}

nodes = hv.Dataset(pd.DataFrame(node_info), 'index')
nodes.data.head()

chord = hv.Chord((links, nodes)).select(value=(5, None))

chord.opts(
    opts.Chord(cmap='Category20', edge_cmap='Category20', edge_color=dim('source').str(),
               labels='name', node_color=dim('index').str()))

hv.save(chord, 'chordout.html')


# Try: Parallel visualisation between two sets of categories.

import plotly.express as px

import plotly.io as pio
pio.renderers.default = "browser"

# PARALLEL CATEGORIES - THREE CATEGORIES AND WIN %


dfforplot = pd.DataFrame([["cigarette",1,"young person"],
                          ["cigar",2,"young person"],
                          ["cigarette",1,"young person"],
                          ["bidi",3,"old person"],
                          ["bidi",3,"young person"]],
                         columns=["Product","ProductNumber","Person"])

fig = px.parallel_categories(dfforplot, dimensions=['Product', 'Person'],
                color="ProductNumber", color_continuous_scale=px.colors.sequential.Inferno)
fig.show()

fig = px.parallel_categories(data_chord_plot,dimensions=["LABEL_x","LABEL_y"])
fig.show()










#### OntoBio below here
### For Visualisation

from ontobio.ontol_factory import OntologyFactory

# Try to plot the mentions in a subgraph using ontobio
# Note: requires a different version of networkx to the pronto library used above

ofactory = OntologyFactory()
ont = ofactory.create("addicto.obo")

with open('detectedOntologyTerms.pkl', 'rb') as f:
    detectedOntologyTerms = pickle.load(f)

idents = [i.replace("ADDICTO:","OBO:ADDICTO_") for i in detectedOntologyTerms] # Translate pronto to ontobio
labels = [ont.label(i) for i in idents]


graph = ont.get_graph()

import networkx
import matplotlib.pyplot as plt

idents = [i.replace("APOLLO_SV:","OBO:APOLLO_SV_") for i in idents] # more translation
idents = [i.replace("BCIO:","OBO:BCIO_") for i in idents]
nodes = ont.traverse_nodes(idents, up=True, down=True)


products_in_json = ont.traverse_nodes(["OBO:ADDICTO_0000279",
                                       "OBO:ADDICTO_0000746",
                                       "OBO:ADDICTO_0000302",
                                       "OBO:ADDICTO_0000817",
                                       "OBO:ADDICTO_0000813"], up=False, down=True) # product



#psysubsusers = ont.traverse_nodes(["OBO:ADDICTO_0000513"], up=False, down=True) # psychoactive subs user
#subont = ont.subontology(psysubsusers)

removeids = ["OBO:ADDICTO_0000818","OBO:ADDICTO_0000269", "OBO:ADDICTO_0000733",
             "OBO:ADDICTO_0000736","OBO:ADDICTO_0000744"] # energy drinks, over the counter medication,
for remid in removeids:
    products_in_json.remove(remid)

subont = ont.subontology(products_in_json)

from ontobio.io.ontol_renderers import GraphRenderer, OboJsonGraphRenderer

#w = GraphRenderer.create('png')
#w.outfile = 'addicto-products-literature.png'
#w.render(subont, query_ids=products)

ojgr = OboJsonGraphRenderer()
ojgr.outfile = "addicto-products.json"
ojgr.write(subont)


#w = GraphRenderer.create('png')
#w.outfile = 'addicto-suser.png'
#w.render(subont, query_ids=psysubsusers)

#ojgr = OboJsonGraphRenderer()
#ojgr.outfile = "addicto-suser.json"
#ojgr.write(subont)

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

# just plain blue
conditionalProperties = []
for product_id in products_in_json:
    if product_id.replace("OBO:ADDICTO_","ADDICTO:") in products_ids_found.values:
        conditionalProperties.append({ "conditions": {"id": product_id} ,
                                       "properties": {"fillcolor": "lightblue"} })


addProps = json.dumps(conditionalProperties) + '}'

with open("imageProps.json", "wt") as text_file:
    text_file.write(image_props_json+addProps)

colors = ["lightcyan","paleturquoise","aquamarine","cyan","turquoise","mediumturquoise","darkturquoise","lightseagreen","darkcyan","teal"]

# then a range of blues
conditionalProperties = []
for product_id in products_in_json:
    product_id_obo = product_id.replace("OBO:ADDICTO_","ADDICTO:")
    if product_id_obo in products_ids_found.values:
        index_of = products_ids_found[products_ids_found == product_id_obo].index[0]
        product_count = int(math.log(products_counts[index_of]))
        conditionalProperties.append({ "conditions": {"id": product_id} ,
                                       "properties": {"fillcolor": colors[product_count]} })

addProps = json.dumps(conditionalProperties) + '}'

with open("imageProps.json", "wt") as text_file:
    text_file.write(image_props_json+addProps)

# After this go to the terminal and type:
# (Terminal) > og2dot.js -s imageProps.json addicto-products.json -t png -o test.png

