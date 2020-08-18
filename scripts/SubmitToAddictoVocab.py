import os
import csv
import urllib.request
import json
import re
import requests
import traceback
import pronto


AOVOCAB_API = "https://api.addictovocab.org/"
GET_TERMS = "terms?label={}&page={}&itemsPerPage={}"
POST_TERMS = "terms"
DELETE_TERMS = "terms/{}"
PATCH_TERMS = "terms/{}"

def getAllIDsFromAddictOVocab():
    pageNo = 1
    totPerPage = 50
    allIds = []

    while (True):
        result = getFromAddictOVocab('',pageNo,totPerPage)
        resultCount = result['hydra:totalItems']

        if resultCount == 0:
            break

        for term in result['hydra:member']:
            allIds.append(term['id'])
        print(f"There are {resultCount} total results, we have {len(allIds)} so far.")

        if resultCount == len(allIds):
            break

        if (pageNo*totPerPage) > resultCount:
            break

        pageNo = pageNo + 1

    return(allIds)



def getFromAddictOVocab(label,pageNo=1,totPerPage=30):
    urlstring = AOVOCAB_API + GET_TERMS.format(label,pageNo,totPerPage)
    print(urlstring)

    r = requests.get(urlstring)
    print(f"Get returned {r.status_code}")
    return ( r.json() )

def getURIForID(id, prefix_dict):
    if "ADDICTO" in id:
        return "http://addictovocab.org/"+id
    else:
        if ":" in id:
            id_split = id.split(":")
        elif "_" in id:
            id_split = id.split("_")
        else:
            print(f"Cannot determine prefix in {id}, just returning id")
            return(id)
        prefix=id_split[0]
        if prefix in prefix_dict:
            uri_prefix = prefix_dict[prefix]
            return (uri_prefix + "_" +id_split[1])
        else:
            print("Prefix ",prefix,"not in dict")
            return (id)


# By default, don't create links the first time we create terms.
# Call a second time (after all data created) to create links.
# Can be done in one step if the linked entities do exist.
def createTermInAddictOVocab(header,rowdata, prefix_dict, create=True,links=False):
    data = {}
    for (value, header) in zip(rowdata,header):
        if value:
            if header == "ID":
                data['id'] = value
                data['uri'] = getURIForID(value, prefix_dict)
            elif header == "Label":
                data['label'] = value
            elif header == "Definition":
                data['definition'] = value
            elif header == "Definition source":
                data['definitionSource'] = value
            elif header == "AO sub-ontology":
                data['addictoSubOntology'] = value
            elif header == "Curator note":
                data['curatorNote'] = value
            elif header == "Synonyms":
                vals = value.split(";")
                data['synonyms'] = vals
            elif header == "Comment":
                data['comment'] = value
            elif header == "Examples of usage":
                data['examples'] = value
            elif header == "Fuzzy set":
                data['fuzzySet'] = bool(value)
            elif header == "E-CigO":
                data['eCigO'] = bool(value)
            elif header == "	Proposer":
                pass
            elif header == "	Curation status":
                pass
            elif header == "Why fuzzy":
                data['fuzzyExplanation'] = value
            elif header == "Cross reference":
                vals = value.split(";")
                data['crossReference'] = vals
            elif header == "BFO entity":
                pass
            elif links and header == "Parent":
                vals = value.split(";")
                if len(vals)==1:
                    value=getIdForLabel(value)
                    data['parentTerm'] = f"/terms/{value}"
                else:
                    vals_to_add = []
                    for v in vals:
                        value = getIdForLabel(value)
                        vals_to_add.append(f"/terms/{v}")
                    data['parentTerm'] = vals_to_add
            elif links and re.match("REL '(.*)'",header):
                rel_name = re.match("REL '(.*)'",header).group(1)
                vals = value.split(";")
                vals_to_add = []
                for v in vals:
                    v = getIdForLabel(v)
                    vals_to_add.append(v)
                data[rel_name] = vals_to_add
            else:
                print(f"Unknown/ignored header: '{header}'")

    if create:
        headers = {"accept": "application/ld+json",
               "Content-Type": "application/ld+json"}
    else:
        headers = {"accept": "application/ld+json",
               "Content-Type": "application/merge-patch+json"}

    try:
        if create:
            urlstring = AOVOCAB_API + POST_TERMS
            r = requests.post(urlstring, json = data, headers=headers)
        else:
            urlstring = AOVOCAB_API + PATCH_TERMS.format(data['id'])
            r = requests.patch(urlstring, json = data, headers=headers)
        #print(f"Create returned {r.status_code}, {r.reason}")
        #if r.status_code in ['500',500,'400',400,'404',404]:
            #print(f"Problematic JSON: {json.dumps(data)}")
    except Exception as e:
        traceback.print_exc()
    return ( ( int(r.status_code), json.dumps(data) ) )


def deleteTermFromAddictOVocab(id):
    urlstring = AOVOCAB_API + DELETE_TERMS.format(id)

    r = requests.delete(urlstring)

    print(f"Delete {id}: returned {r.status_code}")


def getDefinitionForProntoTerm(term):
    if term.definition and len(term.definition)>0:
        return (term.definition)
    annots = [a for a in term.annotations]
    for a in annots:
        if isinstance(a, pronto.LiteralPropertyValue):
            if a.property == 'IAO:0000115':  # Definition
                return (a.literal)
            if a.property == 'IAO:0000600':  # Elucidation
                return (a.literal)
    if term.comment:
        return term.comment

# ---------- Main method execution below here ----------------

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

# load the dictionary for prefix to URI mapping

dict_file = 'inputs/prefix_to_uri_dictionary.csv'
prefix_dict = {}
reader = csv.DictReader(open(dict_file, 'r'))
for line in reader:
    prefix_dict[line['PREFIX']] = line['URI_PREFIX']

path = 'outputs'

addicto_files = []

for root, dirs_list, files_list in os.walk(path):
    for file_name in files_list:
        full_file_name = os.path.join(root, file_name)
        addicto_files.append(full_file_name)

entries = {}
bad_entries = []

# All the external content + hierarchy is in the file addicto_external.obo
# Must be parsed and sent to AOVocab.

externalonto = pronto.Ontology("addicto_external.obo")
for term in externalonto.terms():
    label_id_map[term.name] = term.id

# get the "ready" input data, indexed by ID
for filename in addicto_files:
    with open(filename, 'r') as csvfile:
        csvreader = csv.reader(csvfile)
        header = next(csvreader)

        for row in csvreader:
            rowdata = row
            id = rowdata[0]
            entries[id] = (header,rowdata)


# Check for which ones we created before and delete them
#allIds = getAllIDsFromAddictOVocab()  # NOT WORKING
# And delete them in preparation for the reload
for id in entries.keys(): #[id for id in allIds if len(id)<=15]:
    deleteTermFromAddictOVocab(id)

# Now delete additional external entries
for term in externalonto.terms():
    id = term.id
    if id not in entries.keys(): # Were already deleted
        deleteTermFromAddictOVocab(id)

# now create all our entities, first without links
for (header,test_entity) in entries.values():
    (status, jsonstr) = createTermInAddictOVocab(header,test_entity,prefix_dict)
    if status != 201:
        id = test_entity[0]
        print (status, ": Problem creating term ",id," with JSON: ",jsonstr)
        bad_entries.append(id)

# Now create additional external entries, first without links
for term in externalonto.terms():
    try:
        id = term.id
        external_header=["ID","Label","Definition","Parent"]
        # First round: Create those that are not in
        if id not in entries:
            label = term.name
            definition = getDefinitionForProntoTerm(term)
            parents = []
            for supercls in term.superclasses(distance=1):
                parents.append(supercls.id)
            parent = ";".join(parents)
            #print("TERM DATA: ",id,",",label,",",definition,",",parent)
            # Submit to AddictO Vocab
            (status, jsonstr) = createTermInAddictOVocab(external_header,[id,label,definition,parent],prefix_dict,create=True,links=False)
            if status != 201:
                print (status, ": Problem creating term ",id," with JSON: ",jsonstr)
                bad_entries.append(id)
    except ValueError:
        print("ERROR PROCESSING: ",id)
        continue

# Then add links (own entries)
for id in entries:
    (header,rowdata) = entries[id]
    # Patch it:
    (status,jsonstr) = createTermInAddictOVocab(header, rowdata, prefix_dict, create=False, links=True)
    if status != 200:
        print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)
        bad_entries.append(id)
else:
    print("ID not found in entries: ",id)

# Then add links (external entries)
for term in externalonto.terms():
    try:
        id = term.id
        external_header=["ID","Label","Parent"]
        # Second round: Should all be in. Patch with parents
        label = term.name
        parents = []
        for supercls in term.superclasses(distance=1):
            if supercls.id != id:
                parents.append(supercls.id)
        parent = ";".join(parents)

        print("TERM DATA: ",id,",",label,",",parent)

        # Patch it:
        (status,jsonstr) = createTermInAddictOVocab(external_header, [id,label,parent], prefix_dict, create=False, links=True)
        if status != 200:
            print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)
            bad_entries.append(id)
    except ValueError:
        print("ERROR PROCESSING: ",id)
        continue





# Find the ones that are not in?
#for (header,test_entity) in entries.values():
#    if test_entity[0] not in allIds:
#        print(test_entity[0])



