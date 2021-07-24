import os, os.path
import re
import openpyxl
import csv
import pronto

from whoosh import index
from whoosh.fields import SchemaClass, TEXT, KEYWORD, ID, STORED
from whoosh.analysis import StemmingAnalyzer
from whoosh.qparser import MultifieldParser


# Implementation of Google Cloud Storage for index
class BucketStorage(whoosh.filedb.filestore.RamStorage):

    def __init__(self, bucket):
        super().__init__()
        self.bucket = bucket
        self.filenameslist = []

    def save_to_bucket(self):
        for name in self.files.keys():
            with self.open_file(name) as source:
                print("Saving file",name)
                blob = self.bucket.blob(name)
                blob.upload_from_file(source)
        for name in self.filenameslist:
            if name not in self.files.keys():
                blob = self.bucket.blob(name)
                print("Deleting old file",name)
                self.bucket.delete_blob(blob.name)
                self.filenameslist.remove(name)

    def open_from_bucket(self):
        self.filenameslist = []
        for blob in bucket.list_blobs():
            print("Opening blob",blob.name)
            self.filenameslist.append(blob.name)
            f = self.create_file(blob.name)
            blob.download_to_file(f)
            f.close()


class OntologyContentSchema(SchemaClass):
    repo = ID(stored=True)
    spreadsheet = ID(stored=True)
    class_id = ID(stored=True)
    label = TEXT(stored=True)
    definition = TEXT(stored=True)
    parent = KEYWORD(stored=True)
    tobereviewedby = TEXT(stored=True)



def parseInputSheets(in_path,pattern):
    addicto_files = []
    entity_data = {}

    for root, dirs_list, files_list in os.walk(in_path):
        for file_name in files_list:
            if re.match(pattern, file_name):
                full_file_name = os.path.join(root, file_name)
                addicto_files.append(full_file_name)

    for file in addicto_files:
        try:
            wb = openpyxl.load_workbook(file)
        except Exception as e:
            print(e)
            print(Exception("Error! Not able to parse file: "+file))
            continue

        sheet = wb.active
        data = sheet.rows

        entity_data[file] = []

        header = [i.value for i in next(data)]

        for row in data:
            rowdata = [i.value for i in row]
            entity_data[file].append((header,rowdata))
    return (entity_data)



def reWriteEntityDataSet(repo_name,ix, sheet_name, entity_data):
    writer = ix.writer()
    mparser = MultifieldParser(["repo","spreadsheet"],
                                schema=ix.schema)
    writer.delete_by_query(mparser.parse("repo:"+repo_name+" AND spreadsheet:"+sheet_name))
    writer.commit()
    writer = ix.writer()
    for (header,rowdata) in entity_data:
        if "ID" in header:
            class_id = rowdata[header.index("ID")]
        else:
            class_id = None
        if "Label" in header:
            label = rowdata[header.index("Label")]
        else:
            label = None
        if "Definition" in header:
            definition = rowdata[header.index("Definition")]
        else:
            definition = None
        if "Parent" in header:
            parent = rowdata[header.index("Parent")]
        else:
            parent = None

        if class_id or label or definition or parent:
            writer.add_document(repo=repo_name,
                    spreadsheet=sheet_name.replace('./',''),
                    class_id=(class_id if class_id else None),
                    label=(label if label else None),
                    definition=(definition if definition else None),
                    parent=(parent if parent else None) )
    writer.commit(optimize=True)


def reIndexAddictO(create=True):
    os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")
    in_path = 'inputs'
    pattern = 'AddictO(.*).xlsx'

    entity_data = parseInputSheets(in_path, pattern)

    # Connect to Google cloud
    from google.cloud import storage
    # onto-spread-ed google credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/hastingj/Work/Python/onto-edit/ontospreaded.json'
    client = storage.Client()
    bucket = client.get_bucket('index-spread-ed-dev')
    storageb = BucketStorage(bucket)
    storageb.open_from_bucket()
    if create:
        schema = OntologyContentSchema()
        ix = storageb.create_index(schema)
    else:
        ix = storageb.open_index()
    for sheet in entity_data:
        reWriteEntityDataSet("AddictO",ix,sheet, entity_data[sheet])
    ix.close()
    storageb.save_to_bucket()


def reIndexBCIO():
    os.chdir("/Users/hastingj/Work/Onto/my-hbcp-fork")
    in_path = '.'
    pattern = '(.*).xlsx'

    entity_data = parseInputSheets(in_path, pattern)

    # Connect to Google cloud
    from google.cloud import storage
    # onto-spread-ed google credentials
    os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/hastingj/Work/Python/onto-edit/ontospreaded.json'
    client = storage.Client()
    bucket = client.get_bucket('index-spread-ed-dev')
    storageb = BucketStorage(bucket)
    storageb.open_from_bucket()

    #schema = OntologyContentSchema()
    ix = storageb.open_index()
    for sheet in entity_data:
        reWriteEntityDataSet("BCIO",ix, sheet, entity_data[sheet])
    ix.close()
    storageb.save_to_bucket()



#### Main function execution below here

def main():

# Add a field in the index:
#writer.add_field("tobereviewedby", whoosh.fields.TEXT(stored=True))
#writer.commit()
#writer = ix.writer()


#    os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")
#    in_path = 'inputs'
#    pattern = 'AddictO(.*).xlsx'

#    entity_data = parseInputSheets(in_path, pattern)

    # Connect to Google cloud
#    from google.cloud import storage
    # onto-spread-ed google credentials
#    os.environ['GOOGLE_APPLICATION_CREDENTIALS']='/Users/hastingj/Work/Python/onto-edit/ontospreaded.json'
#    client = storage.Client()
#    bucket = client.get_bucket('index-spread-ed')
#    storage = BucketStorage(bucket)
#    storage.open_from_bucket()

#    schema = OntologyContentSchema()
    #ix = storage.create_index(schema)
#    writeEntityData("AddictO",ix,entity_data)
#    storage.save_to_bucket()


if __name__ == "__main__":
    main()


#def delete_blob(bucket_name, blob_name):
#    """Deletes a blob from the bucket."""
#    # bucket_name = "your-bucket-name"
#    # blob_name = "your-object-name"
#    from google.cloud import storage
#    storage_client = storage.Client()

#    bucket = storage_client.bucket('index-spread-ed')
#    blob = bucket.blob('')
#    blob.delete()

#    print("Blob {} deleted.".format(blob_name))

# blobs = client.list_blobs(bucket)


# Then do other things...
#blob = bucket.get_blob('static/index.txt')

#print(blob.download_as_string())

#blob.upload_from_string('New contents!')

#blob2 = bucket.blob('remote/path/storage.txt')
#blob2.upload_from_filename(filename='/local/path.txt')