
import os
import openpyxl
from collections import Counter
import argparse
import sys

if __name__ == '__main__':

    parser=argparse.ArgumentParser()
    parser.add_argument('--path', '-i',help='Name of the path')
    
    args=parser.parse_args()
    path = args.path
    
    
    if args is None :
        parser.print_help()
        sys.exit('Not enough arguments. Expected at least -i "Path to ontology folder" ')

    

    id_list = []
    label_list = []
    # path = "/home/tom/Documents/PROGRAMMING/Python/addiction-ontology"
    files = os.listdir(path + "/inputs")

    allInfo = []
    for f in files:
        inputFileName = path + "/inputs/" + f
        print("checking: '", inputFileName, "'...")
        try:
            wb = openpyxl.load_workbook(inputFileName)
            sheet = wb.active
            data = sheet.rows
            rows = []
            header = [i.value for i in next(data)]

            for row in sheet[2:sheet.max_row]:
                values = {}
                values["Sheet"] = f
                for key, cell in zip(header, row):
                    if key == "ID" and cell.value != None:
                        id_list.append(cell.value) # just the ID's
                        values[key] = cell.value
                    if key == "Label" and cell.value != None:
                        values[key] = cell.value
                allInfo.append(values) # all Sheet, ID, Label
        except Exception as e:
            print("Got an error ",e)


    #check from https://codefather.tech/blog/python-check-for-duplicates-in-list/
    dups_list = [key for key in Counter(id_list).keys() if Counter(id_list)[key]>1] #checks for duplicates in combined ID list!
    # print("dups_list is: ", dups) #got list of duplicates
    returnList = []
    for d in allInfo: # loop over all rows
        instance = {}
        for k, v in d.items(): # row
            if k == "ID":
                for i in dups_list:
                    if v == i and v != None and v.strip() != '': # ID of duplicate position in allInfo, which is not blank
                        instance[k] = v # common ID
                        instance["Label"] = d["Label"]
                        instance["Sheet"] = d["Sheet"]  
                        instance["Label2"] = ""  
                        instance["Sheet2"] = "" 
        firstDup = True  
        if instance: # got a duplicate from dups_list
            #check returnList for ID, append Label2, Sheet2:
            for t in returnList: #check if we already saved this ID details #todo: do we want to check for 3 or more duplicates?
                for k, v in t.items():
                    if k == "ID":
                        if v == instance["ID"] and v != None and v.strip() != '': 
                            #update second duplicate in place:
                            t.update(Label2 = instance["Label"])
                            t.update(Sheet2 = instance["Sheet"])
                            firstDup = False # don't do first duplicate again
            if firstDup: # first duplicate
                returnList.append(instance) 
    print("All duplicates:")  
    print("")
    count = 0;
    for r in returnList:
        count = count + 1
        print(count, ": ", r)  
        print("")     
            