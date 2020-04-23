import os
import re
import openpyxl


os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

in_path = 'inputs'
out_path = 'temp'
os.makedirs(out_path,exist_ok=True)   # shouldn't exist, just for testing
pattern = 'AddictO(.*).xlsx'
addicto_files = []

for root, dirs_list, files_list in os.walk(path):
    for file_name in files_list:
        if re.match(pattern, file_name):
            full_file_name = os.path.join(root, file_name)
            addicto_files.append(full_file_name)


next_id = 1

for file in addicto_files:
    try:
        wb = openpyxl.load_workbook(file)
    except Exception as e:
        print(e)
        raise Exception("Error! Not able to parse file: "+file)

    sheet = wb.active
    data = sheet.rows

    header = [i.value for i in next(data)]
    print(header)

    for row in data:
        if row[0].value is None or len(row[0].value)==0:
            row[0].value = 'ADDICTO:'+str(next_id).zfill(6)
            next_id = next_id + 1

    wb.save(file.replace(in_path,out_path).replace(".xlsx","-updated.xlsx"))






