import pronto
import os

os.chdir("/Users/hastingj/Work/Onto/addiction-ontology/")


from ontoutils.robot_wrapper import RobotSubsetWrapper

IRI_PREFIX = 'http://addictovocab.org/'
ID_PREFIX = '\"ADDICTO: '+IRI_PREFIX+'ADDICTO_\"'

termId = "ADDICTO:0000279" # root -- product

robotWrapper = RobotSubsetWrapper(robotcmd='~/Work/Onto/robot/robot')

robotWrapper.createSubsetFrom('addicto.owl', 'addicto-products.csv', termId, ID_PREFIX, exportCsvHeaders='ID|LABEL|definition|SYNONYMS',exportSort="LABEL" )


