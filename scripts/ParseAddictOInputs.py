import os
import re
import openpyxl
import csv


os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

in_path = 'inputs'
out_path = 'outputs'
os.makedirs(out_path,exist_ok=True)   # shouldn't exist, just for testing
pattern = 'AddictO(.*).xlsx'
addicto_files = []

for root, dirs_list, files_list in os.walk(in_path):
    for file_name in files_list:
        if re.match(pattern, file_name):
            full_file_name = os.path.join(root, file_name)
            addicto_files.append(full_file_name)

next_id = 100
digit_count = 7
total_good = 0
label_id_map = {}
external_entities = {}


# First get the accurate next_id
for file in addicto_files:
    try:
        wb = openpyxl.load_workbook(file)
    except Exception as e:
        print(e)
        raise Exception("Error! Not able to parse file: "+file)

    sheet = wb.active
    data = sheet.rows

    for row in data:
        rowdata = [i.value for i in row]
        if rowdata[0] and "ADDICTO:" in rowdata[0]:
            idStr = rowdata[0]
            idStr = idStr[(idStr.rindex(':')+1):]
            id = int(idStr)
            if id >= next_id:
                next_id = id+1



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

    header = [i.value for i in next(data)] # is there a better way?
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
        defn = rowdata[def_column]
        parent = rowdata[parent_column]

        if label and defn and parent:
            if len(label)>0 and len(defn)>0 and len(parent)>0:
                if label in good_entities.keys():
                    print(f"Appears to be a duplicate label: {label} in {file}")
                good_entities[label] = rowdata

    # Not validating the parents strictly for now.
    print(f"In file {file}, {len(good_entities)} GOOD.")
    total_good = total_good + len(good_entities)

    # Assign them IDs
    for (label,rowdata) in good_entities.items():
        if not rowdata[0] or len(rowdata[0])==0:
            rowdata[0] = "ADDICTO:"+str(next_id).zfill(digit_count)
            next_id = next_id + 1
        elif "ADDICTO:" in rowdata[0]:
            print(f"Found existing internal id {rowdata[0]}")
        else:
            print(f"Found external id {rowdata[0]}")
            external_entities[rowdata[0]] = rowdata
        label_id_map[label] = rowdata[0]

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



# # # -----------------------------
# # # Only needed if IDs were added
# Write newly generated IDs back to original files ID columns
for file in addicto_files:

    try:
        wb = openpyxl.load_workbook(file)
    except Exception as e:
        print(e)
        raise Exception("Error! Not able to parse file: "+file)

    sheet = wb.active
    data = sheet.rows

    header = [i.value for i in next(data)]

    label_column = [i for (i,j) in zip(range(len(header)),header) if j=='Label'][0]

    for row in data:
        label = row[label_column].value
        if label in label_id_map:
            if not row[0].value or len(row[0].value)==0:
                row[0].value = label_id_map[label]

    wb.save(file)






# Get the external entities from the file and display in the right format for the imports

file = 'imports/external-entities.csv'
with open (file, 'r') as csvfile:
    csvreader = csv.reader(csvfile)

    for row in csvreader:
        rowdata = row
        id = rowdata[0]
        label = rowdata[1]
        if "CHEBI" in id:
            print(label, ' [', id, ']', sep='', end=';')




# External parents/targets of relations:
# We need to load the information for these from their source ontologies, where they are not included as rows in the spreadsheets.
# Prepare subsets from several ontologies and merge them

from ontoutils.robot_wrapper import RobotImportsWrapper

robotWrapper = RobotImportsWrapper(robotcmd='~/Work/Onto/robot/robot',cleanup=False)
robotWrapper.processImportsFromExcel(importsFileName='imports/External_Imports.xlsx',
                                        importsOWLURI='http://addictovocab.org/ontology/addicto_external.owl',
                                        importsOWLFileName = 'addicto_external.owl',
                                        ontologyName = 'ADDICTO')
robotWrapper.addAdditionalParents(importsParentsFileName = 'imports/External_Imports_New_Parents.csv',                                         importsOWLURI='http://addictovocab.org/ontology/addicto_external.owl',importsOWLFileName = 'addicto_external.owl')
