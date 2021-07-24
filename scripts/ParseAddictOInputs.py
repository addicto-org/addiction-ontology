import os
import re
import openpyxl
import csv
import pronto
import distutils
import distutils.util

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")


def getIdForLabel(value):
    if value in label_id_map.keys():
        return ( label_id_map[value] )
    if value in label_id_map.values():
        return value  # already an ID
    if value.lower() in label_id_map.keys():
        return ( label_id_map[value.lower()] )
    if value.strip() in label_id_map.keys():
        return ( label_id_map[value.strip()] )
    if value.lower().strip() in label_id_map.keys():
        return ( label_id_map[value.lower().strip()] )
    raise ValueError (f"No ID found for {value}.")

def getLabelForID(value):
    if value in label_id_map.values():
        keys = [k for k,v in label_id_map.items() if v == value]
        return keys[0]
    else:
        return value

def getCorrectFormForLabel(value):
    if value in label_id_map.keys():
        return ( value )
    if value.lower() in label_id_map.keys():
        return ( value.lower() )
    if value.strip() in label_id_map.keys():
        return ( value.strip() )
    if value.lower().strip() in label_id_map.keys():
        return ( value.lower().strip() )

    return (value)


# Run the main processing:


in_path = 'inputs'
out_path = 'outputs'
os.makedirs(out_path,exist_ok=True)   # shouldn't exist, just for testing
pattern = 'AddictO(.*).xlsx'
addicto_files = []
CONVERT_TO_LOWERCASE = False

for root, dirs_list, files_list in os.walk(in_path):
    for file_name in files_list:
        if re.match(pattern, file_name):
            full_file_name = os.path.join(root, file_name)
            addicto_files.append(full_file_name)

addicto_files.remove('inputs/AddictO_Upper level.xlsx')

next_id = 100
digit_count = 7
total_good = 0
label_id_map = {}
external_entities = {}
num_entities = 0
num_ecigo = 0
num_good_ecigo = 0

# First get the accurate next_id based on the input files

for file in addicto_files:
    try:
        wb = openpyxl.load_workbook(file)
    except Exception as e:
        print(e)
        raise Exception("Error! Not able to parse file: "+file)

    sheet = wb.active
    data = sheet.rows

    header = [i.value for i in next(data)]
    if 'E-CigO' in header:
        eCigOCol = header.index('E-CigO')
        skip_ecig = False
    else:
        skip_ecig = True

    for row in data:
        rowdata = [i.value for i in row]
        num_entities = num_entities + 1
        if not skip_ecig:
            ecigo = rowdata[eCigOCol]
            if ecigo:
                try:
                    ecigo = int(ecigo)
                except:
                    try:
                        ecigo = distutils.util.strtobool(ecigo)
                    except:
                        print("Problem parsing value ",ecigo,"in sheet",sheet)
                        ecigo = True
                if ecigo and int(ecigo) == 1:
                    num_ecigo = num_ecigo + 1

        if rowdata[0] and "ADDICTO:" in rowdata[0]:
            idStr = rowdata[0]
            idStr = idStr[(idStr.rindex(':')+1):]
            id = int(idStr)
            if id >= next_id:
                next_id = id+1

print(next_id)

# Now do the main parsing

for file in addicto_files:
    try:
        wb = openpyxl.load_workbook(file)
    except Exception as e:
        print(e)
        raise Exception("Error! Not able to parse file: "+file)

    sheet = wb.active
    data = sheet.rows
    good_entities = {}

    rel_columns = {}

    header = [i.value for i in next(data)]
    if 'E-CigO' in header:
        eCigOCol = header.index('E-CigO')
        skip_ecig = False
    else:
        skip_ecig = True

    label_column = [i for (i,j) in zip(range(len(header)),header) if j=='Label'][0]
    def_column = [i for (i,j) in zip(range(len(header)),header) if j=='Definition'][0]
    parent_column = [i for (i,j) in zip(range(len(header)),header) if j=='Parent'][0]
    if "REL 'has role'" in header:
        rel_columns['has role'] = [i for (i,j) in zip(range(len(header)),header) if j=="REL 'has role'"][0]
    if "REL 'has part'" in header:
        rel_columns['has part'] = [i for (i,j) in zip(range(len(header)),header) if j=="REL 'has part'"][0]

    for row in data:
        rowdata = [i.value for i in row]

        label = rowdata[label_column]
        if label:
            label = label.strip()
        defn = rowdata[def_column]
        parent = rowdata[parent_column]
        if parent:
            parent = parent.strip()

        if label and defn and parent:
            if len(label)>0 and len(defn)>0 and len(parent)>0:
                if label in good_entities.keys():
                    print(f"Appears to be a duplicate label: {label} in {file}")
                good_entities[label] = rowdata

                if not skip_ecig:
                    ecigo = rowdata[eCigOCol]
                    if ecigo:
                        try:
                            ecigo = int(ecigo)
                        except:
                            try:
                                ecigo = distutils.util.strtobool(ecigo)
                            except:
                                print("Problem parsing value ",ecigo,"in sheet",sheet)
                                ecigo = True
                        if ecigo and int(ecigo) == 1:
                            num_good_ecigo = num_good_ecigo + 1

    # Not validating the parents strictly for now.
    print(f"In file {file}, {len(good_entities)} GOOD.")
    total_good = total_good + len(good_entities)

    # Assign them IDs DO THIS IN APP NOW
#    for (label,rowdata) in good_entities.items():
#        if not rowdata[0] or len(rowdata[0])==0:
#            rowdata[0] = "ADDICTO:"+str(next_id).zfill(digit_count)
#            next_id = next_id + 1
#        elif "ADDICTO:" in rowdata[0]:
#            print(f"Found existing internal id {rowdata[0]}")
#        else:
#            print(f"Found external id {rowdata[0]}")
#            external_entities[rowdata[0]] = rowdata
#        label_id_map[label] = rowdata[0]

    # If the parent is good too, replace its label with its ID
    for (label,rowdata) in good_entities.items():
        parent = rowdata[parent_column]
        if parent in label_id_map.keys():
            rowdata[parent_column] = label_id_map[parent]
    # Same for relation columns
        for colname, colindex in rel_columns.items():
            if rowdata[colindex]:
                vals = rowdata[colindex].split(";")
                vals_updated = []
                for v in vals:
                    if v in label_id_map.keys():
                        vals_updated.append(label_id_map[v])
                    else:
                        vals_updated.append(v)
                rowdata[colindex] = ";".join(vals_updated)

    # Write to modified files for sending to database
    filename = file.replace(in_path,out_path).split(sep=".")[0] + ".csv"

    with open(filename, 'w') as file:
        writer = csv.writer(file)
        writer.writerow(header)
        for rowdata in good_entities.values():
            writer.writerow(rowdata)

with open('imports/external-entities.csv','w') as file:
    writer = csv.writer(file)
    for rowdata in external_entities.values():
        writer.writerow(rowdata)

print(f"Finished extracting {total_good} good entities, "
      f"{next_id-101} internal.")



if True:
    # # # -----------------------------
    # # # Only needed if IDs were added
    # Write newly generated IDs back to original files ID columns
    for file in addicto_files:

        CHANGED = False
        try:
            wb = openpyxl.load_workbook(file)
        except Exception as e:
            print(e)
            raise Exception("Error! Not able to parse file: "+file)

        sheet = wb.active
        data = sheet.rows

        header = [i.value for i in next(data)]

        label_column = [i for (i,j) in zip(range(len(header)),header) if j=='Label'][0]
        parent_column = [i for (i,j) in zip(range(len(header)),header) if j=='Parent'][0]

        for row in data:
            label = row[label_column].value
            if CONVERT_TO_LOWERCASE and label:
                row[label_column].value = label[0].lower() + label[1:]
                CHANGED = True
            parent = row[parent_column].value
            if CONVERT_TO_LOWERCASE and parent:
                row[parent_column].value = parent[0].lower() + parent[1:]
            if label in label_id_map:
                if not row[0].value or len(row[0].value)==0:
                    row[0].value = label_id_map[label]
                    CHANGED = True

        if CHANGED:
            wb.save(file)






# Get the external entities from the file and display in the right format for the imports

#file = 'imports/external-entities.csv'
#with open (file, 'r') as csvfile:
#    csvreader = csv.reader(csvfile)

#    for row in csvreader:
#        rowdata = row
#        id = rowdata[0]
#        label = rowdata[1]
#        if "CHEBI" in id:
#            print(label, ' [', id, ']', sep='', end=';')


# Do this only when external entities change
if False:

    # External parents/targets of relations:
    # We need to load the information for these from their source ontologies, where they are not included as rows in the spreadsheets.
    # Prepare subsets from several ontologies and merge them

    from ontoutils.robot_wrapper import RobotImportsWrapper

    robotWrapper = RobotImportsWrapper(robotcmd='~/Work/Onto/robot/robot',cleanup=False)
    robotWrapper.processImportsFromExcel(importsFileName='imports/External_Imports.xlsx',
                                            importsOWLURI='http://addictovocab.org/addicto_external.owl',
                                            importsOWLFileName = 'addicto_external.owl',
                                            ontologyName = 'ADDICTO')
    robotWrapper.addAdditionalContent(extraContentTemplate = 'imports/External_Imports_New_Parents.csv',                                         importsOWLURI='http://addictovocab.org/addicto_external.owl',importsOWLFileName = 'addicto_external.owl')

    robotWrapper.addAdditionalContent(extraContentTemplate = 'imports/External_Imports_New_Labels.csv',                                         importsOWLURI='http://addictovocab.org/addicto_external.owl',importsOWLFileName = 'addicto_external.owl')

    robotWrapper.removeProblemMetadata(importsOWLURI='http://addictovocab.org/addicto_external.owl',importsOWLFileName = 'addicto_external.owl', metadataURIFile = "problem-metadata.txt")

    robotWrapper.createOBOFile(importsOWLURI='http://addictovocab.org/addicto_external.owl',importsOWLFileName = 'addicto_external.owl')



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




# Merge into a single spreadsheet for creating an input file for ROBOT to create an OWL file (entries built in submit to addicto vocab file)
# First get merger of used headers
all_headers = []
headers_to_exclude = ['AO sub-ontology', 'Upper level', 'Fuzzy set', 'E-CigO', 'Proposer', 'Curation status', 'Why fuzzy', 'Cross reference', 'Type']
rel_mappings = {'has part':'[BFO:0000051]',
                'has role': '[RO:0000087]',
                'Derives from':'[RO:0001000]',
                'is about' :'[IAO:0000136]',
                'contains' : '[RO:0001019]'
                }
for id in entries:
    (header,rowdata) = entries[id]
    for item in header:
        if item not in all_headers and item not in headers_to_exclude:
            all_headers.append(item)

all_row_data = []

for id in entries:
    (header,rowdata) = entries[id]
    new_rowdata = []

    # exclude external entities
    if "ADDICTO" not in rowdata[0]:
        continue

    # exclude entities with nonexistent parents
    parentStr = rowdata[header.index('Parent')]
    parentVals = parentStr.split(";")
    parents = []
    for p in parentVals:
        m = re.search(r"\[([A-Za-z0-9:]+)\]", p)
        if m:
            p = m.group(1)
            print ("Found match:", m, "=>", p)
        if re.fullmatch("[A-Za-z]*:(\d)*",p):
            #print("Got ID-form parent: ",p, "replacing with label", getLabelForID(p))
            p = getLabelForID(p)
            parents.append(p)
        else:
            try:
                id = getIdForLabel(p)
            except ValueError:
                print("No ID found for ")
                continue # Not found
            else:
                parents.append(getCorrectFormForLabel(p)) # it has an id, but, we want the label
    if len(parents)>0:
        parent = ";".join(parents)
    else:
        print ("No usable parents in",parentStr)
        continue # SKIP THIS ENTRY

    for h in all_headers:
        if h in header:
            if h == 'Parent':
                new_rowdata.append(parent)
            else:
                i = header.index(h)
                val = rowdata[i]
                new_rowdata.append(val)
        else:
            new_rowdata.append('')
    all_row_data.append(new_rowdata)


inputFileName  = 'AddictO-own-merged.xlsx'


from openpyxl import Workbook
wb = Workbook()
sheet = wb.active
# Write header
for i, v in enumerate(all_headers):
    for mp in rel_mappings.keys():
        if mp in v:
            v = v + " "+rel_mappings[mp]
    sheet.cell(row=1,column=i+1).value = v
# Write values
for i, line in enumerate(all_row_data):
    for k, val in enumerate(line):
        sheet.cell(row=i+2, column=k+1).value = val
wb.save(inputFileName)


#from importlib import reload
#reload(ontoutils.robot_wrapper)

from ontoutils.robot_wrapper import RobotTemplateWrapper
robotWrapper = RobotTemplateWrapper(robotcmd='~/Work/Onto/robot/robot')

csvFileName = robotWrapper.processClassInfoFromExcel(inputFileName)


## EXECUTE THE ROBOT COMMAND AS A SUB-PROCESS

owlFileName = "addicto.owl"
IRI_PREFIX = 'http://addictovocab.org/'
ID_PREFIX = '\"ADDICTO: '+IRI_PREFIX+'ADDICTO_\"'
ONTOLOGY_IRI = IRI_PREFIX+owlFileName
dependency='addicto_external.owl'


robotWrapper.createOntologyFromTemplateFile(csvFileName, dependency, IRI_PREFIX, ID_PREFIX, ONTOLOGY_IRI,owlFileName)

from ontoutils.robot_wrapper import RobotImportsWrapper
robotWrapper = RobotImportsWrapper(robotcmd='~/Work/Onto/robot/robot',cleanup=False)
robotWrapper.createOBOFile(importsOWLURI='http://addictovocab.org/addicto.owl',importsOWLFileName = 'addicto.owl')

# Annotate with version information
# robot annotate --input addicto.owl --annotation rdfs:comment "The Addiction Ontology (AddictO) is an ontology being developed all aspects of addiction research." --annotation owl:versionInfo "2021-03-05" --ontology-iri "http://addictovocab.org/addicto.owl" --version-iri "http://addictovocab.org/addicto.owl/2021-03-05" --output addicto.owl
#
# Build the merged file for onto-edit
# robot merge --input addicto.owl convert --output addicto-merged.owx

