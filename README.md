# Demo-Dialogue-Systems---English

## Overview
This is a demo example of an ontology-driven dialogues system, which uses a set of ontologies in different subject areas as a main knowledge store.

The system has three main components: 

client_service includes Django applications for the user web interface representation. It provides display and operation of the user interface, pre-processing of incoming texts, and preparation for the display of received responses. Also, this service performs the function of logging the history of dialogues. In addition, certain modules of this application perform the functions of an intermediate point of transmission of messages between other services of the system.
    
ontology_service is a Flask application which operates as a micro-service and deals with ontologies. Warning: queries are executed directly by this module using the RDFlib Python package, which performs extremely slowly. For production, you better change the endpoint of the ontology to a reliable and fast RDF triples store like Jena Fuseki.
    
sparql_converter is a Flask application also a micro-service responsible for the formation of SPARQL queries according to the input users' phrases. 

Each of the components is a separate service than could be set up individualy.
    
For the system to work, you should create a database on MongoDB that contains the following collections: AdditionalData, AnswersCache, ConverterIDStore, ConverterResults, Ontologies, OntologyIDStore, and OntologyResults. The Ontologies collection contains OWL ontologies and must be pre-populated. The Ontologies collection contains the ontologies available in the system, their names and keywords in the format: 

    id: identifier assigned automatically by MongoDB;
    name: ontology name;
    ontology: the OWL ontology itself;
    keywords: a list of concepts included in this ontology

You should also create a database under PostgreSQL, to which the user and the password. These parameters are to be set in the settings.py file in the client_service.

There is a mongo_client_config_answers.xml configuration file with the AnswersCache target collection. This collection is used to temporarily store received responses.
The chatbot_config.xml file has a sparql_converter_url_common parameter. The chatbot_config.xml file has a cache_clean_time parameter, the value of which specifies the storage period of responses for repeated accelerated issuance (bypassing formal queries to the ontology). The time is given in seconds.

It is assumed that entities stored in the ontology nodes are verbose. So it is quite unlikely for them to appear in a user's phrase in the direction close shape. So a procedure is needed to substitute the extracted terms with the closest present in the ontology or/and in the desition tree. In this case, both extension and shrinking of the context may occur. To simplify such a procedure performance the keywords.json files are included (name may vary from the ontology name because there could be several of such files each of them relates to the certain ontology), which are used in procedures to bring entities selected from a user to those contained in the values of vertices and predicates of ontological graphs, as well as for the screening of concepts unknown to the system.  

The tree.xml file contains the decision tree that is used in the semantic analysis of the user's phrase.

The links_dict.json file contains links to the image files needed for the responses. 

## Description and usage of the components

### client_service
It is a main shell that not only implements the users web interface but also preprocessing and postprocessing of the data.
Because it is a Django application it has the appropriate known structure. SDG directory contains the standard files for a Django progect settings. Probably the few things you need to change here are:

    specify the hosts or IP in the ALLOWED_HOSTS in the settings.py file
    put your DATABASES settings (such as 'ENGINE', 'NAME', 'PASSWORD', 'USER', 'HOST', and 'PORT') in in the settings.py file
    turn off/on the DEBUG in the settings.py file
    
--    




