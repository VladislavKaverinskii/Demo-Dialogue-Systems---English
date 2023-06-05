# Demo-Dialogue-Systems---English
This is a demo example of an ontology driven dialogues system, which uses set of ontologies in diggerent subject areas as a main knowlege store.

The system has three main components: 

    client_service includes Django application for the user web interface representation
    
    ontology_service is a Flask application which operates as a micro-service and dealing with ontologies
    
    sparql_converter is a Flask application also a micro-service responsible for formation of SPARQL queries according to the input users' phrases
    
