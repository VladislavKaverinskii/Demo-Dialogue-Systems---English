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
    
The main files of the application business logic are in the directory SDGbot. Among them the most important is views.py. The only two models are CommunicationAct and UserDialogPosition. CommunicationAct model is responsible for interaction between services and user storage. UserDialogPosition is needed for the dialogues histories store and restore after the page reloading. UserDialogPosition notes are normally automatically periodically deleted from the database when expire.

In the *static* directory among other things, pdf files are stored to be displayed in the dialogue system interface. They represent the sources the ontologies are based on.

To deal with each of the ontology and with the subject area in belongs to there are three sub-urls. Here thy are: 

    path('', csrf_exempt(views.StartConversation.as_view()), name="index"),
    path('european_parlament/', csrf_exempt(views.StartConversationEP.as_view()), name="index_2"),
    path('aliyev/', csrf_exempt(views.StartConversationAliyev.as_view()), name="index_3")

The entry point of the application in file *manage.py* in the root directory of the application. Its behaviour obey the general rules of the Django applications. 

Files keywords.json and keywords_aliyev.json represent named entities from the different ontologies used in the system. These files are created automatically from the OWL ontologies and have the following structure. It is a dictionary with the next high level keys:

    "class_names_dict" - entities relate to the OWL classes
    "individual_names_dict" - entities relate to the OWL individuals
    "pradicates" - entities relate to the named specific predicates from the ontology
    "defined_classes" - names of the classes that are linked with specific predicates
    
Such a classification simplifies the further entities substitution to SPARQL queries.

The "class_names_dict" has keys which represent the entities of OWL classes as they are given in the ontology. To them corresponds dictionaries with a single key "words". It includes the list of lemmatized words ("text" key) and the parts of speech ("POS" key) for each word from the corresponding named entity. Parts of speech are marked as it assumed in the NLTK.

The items of the "pradicates" section except the similar “words” part have also a key in "in_class" that represents the list of classes this named predicate belongs to. The same is done for the "individual_names_dict" items. 

links_dict.json file and the similar relate to the different ontologies includes keys which correspond to the phrases in the responses tests that require an outer recourse link. To each of the key corresponds a list of three items which are:

    1 – the link itself (URI);
    2 – name of the link to be displayed (if null merely the URL will de shown)
    3 – the OWL class name in relates to

Most of the application settings are gathered in the file chatbot_config.xml. It has the following container items:

    <name> - the name of the application
    <sparql_converter_name> - the name of the SPARQL converter used in the system
    <sparql_converter_url> - the entry point of the SPARQL converter service API
    <sparql_converter_password> the password of the SPARQL converter service API
    <ontology_agent_name> - the name of the ontology agent (service) used in the system
    <ontology_agent_url> - the entry point of the ontology agent API
    <ontology_agent_password> - the password of the ontology agent API
    <conversation_limitation> - the time (in seconds) how long a current dialogue with a certain user could be kept idle (without new messages), i.e. the session duration
    <garbage_deleting> - time (in seconds) how long the temporary data are to be kept
    <wait_time> - periodicity (in seconds) to check expired data
    <db_clean_time> - periodicity (in seconds) to cleat the database of temporary data

    <answers_comments> - additional comments provided to the responses according to certainty of their relevance. There are the six levels: <sure_answer>, <broad_question>, <unsure>, <probably>, <related_info>, and <additional_info>

    <greeting_phrases> - standard phrases to greet the user or supplement the response
    <standard_answers>, <explanations>      - explanations for failures
    <dialog_answers> - responses for typical standard situations not related to the subject area of the system. They are provided according to the related <markers> in the user’s message.
    <goodbye_phrases> - phrases for verbose closing of a dialogue with the system

### sparql_converter

The entry point of this application is text_to_sparql.py 
	
The scripts corresponds to the business logic of the service are gathered in the *converter* directory.

The main settings are given in the agent_config.xml file. It has the following staitments:

    <name> - the name of the service
    <queue_timout> - max time (in seconds) to keep a task in queue
    <ttl> - time to keep in the queue completed tasks
    <result_ttl> - time to store the results in queue
    <failure_ttl> - time to store the failure messages in queue
    <check_ids_interval> - periodicity to check the expired ID’s
    <limitation> - max time to store the results in the data base
    <garbage_deleting> - time (in seconds) how long the temporary data are to be kept
    <host> - the host the service works on
    <port> - the port the service works on
    <responding_url> - URL to send the obtained results
    <ansver_attempts> - number of the attempts to obtain the response

File ontologies_list.xml contains the list of the ontologies names used in the system

File tree.xml is an XML representation of the decision tree used for the appropriate SPARQL query template selection basing on the words from the input user’s phrase.

















