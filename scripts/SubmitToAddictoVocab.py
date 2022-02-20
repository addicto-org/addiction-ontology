import os
import csv
import urllib.request
import json
import re
import requests
import traceback
import pronto
import distutils
import distutils.util


AOVOCAB_API = "https://api.addictovocab.org/"
GET_TERMS_BY_LABEL = "terms?label={}&page={}&itemsPerPage={}"
GET_TERMS = "terms/{}"
POST_TERMS = "terms"
DELETE_TERMS = "terms/{}"
PATCH_TERMS = "terms/{}"

AUTH_STR = "X-AUTH-TOKEN"
AUTH_KEY = os.environ["ADDICTO_AUTH"]


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


def getFromAddictOVocabByLabel(label,pageNo=1,totPerPage=30):
    urlstring = AOVOCAB_API + GET_TERMS_BY_LABEL.format(label,pageNo,totPerPage)
    print(urlstring)

    r = requests.get(urlstring, headers={AUTH_STR:AUTH_KEY})
    #print(f"Get returned {r.status_code}")
    return ( r.json() )

def getFromAddictOVocab(id):
    urlstring = AOVOCAB_API + GET_TERMS.format(id)
    #print(urlstring)
    r = requests.get(urlstring)
    #print(f"Get returned {r.status_code}")
    if r.status_code == 404:
        return (r.status_code, None)
    else:
        return (r.status_code, r.json())

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
def createTermInAddictOVocab(header,rowdata, prefix_dict, create=True,links=False,revision_msg="Minor update"):
    data = {}
    for (value, headerval) in zip(rowdata,header):
        if value:
            if headerval == "ID":
                data['id'] = value
                data['uri'] = getURIForID(value, prefix_dict)
            elif headerval == "Label":
                data['label'] = value
            elif headerval == "Definition":
                data['definition'] = value
            elif headerval == "Definition source":
                data['definitionSource'] = value
            elif headerval == "Logical definition":
                data['logicalDefinition'] = value
            elif headerval == "Informal definition":
                data['informalDefinition'] = value
            elif headerval == "AO sub-ontology":
                data['addictoSubOntology'] = value
            elif headerval == "Curator note":
                data['curatorNote'] = value
            elif headerval == "Synonyms":
                vals = value.split(";")
                data['synonyms'] = vals
            elif headerval == "Comment":
                data['comment'] = value
            elif headerval == "Examples of usage":
                data['examples'] = value
            elif headerval == "Fuzzy set":
                if value:
                    try:
                        data['fuzzySet'] = bool(int(value))
                    except ValueError:
                        data['fuzzySet'] = bool(distutils.util.strtobool(value))
                else:
                    data['fuzzySet'] = False
            elif headerval == "E-CigO":
                if value:
                    try:
                        data['eCigO'] = bool(int(value))
                    except ValueError:
                        data['eCigO'] = bool(distutils.util.strtobool(value))
                else:
                    data['eCigO'] = False
            elif headerval == "Curator":
                pass
            elif headerval == "Curation status":
                if value in ['To Be Discussed','In Discussion']:
                    value = "Proposed"
                data['curationStatus'] = value
            elif headerval == "Why fuzzy":
                data['fuzzyExplanation'] = value
            elif headerval == "Cross reference":
                vals = value.split(";")
                data['crossReference'] = vals
            elif headerval == "BFO entity":
                pass
            elif links and headerval == "Parent":
                vals = value.split(";")
                if len(vals)==1:
                    try:
                        value=getIdForLabel(value)
                        data['parentTerm'] = f"/terms/{value}"
                    except ValueError:
                        print(f"No ID found for label {value}, skipping")
                        continue
                else:
                    for value in vals:
                        #value = vals[0]
                        try:
                            value = getIdForLabel(value)
                            data['parentTerm'] = f"/terms/{value}"
                            break
                        except ValueError:
                            print(f"No ID found for value {value}, skipping...")
                            continue
                    if 'parentTerm' not in data:
                        print(f"No usable parent found for {value}.")
                        continue
            elif links and re.match("REL '(.*)'",headerval):
                rel_name = re.match("REL '(.*)'",headerval).group(1)
                vals = value.split(";")
                vals_to_add = []
                for v in vals:
                    try:
                        v = '/terms/'+getIdForLabel(v)
                        vals_to_add.append(v)
                    except ValueError:
                        print(f"No ID found for linked value {v}, skipping.")
                if len(vals_to_add)>0:
                    if 'termLinks' not in data:
                        data['termLinks'] = []
                    data['termLinks'].append({'type':rel_name,
                                          'linkedTerms':vals_to_add})
            else:
                print(f"Unknown/ignored header: '{headerval}'")

    if 'eCigO' not in data:
        data['eCigO'] = False
    if 'fuzzySet' not in data:
        data['fuzzySet'] = False

    if create:
        headers = { AUTH_STR : AUTH_KEY,
               "accept": "application/ld+json",
               "Content-Type": "application/ld+json"}
    else:
        headers = { AUTH_STR : AUTH_KEY,
                "accept": "application/ld+json",
                "Content-Type": "application/merge-patch+json"}
        if data['curationStatus'] == 'Published':  # Revision msg needed
            data['revisionMessage'] = revision_msg

    #print(data)

    try:
        if create:
            urlstring = AOVOCAB_API + POST_TERMS
            r = requests.post(urlstring, json = data, headers=headers)
            status = r.status_code
        else:
            urlstring = AOVOCAB_API + PATCH_TERMS.format(data['id'])
            r = requests.patch(urlstring, json = data, headers=headers)
            status = r.status_code
        #print(f"Create returned {r.status_code}, {r.reason}")
        #if r.status_code in ['500',500,'400',400,'404',404]:
            #print(f"Problematic JSON: {json.dumps(data)}")
    except Exception as e:
        traceback.print_exc()
        status = None
    return ( ( status, json.dumps(data) ) )


def deleteTermFromAddictOVocab(id):
    urlstring = AOVOCAB_API + DELETE_TERMS.format(id)

    r = requests.delete(urlstring, headers = {AUTH_STR : AUTH_KEY})

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
        return (term.comment)
    return ("None")

# ---------- Main method execution below here ----------------

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

# load the dictionary for prefix to URI mapping

dict_file = 'scripts/prefix_to_uri_dictionary.csv'
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
revisionmsg="February 2022 ADDICTO release"

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



### Update entries with new data
### Try to create if update fails


# Patch if exists or else create first without links
for (header,test_entity) in entries.values():
    id = test_entity[0]
    # get it first
    (status,entry) = getFromAddictOVocab(test_entity[0])
    if status == 200:
        #print("Found existing entry: ",id)
        # Now check if existing status is 'published'. if yes don't patch without message... manually.
        existing_status = entry['curationStatus']
        if existing_status == 'published':
            #print("Not patching ",id," as already published.")
            # Only patch if changed. Get the latest revision:
            termRevision = entry['termRevisions'][0]
            for t in entry['termRevisions']:
                if 'modifiedAt' in t and  t['modifiedAt']>=termRevision['modifiedAt']:
                    termRevision=t
            print("Got latest revision mod. at",termRevision['modifiedAt'])
            termLabel = termRevision['label']
            termDef = termRevision['definition']
            if 'parentTerm' in termRevision:
                termParent = termRevision['parentTerm']
            else:
                termParent = ""

            newLabel = test_entity[header.index("Label")]
            newDef = test_entity[header.index("Definition")]
            newParent =getIdForLabel(test_entity[header.index('Parent')])
            newParent = f"/terms/{newParent}"
            CHANGED = False
            if termLabel != newLabel or termDef != newDef or termParent != newParent:
                print("PUBLISHED TERM CHANGED: ",id,"ORIG",termLabel,termDef,termParent,"CH TO",newLabel,newDef,newParent,"Patching...")
                # Patch it:
                (status,jsonstr) = createTermInAddictOVocab(header, test_entity, prefix_dict, create=False, links=True, revision_msg=revisionmsg)
                if status != 200:
                    print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)

        else:
            # Now patch.
            (status, jsonstr) = createTermInAddictOVocab(header,test_entity,prefix_dict, create=False, links=True)
            if status != 200:
                print("Error patching existing entry. Investigate: ",id, status, jsonstr)

    else:
        # Not found by ID. Try submit with post
        (status, jsonstr) = createTermInAddictOVocab(header,test_entity,prefix_dict)
        if status != 201:
            id = test_entity[0]
            print (status, ": Problem creating term ",id," with JSON: ",jsonstr)
            bad_entries.append(id)



# Try again after fixing problems

#bad_entries_first = bad_entries
#bad_entries = []


#for entry_id in bad_entries_first:
#    (header,test_entity) = entries[entry_id]
    #id = test
    # get it first
#    (entry,status) = getFromAddictOVocab(test_entity[0])
#    if status == 200:
#        print("Found existing entry: ",id)
        # Now check if existing status is 'published'. if yes don't patch without message... manually.
#        existing_status = entry['curationStatus']
#        if existing_status == 'published':
#            print("Not patching ",id," as already published.")
#        else:
#            # Now patch.
#            (status, jsonstr) = createTermInAddictOVocab(header,test_entity,prefix_dict, create=False, links=True)
#            if status != 200:
#                print("Error patching existing entry. Investigate: ",id, status, jsonstr)#
#
#    else:
#        # Not found by ID. Try submit with post
#        (status, jsonstr) = createTermInAddictOVocab(header,test_entity,prefix_dict)
#        if status != 201:
#            id = test_entity[0]
#            print (status, ": Problem creating term ",id," with JSON: ",jsonstr)
#            bad_entries.append(id)


# Now create additional external entries, first without links
for term in externalonto.terms():
    try:
        id = term.id
        external_header=["ID","Label","Definition","Parent","Curation status"]

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
            (status, jsonstr) = createTermInAddictOVocab(external_header,[id,label,definition,parent,"External"],prefix_dict,create=False,links=False)
            if status != 200:
                (status, jsonstr) = createTermInAddictOVocab(external_header,[id,label,definition,parent,"External"],prefix_dict,create=True,links=False)
                if status != 201:
                    print (status, ": Problem creating term ",id," with JSON: ",jsonstr)
                    bad_entries.append(id)
    except ValueError:
        print("ERROR PROCESSING: ",id)
        continue


# Then add links (own entries)
for id in entries:
    (header,rowdata) = entries[id]
    # Check if need to patch it:
    (status, entry) = getFromAddictOVocab(id)
    if status == 200:
        if entry['curationStatus']!= 'published':
            (status,jsonstr) = createTermInAddictOVocab(header, rowdata, prefix_dict, create=False, links=True)
            if status != 200:
                print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)
                bad_entries.append(id)


# Then add links (external entries)
for term in externalonto.terms():
    try:
        id = term.id
        external_header=["ID","Label","Definition","Parent","Curation status"]
        # Second round: Should all be in. Patch with parents
        label = term.name
        definition = getDefinitionForProntoTerm(term)
        parents = []
        for supercls in term.superclasses(distance=1):
            if supercls.id != id:
                parents.append(supercls.id)
        parent = ";".join(parents)

        print("TERM DATA: ",id,",",label,",",parent)

        # Patch it:
        (status,jsonstr) = createTermInAddictOVocab(external_header, [id,label,definition,parent,"External"], prefix_dict, create=False, links=True)
        if status != 200:
            print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)
            bad_entries.append(id)
    except ValueError:
        print("ERROR PROCESSING: ",id)
        continue



### Add parents for published entries i!!!

for id in entries:
    (header,rowdata) = entries[id]
    # Check if need to patch it:
    (status, entry) = getFromAddictOVocab(id)
    if status == 200:
        if entry['curationStatus'] == 'published':
            if 'parentTerm' not in entry['termRevisions'][0].keys():
                #print("Parent of ",id,"is",entry['termRevisions'][0]['parentTerm'])
                print("Term",id,"appears to have no parent. Patching...")
                (header,rowdata) = entries[id]
                # Patch it:
                (status,jsonstr) = createTermInAddictOVocab(header, rowdata, prefix_dict, create=False, links=True, revision_msg=revisionmsg)
                if status != 200:
                    print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)




### ERRORS FROM LAST RUN


# Status rejected
#to_redo_422 = ["ADDICTO:0000714","ADDICTO:0000770", "ADDICTO:0000716", "ADDICTO:0000717", "ADDICTO:0000718", "ADDICTO:0000202", "ADDICTO:0000860", "ADDICTO:0000640" , "ADDICTO:0000146", "ADDICTO:0000883", "ADDICTO:0000884", "ADDICTO:0000149", "ADDICTO:0000456","ADDICTO:0000405", "ADDICTO:0000149","ADDICTO:0000479"]

# Missing parent -- should have been fixed on the next iteration?
#to_redo_400 = ["ADDICTO:0000847","ADDICTO:0000342","ADDICTO:0000351","ADDICTO:0000523","ADDICTO:0000352","ADDICTO:0000835", "ADDICTO:0000374", "ADDICTO:0000375", "ADDICTO:0000713", "ADDICTO:0000776", "ADDICTO:0000781", "ADDICTO:0000780", "ADDICTO:0000389", "ADDICTO:0000842", "ADDICTO:0000391", "ADDICTO:0000513", "ADDICTO:0000846", "ADDICTO:0000405", "ADDICTO:0000849", "ADDICTO:0000938" , "ADDICTO:0000941", "ADDICTO:0000410", "ADDICTO:0000870", "ADDICTO:0000872", "ADDICTO:0000873", "ADDICTO:0000191", "ADDICTO:0000892", "ADDICTO:0000919", "ADDICTO:0000195", "ADDICTO:0000532", "ADDICTO:0000534", "ADDICTO:0000748" , "ADDICTO:0000906", "ADDICTO:0000820", "ADDICTO:0000754", "ADDICTO:0000258", "ADDICTO:0000259", "ADDICTO:0000260", "ADDICTO:0000261", "ADDICTO:0000755", "ADDICTO:0000759" , "ADDICTO:0000630", "ADDICTO:0000631", "ADDICTO:0000108", "ADDICTO:0000112", "ADDICTO:0000113", "ADDICTO:0000649", "ADDICTO:0000634", "ADDICTO:0000644", "ADDICTO:0000637", "ADDICTO:0000638", "ADDICTO:0000635", "ADDICTO:0000636" , "ADDICTO:0000648", "ADDICTO:0000633", "ADDICTO:0000665", "ADDICTO:0000679", "ADDICTO:0000700", "ADDICTO:0000655", "ADDICTO:0000656", "ADDICTO:0000658", "ADDICTO:0000666", "ADDICTO:0000672", "ADDICTO:0000669", "ADDICTO:0000670", "ADDICTO:0000667", "ADDICTO:0000668", "ADDICTO:0000675", "ADDICTO:0000722", "ADDICTO:0000680", "ADDICTO:0000686", "ADDICTO:0000683", "ADDICTO:0000684", "ADDICTO:0000681", "ADDICTO:0000682", "ADDICTO:0000688", "ADDICTO:0000651", "ADDICTO:0000689", "ADDICTO:0000710", "ADDICTO:0000729", "ADDICTO:0000701", "ADDICTO:0000707", "ADDICTO:0000704", "ADDICTO:0000705", "ADDICTO:0000702", "ADDICTO:0000703", "ADDICTO:0000709", "IAO:0000310", "ADDICTO:0000170", "ADDICTO:0000152", "ADDICTO:0000171", "ADDICTO:0000477", "ADDICTO:0000479"]

# Need revision message
#published_status = ["ADDICTO:0000367", "ADDICTO:0000715", "ADDICTO:0000381", "ADDICTO:0000399", "ADDICTO:0000406", "ADDICTO:0000308", "ADDICTO:0000893", "ADDICTO:0000737" , "ADDICTO:0000794", "ADDICTO:0000198", "ADDICTO:0000199", "ADDICTO:0000200", "ADDICTO:0000201", "ADDICTO:0000743",  "ADDICTO:0000207", "ADDICTO:0000209", "ADDICTO:0000531", "ADDICTO:0000212", "ADDICTO:0000923", "ADDICTO:0000232", "ADDICTO:0000231", "ADDICTO:0000897", "ADDICTO:0000246", "ADDICTO:0000245", "ADDICTO:0000535", "ADDICTO:0000249", "ADDICTO:0000254", "ADDICTO:0000294", "ADDICTO:0000257", "ADDICTO:0000295", "ADDICTO:0000271", "ADDICTO:0000279" , "ADDICTO:0000292", "ADDICTO:0000907", "ADDICTO:0000303", "ADDICTO:0000305", "ADDICTO:0000311", "ADDICTO:0000316"]



### SUBMIT JUST ONE CHANGE TO AN ENTRY WITH A SPECIFIED ID:

# Find an entry with a given ID
# Patch it (in full) with a revision message

# idtochange = 'ADDICTO:0000308' # FDA tobacco product.
# idstochange = ['ADDICTO:0000308','ADDICTO:0000200','ADDICTO:0000201','ADDICTO:0000207','ADDICTO:0000295','ADDICTO:0000279','ADDICTO:0000292','ADDICTO:0000303','ADDICTO:0000305','ADDICTO:0000311']

idstochange = published_status
revisionmsg="November ADDICTO release"

for idtochange in idstochange:
    (header,rowdata) = entries[idtochange]
    # Patch it:
    (status,jsonstr) = createTermInAddictOVocab(header, rowdata, prefix_dict, create=False, links=True, revision_msg=revisionmsg)
    if status != 200:
        print(status, ": Problem patching term ",id,"with JSON: ",jsonstr)




## id to remove
idstoremove = "ADDICTO:0000746"




