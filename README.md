# Demo-Dialogue-Systems---English
This is a demo example of an ontology driven dialogues system, which uses set of ontologies in diggerent subject areas as a main knowlege store.

The system has three main components: 

client_service includes Django applications for the user web interface representation. It provides display and operation of the user interface, pre-processing of incoming texts, preparation for display of received responses. Also, this service performs the functions of logging the history of dialogues. In addition, certain modules of this application perform the functions of an intermediate point of transmission of messages between other services of the system.
    
ontology_service is a Flask application which operates as a micro-service and dealing with ontologies. Warning: queries are executed directly by this module using the RDFlib Python package, which performs extermely slow. For production change in to the endpoint of a reliable and fasr RDF tripples store like Jena Fuseki.
    
sparql_converter is a Flask application also a micro-service responsible for formation of SPARQL queries according to the input users' phrases. 
    
For the system to work, you should create a database on MongoDB that contains the following collections: AdditionalData, AnswersCache, ConverterIDStore, ConverterResults, Ontologies, OntologyIDStore, OntologyResults. The Ontologies collection contains OWL ontologies and must be pre-populated. The Ontologies collection contains the ontologies available in the system, their names and keywords in the format: 

    id: identifier assigned automatically by MongoDB;
    name: ontology name;
    ontology: the OWL ontology itself;
    keywords: a list of concepts included in this ontology

You should also create a database under PostgreSQL, to which the user and the password. These parameters are to set in the settings.py file in the client_service.

There is a mongo_client_config_answers.xml configuration file with the AnswersCache target collection. This collection is used to temporarily store received responses.
The chatbot_config.xml file has a sparql_converter_url_common parameter. The chatbot_config.xml file has a cache_clean_time parameter, the value of which specifies the storage period of responses for repeated accelerated issuance (bypassing formal queries to the ontology). The time is given in seconds.

The application has a keywords_generators directory, which contains software modules that automatically generate keywords.json, ontology_entities.json, and tree_entities.json files, which are used in procedures to bring entities selected from a user to those contained in the values of vertices and/or predicates ontological graph, as well as for the screening of concepts unknown to the system. 
The tree.xml file contains the decision tree that is used in the semantic analysis of the user's phrase.
The links_dict.json file contain links to the images files needed for the responses.
