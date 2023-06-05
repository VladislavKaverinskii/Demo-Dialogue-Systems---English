# Demo-Dialogue-Systems---English
This is a demo example of an ontology driven dialogues system, which uses set of ontologies in diggerent subject areas as a main knowlege store.

The system has three main components: 

    client_service includes Django applications for the user web interface representation. It provides display and operation of the user interface, pre-processing of incoming texts, preparation for display of received responses. Also, this service performs the functions of logging the history of dialogues. In addition, certain modules of this application perform the functions of an intermediate point of transmission of messages between other services of the system.
    
    ontology_service is a Flask application which operates as a micro-service and dealing with ontologies. Warning: queries are executed directly by this module using the RDFlib Python package, which performs extermely slow. For production change in to the endpoint of a reliable and fasr RDF tripples store like Jena Fuseki.
    
    sparql_converter is a Flask application also a micro-service responsible for formation of SPARQL queries according to the input users' phrases. 
    



