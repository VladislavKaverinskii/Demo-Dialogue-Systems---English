# -*- coding: utf8 -*-

import rdflib
import asyncio
import motor.motor_asyncio
import json
import xml.etree.ElementTree as Et
from argparse import ArgumentParser
import requests
import random
import time
import traceback


class Ontologies:
    __instance = None
    def __init__(self):
        if not Ontologies.__instance:
            self.ontologies_names = []
            self.ontology_objects = {}
            self.default_ontology = ""
            self.mongo_data_base = None
        else:
            print("Instance already created:", self.getInstance())

    @classmethod
    def get_instance(cls, config_file="ontologies_list.xml", mongo_data_base=None):
        if not cls.__instance and mongo_data_base is not None:
            cls.__instance = Ontologies()
            cls.__instance.mongo_data_base = mongo_data_base
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for j in root:
                if j.tag == "ontologies":
                    for onto_name in j:
                        cls.__instance.ontologies_names.append(onto_name.text.strip())
                        loop = asyncio.get_event_loop()
                        print(onto_name.text.strip())
                        data = loop.run_until_complete(get_data_from_db(dict_item={"name": onto_name.text.strip()},
                                                                        mongo_data_base=mongo_data_base))

                        g = rdflib.Graph()
                        print(mongo_data_base)
                        g.parse(data=data.get("ontology"), format='xml')
                        nif = rdflib.Namespace('')
                        g.bind('ontology', nif)
                        print("graph has %s statements." % len(g))
                        cls.__instance.ontology_objects[onto_name.text.strip()] = g
                elif j.tag == "default_ontology":
                    cls.__instance.default_ontology = j.text.strip()
        return cls.__instance


async def get_data_from_db(dict_item=None, mongo_data_base=None):
    if dict_item is not None:
        if mongo_data_base is not None:
            print("dict_item", dict_item)
            document = await mongo_data_base.find_one(dict_item, projection={'_id': False})
            return document
    return {}


class DBConstantsOntology:
    __instance = None
    def __init__(self):
        if not DBConstantsOntology.__instance:
            self.admin = ""
            self.password = ""
            self.db_url = ""
            self.db_name = ""
            self.collection_name = ""
            self.collection_name_letters = ""
            self.url_base = ""
        else:
            print("Instance already created:", self.getInstance())

    @classmethod
    def get_instance(cls, config_file="mongo_client_config_ontology.xml"):
        if not cls.__instance:
            cls.__instance = DBConstantsOntology()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for t in root:
                if t.tag == "admin":
                    cls.__instance.admin = t.text.strip()
                if t.tag == "password":
                    cls.__instance.password = t.text.strip()
                if t.tag == "db_url":
                    cls.__instance.db_url = t.text.strip()
                if t.tag == "db_name":
                    cls.__instance.db_name = t.text.strip()
                if t.tag == "collection_name":
                    cls.__instance.collection_name = t.text.strip()
                if t.tag == "collection_name_letters":
                    cls.__instance.collection_name_letters = t.text.strip()
                if t.tag == "base":
                    cls.__instance.url_base = t.text.strip()
        return cls.__instance


def execute_sparql_query(query="", graph=None):
    if graph is not None and query is not None and "select" in query.lower():
        return graph.query(query)
    else:
        return None


def get_ontilogy_answers_from_qurey_set(query_set=None, ontologies_config=None, ontology_config_file="ontologies_list.xml",
                                        ontologies_data_base=None):
    s_time = time.time()
    random.seed()
    if query_set is not None:
        if ontologies_config is None:
            ontologies_config = Ontologies().get_instance(config_file=ontology_config_file, mongo_data_base=ontologies_data_base)
        else:
            ontologies_config = ontologies_config.get_instance(config_file=ontology_config_file, mongo_data_base=ontologies_data_base)
        results = []
        found_answers = []
        if isinstance(query_set, str):
            try:
                query_set = json.loads(query_set)
            except:
                return []
        print("query_set", query_set)
        total_keys_n = 0
        for counter, query_list in enumerate(query_set):
            results_level = []
            last_ontology = ""
            for j, query_point in enumerate(query_list):
                graph = ontologies_config.ontology_objects.get(query_point["ontology"])
                query = query_point.get("query")
                last_ontology = query_point["ontology"]
                semantic_type = query_point["query_type"]
                entities_for_query = query_point["entities_for_query"]
                if query is not None and query != "":
                    current_answer = execute_sparql_query(query=query, graph=graph)
                    print("current_answer", current_answer)
                    if current_answer is not None:
                        answer_keys = []
                        k = 0
                        # current_answer_list = current_answer.serialize(format='csv').decode('utf-8').split('\n')
                        # result = current_answer.serialize(format='csv').decode('utf-8')

                        try:
                            result = json.loads(current_answer.serialize(format='json').decode('utf-8'))
                        except Exception as e:
                            print(e)
                            print(traceback.format_exc())
                            print("current_answer 2", current_answer)
                            # Костыль на тот случай, если результат не парсится как json (есть недозволенные символы)
                            result = {
                                "head": {'vars': ['title', 'result']},
                                "results": {'bindings':[]}}
                            for row in current_answer:
                                try:
                                    result_item = '%s ||| %s' % row
                                    current_title, current_result = result_item.split('|||')
                                    print("||||", current_title, current_result)
                                    current_res_dict = {
                                        'result': {
                                            'type': 'literal',
                                            'value': current_result,
                                            'datatype': 'string'
                                            },
                                        'title':
                                            {'type': 'literal',
                                             'value': current_title,
                                             'xml:lang': 'en'
                                             }
                                    }
                                    result["results"]['bindings'].append(current_res_dict)
                                except:
                                    print(e)
                                    print(traceback.format_exc())
                                    continue


                        print("result", result)

                        current_answer_list = list()

                        if 'head' in result and 'results' in result:
                            if 'vars' in result['head']:
                                if len(result['head']['vars']) > 1:
                                    for res in result['results']:
                                        for res_2 in result['results'][res]:
                                            if 'title' in res_2 and 'result' in res_2:
                                                if 'value' in res_2['title'] and 'value' in res_2['result']:
                                                    if '#' in res_2['title']['value']:
                                                        res_2['title']['value'] = res_2['title']['value'].split('#')[1]
                                                    elif "http://www.semanticweb.org/" in res_2['title']['value']:
                                                        res_2['title']['value'] = res_2['title']['value'].strip("http://www.semanticweb.org/")
                                                    if '#' in res_2['result']['value']:
                                                        res_2['result']['value'] = res_2['result']['value'].split('#')[1]
                                                    elif "http://www.semanticweb.org/" in res_2['result']['value']:
                                                        res_2['result']['value'] = res_2['result']['value'].strip(
                                                            "http://www.semanticweb.org/")
                                                    current_answer_list.append([res_2['title']['value'], res_2['result']['value']])
                                elif (len(result['head']['vars']) == 1 and 'result' in result['head']['vars']
                                      or 'title' in result['head']['vars']):
                                    for res in result['results']:
                                        for res_2 in result['results'][res]:
                                            if 'title' in res_2 and 'value' in res_2['title']:
                                                if '#' in res_2['title']['value']:
                                                    res_2['title']['value'] = res_2['title']['value'].split('#')[1]
                                                elif "http://www.semanticweb.org/" in res_2['title']['value']:
                                                    res_2['title']['value'] = res_2['title']['value'].strip(
                                                        "http://www.semanticweb.org/")
                                                current_answer_list.append([res_2['title']['value']])
                                            elif 'result' in res_2 and 'value' in res_2['result']:
                                                if '#' in res_2['result']['value']:
                                                    res_2['result']['value'] = res_2['result']['value'].split('#')[1]
                                                elif "http://www.semanticweb.org/" in res_2['result']['value']:
                                                    res_2['result']['value'] = res_2['result']['value'].strip(
                                                        "http://www.semanticweb.org/")
                                                current_answer_list.append([res_2['result']['value']])

                        print(query)
                        print(current_answer_list)

                        for answer in current_answer_list:
                            if k <= 10:
                                print("answer", answer)
                                if answer not in found_answers:
                                    # print(e)
                                    # print(traceback.format_exc())
                                    if len(answer) > 1:
                                        answer_keys.append({"name": answer[0], "key": answer[1], "type": "letters",
                                                            "is_link": False, "semantic_type": semantic_type,
                                                            "entities_for_query": entities_for_query})
                                    else:
                                        answer_keys.append({"name": "", "key": answer[0], "type": "letters",
                                                            "is_link": False, "semantic_type": semantic_type,
                                                            "entities_for_query": entities_for_query})
                                    found_answers.append(answer)
                                    total_keys_n += 1


                        #print("answer_keys", answer_keys)
                        result_tmp = dict()

                        for ky in answer_keys:
                            if ky.get('key') in result_tmp:
                                ky["additional"] = result_tmp[ky.get('key')]
                            else:
                                ky["additional"] = dict()
                        results_level.append(answer_keys)
                        #print("answer_keys ", answer_keys)

            # print(results_level)

            results.append(results_level)
            if last_ontology != "letters":
                if total_keys_n >= 10:
                    print("query execution", (time.time()) - s_time)
                    return results
                if len(results_level) > 0 and counter > 0 and min(len(k_list) for k_list in results_level) >= 20:
                    break
                elif len(results_level) > 0 and counter == 0 and min(len(k_list) for k_list in results_level) >= 20:
                    break
        print("query execution", (time.time()) - s_time)
        print()
        for r in results:
            print(r)
        return results
    return []



if __name__ == "__main__":
    db_config_ontologies = DBConstantsOntology().get_instance(config_file="mongo_client_config_ontology.xml")
    db_url_ontologies = db_config_ontologies.url_base + '://' + db_config_ontologies.admin + ':' + db_config_ontologies.password + '@' + db_config_ontologies.db_url
    print(db_url_ontologies)
    client_ontologies = motor.motor_asyncio.AsyncIOMotorClient(db_url_ontologies)
    print(client_ontologies)
    db_ontologies = eval('client_ontologies.' + db_config_ontologies.db_name)
    collection_ontologies = eval('db_ontologies.' + db_config_ontologies.collection_name)


    ontologies = Ontologies()

    ontology_config = ontologies.get_instance(config_file="ontologies_list.xml", mongo_data_base=collection_ontologies)

    #test_query_set = [[{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Nordnet. ?intersectionElementID rdf:rest*/rdf:first :Vps. ?intersectionElementID rdf:rest*/rdf:first :Hvor. ?intersectionElementID rdf:rest*/rdf:first :Finne. ?intersectionElementID rdf:rest*/rdf:first :Nummer. ?intersectionElementID rdf:rest*/rdf:first :Konto.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Vps. ?intersectionElementID rdf:rest*/rdf:first :Konto. ?intersectionElementID rdf:rest*/rdf:first :Finne. ?intersectionElementID rdf:rest*/rdf:first :Nordnet. ?intersectionElementID rdf:rest*/rdf:first :Hvor.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Nummer. ?intersectionElementID rdf:rest*/rdf:first :Konto. ?intersectionElementID rdf:rest*/rdf:first :Nordnet. ?intersectionElementID rdf:rest*/rdf:first :Finne.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Hvor. ?intersectionElementID rdf:rest*/rdf:first :Konto. ?intersectionElementID rdf:rest*/rdf:first :Finne.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Nummer. ?intersectionElementID rdf:rest*/rdf:first :Finne.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Konto.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}]]

    #test_query_set_2 = [[{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Investeringskontoe. ?intersectionElementID rdf:rest*/rdf:first :Hva. ?intersectionElementID rdf:rest*/rdf:first :Når. ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :tyyr. ?intersectionElementID rdf:rest*/rdf:first :ghj. ?intersectionElementID rdf:rest*/rdf:first :ssss. ?intersectionElementID rdf:rest*/rdf:first :gfdd.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Investeringskontoe. ?intersectionElementID rdf:rest*/rdf:first :Hva. ?intersectionElementID rdf:rest*/rdf:first :Når. ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :tyyr. ?intersectionElementID rdf:rest*/rdf:first :ghj. ?intersectionElementID rdf:rest*/rdf:first :ssss. ?intersectionElementID rdf:rest*/rdf:first :gfdd.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Når. ?intersectionElementID rdf:rest*/rdf:first :Investeringskontoe. ?intersectionElementID rdf:rest*/rdf:first :Hva.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :ssss. ?intersectionElementID rdf:rest*/rdf:first :tyyr. ?intersectionElementID rdf:rest*/rdf:first :ghj.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Når. ?intersectionElementID rdf:rest*/rdf:first :Investeringskontoe. ?intersectionElementID rdf:rest*/rdf:first :Hva.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :ssss. ?intersectionElementID rdf:rest*/rdf:first :tyyr. ?intersectionElementID rdf:rest*/rdf:first :ghj.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Hva. ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :gfdd. ?intersectionElementID rdf:rest*/rdf:first :ssss.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Hva. ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :gfdd. ?intersectionElementID rdf:rest*/rdf:first :ssss.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :gfdd.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}], [{'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :Flytte.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}, {'ontology': 'nordent_answers', 'query': 'SELECT DISTINCT ?result WHERE { ?intersectionElementID rdf:rest*/rdf:first :gfdd.  ?intersectionName owl:intersectionOf ?intersectionElementID.  ?propName rdfs:domain ?intersectionName.  ?propName rdfs:range ?result.  ?result rdfs:subClassOf :ReadyAnswerLink. }'}]]

    test_query_set = [[{'ontology': 'ontology', 'query': 'SELECT DISTINCT ?title ?result WHERE { :Процеси_навчання_у_фізичній_та_реабілітаційній_медицині ?title ?result.  filter (?title != rdfs:label).  filter (?title != rdfs:shape).  filter (?title != rdfs:guid).  filter (?title != rdfs:color).  filter (?title != rdfs:xPos).  filter (?title != rdfs:yPos).  filter (?title != rdf:type).  filter (?title != rdfs:coment).  filter (?title != owl:equivalentClass).  filter (?title != rdfs:subClassOf). }'}]]

    sparql_query_results = get_ontilogy_answers_from_qurey_set(query_set=test_query_set, ontologies_config=ontologies,
                                                               ontology_config_file="ontologies_list.xml",
                                                               ontologies_data_base=collection_ontologies)


    for i in sparql_query_results:
        print(i)


