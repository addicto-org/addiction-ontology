import os

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")

from Bio import Entrez
import pronto
import time


def getCountAndIdList(query):
    Entrez.email = 'janna.hastings@ucl.ac.uk'
    handle = Entrez.esearch(db='pubmed',term=query)
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


def getCountForTermId(onto, termId):
    name = onto[termId].name
    searchExpression = "("+name+")"
    synonyms = [s.literal for s in onto[termId].annotations if s.property == 'IAO:0000118']
    for s in synonyms:
        searchExpression = searchExpression + "OR ("+s+")"
    (count,IdList) = getCountAndIdList(searchExpression)
    print("Search for ",termId,":",searchExpression," returned ", count, "hits")
    return ((termId,name,count,IdList))


def getCountForSubBranch(onto, rootTermId, results = {}):
    term = onto[rootTermId]
    subclasses = [sc for sc in term.subclasses(distance=1)]
    for sc in subclasses:
        if sc.id == rootTermId:
            continue
        elif sc.id in results.keys():
            continue
        else:
            time.sleep(0.2)  # Be sure not to hit the Entrez limit of queries per second
            results[sc.id] = getCountForTermId(onto,sc.id)
            results = getCountForSubBranch(onto,sc.id, results)
    return( results )





if __name__ == '__main__':

    onto = pronto.Ontology("addicto.obo")

    termId = "ADDICTO:0000279" # root -- product

    results = getCountForSubBranch(onto,termId)




