# -*- coding: utf-8 -*-

import argparse
import os
import json
import time
import threading
import hashlib
import random
import string
import traceback
import requests
import signal
import asyncio

from flask import Flask
from flask import request
app = Flask(__name__)
import xml.etree.ElementTree as Et
import motor.motor_asyncio

import converter.sparql_converter


is_running = True
global_threads = []
threading.stack_size(512*1024)


keywords = dict()
keywords_ep = dict()
with open('keywords.json', 'r', encoding='utf-8') as keywords_file:
    keywords = json.loads(keywords_file.read())
    print(keywords)


with open('keywords_ep.json', 'r', encoding='utf-8') as keywords_file:
    keywords_ep = json.loads(keywords_file.read())
    print(keywords_ep)

with open('keywords_aliyev.json', 'r', encoding='utf-8') as keywords_file:
    keywords_aliyev = json.loads(keywords_file.read())
    print(keywords_aliyev)


class AgentConstants:
    __instance = None
    def __init__(self):
        if not AgentConstants.__instance:
            self.name = ""
            self.queue_timout = 100
            self.ttl = 10
            self.result_ttl = 20
            self.failure_ttl = 10
            self.check_ids_interval = 1000
            self.limitation = 10000
            self.garbage_deleting = 10000
            self.host = '0.0.0.0'
            self.port = 80
            self.responding_url = ""
            self.ansver_attempts = 10
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="agent_config.xml"):
        if not cls.__instance:
            cls.__instance = AgentConstants()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for i in root:
                if i.tag == "name":
                    cls.__instance.name = i.text.strip()
                elif i.tag == "queue_timout":
                    cls.__instance.queue_timout = int(i.text.strip())
                elif i.tag == "ttl":
                    cls.__instance.ttl = int(i.text.strip())
                elif i.tag == "result_ttl":
                    cls.__instance.result_ttl = int(i.text.strip())
                elif i.tag == "failure_ttl":
                    cls.__instance.failure_ttl = int(i.text.strip())
                elif i.tag == "check_ids_interval":
                    cls.__instance.check_ids_interval = int(i.text.strip())
                elif i.tag == "limitation":
                    cls.__instance.limitation = int(i.text.strip())
                elif i.tag == "host":
                    cls.__instance.host = i.text.strip()
                elif i.tag == "port":
                    cls.__instance.port = int(i.text.strip())
                elif i.tag == "garbage_deleting":
                    cls.__instance.garbage_deleting = int(i.text.strip())
                elif i.tag == "responding_url":
                    cls.__instance.responding_url = i.text.strip()
                elif i.tag == "ansver_attempts":
                    cls.__instance.ansver_attempts = int(i.text.strip())
        return cls.__instance


class IDStoreConfig:
    __instance = None
    def __init__(self):
        if not IDStoreConfig.__instance:
            self.admin = ""
            self.password = ""
            self.db_url = ""
            self.db_name = ""
            self.collection_name = ""
            self.url_base = ""
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="mongo_id_store_config.xml"):
        if not cls.__instance:
            cls.__instance = IDStoreConfig()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for i in root:
                if i.tag == "admin":
                    cls.__instance.admin = i.text.strip()
                if i.tag == "password":
                    cls.__instance.password = i.text.strip()
                if i.tag == "db_url":
                    cls.__instance.db_url = i.text.strip()
                if i.tag == "db_name":
                    cls.__instance.db_name = i.text.strip()
                if i.tag == "collection_name":
                    cls.__instance.collection_name = i.text.strip()
                if i.tag == "base":
                    cls.__instance.url_base = i.text.strip()
        return cls.__instance


class ResultsStoreConfig:
    __instance = None
    def __init__(self):
        if not ResultsStoreConfig.__instance:
            self.admin = ""
            self.password = ""
            self.db_url = ""
            self.db_name = ""
            self.collection_name = ""
            self.url_base = ""
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="mongo_results_config.xml"):
        if not cls.__instance:
            cls.__instance = ResultsStoreConfig()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for i in root:
                if i.tag == "admin":
                    cls.__instance.admin = i.text.strip()
                if i.tag == "password":
                    cls.__instance.password = i.text.strip()
                if i.tag == "db_url":
                    cls.__instance.db_url = i.text.strip()
                if i.tag == "db_name":
                    cls.__instance.db_name = i.text.strip()
                if i.tag == "collection_name":
                    cls.__instance.collection_name = i.text.strip()
                if i.tag == "base":
                    cls.__instance.url_base = i.text.strip()
        return cls.__instance


agent_constants = AgentConstants().get_instance(config_file="agent_config.xml")
entities_names_description = converter.sparql_converter.InputVarsNames()
analyzer = converter.sparql_converter.AnalyzerAPIWrapper()
marker_words = converter.sparql_converter.MarkerWords()

db_config = converter.sparql_converter.DBConstants().get_instance(config_file="converter/mongo_client_config_ontology.xml")
db_url = db_config.url_base + '://' + db_config.admin + ':' + db_config.password + '@' + db_config.db_url
print(db_config.db_url)
client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
db = eval('client.' + db_config.db_name)
collection = eval('db.' + db_config.collection_name)


# print(collection)


query_templates = converter.sparql_converter.QueryTemplates()
ontologies = converter.sparql_converter.Ontologies()
ontology_config_global = converter.sparql_converter.Ontologies().get_instance(config_file="converter/ontologies_list.xml",
                                                                              mongo_data_base=collection)


id_db_config = IDStoreConfig().get_instance(config_file="mongo_id_store_config.xml")
id_db_url = id_db_config.url_base + '://' + id_db_config.admin + ':' + id_db_config.password + '@' + id_db_config.db_url
id_client = motor.motor_asyncio.AsyncIOMotorClient(id_db_url)
id_db = eval('id_client.' + id_db_config.db_name)
id_collection = eval('id_db.' + id_db_config.collection_name)

results_db_config = ResultsStoreConfig().get_instance(config_file="mongo_results_config.xml")
results_db_url = results_db_config.url_base + '://' + results_db_config.admin + ':' + results_db_config.password + '@' + results_db_config.db_url
# print(results_db_url)
results_client = motor.motor_asyncio.AsyncIOMotorClient(results_db_config.db_url)
results_db = eval('results_client.' + results_db_config.db_name)
results_collection = eval('results_db.' + results_db_config.collection_name)


async def get_data_from_db(dict_item=None, mongo_data_base=None):
    if dict_item is not None:
        if mongo_data_base is not None:
            document = await mongo_data_base.find_one(dict_item, projection={'_id': False})
            return document
    return None


async def put_data_to_db(dict_item=None, mongo_data_base=None):
    if dict_item is not None:
        document = await mongo_data_base.find_one(dict_item)
        if document is None:
            result = await mongo_data_base.insert_one(dict_item)
            return result
    return None


async def replace_data_in_db(dict_item=None, key="", mongo_data_base=None):
    if dict_item is not None:
        document = await mongo_data_base.find_one({key: dict_item[key]})
        # print("document", document)
        if document is not None:
            _id = document['_id']
            result = await mongo_data_base.replace_one({'_id': _id}, dict_item)
            return result
        else:
            result = await mongo_data_base.insert_one(dict_item)
            return result
    return None


async def delete_data_from_db(dict_item=None, mongo_data_base=None):
    if dict_item is not None:
        document = await mongo_data_base.find_one(dict_item)
        # print(document)
        if document is not None:
            _id = document['_id']
            # print(_id)
            result = await mongo_data_base.delete_one(dict_item)
            return result
    return None


async def get_all_data_from_db(mongo_data_base=None):
    docs = []
    async for doc in mongo_data_base.find():
        docs.append(doc)
    return docs


conversation_ids = {}

salt = b'^\x17\x9d\xe6\xb0?\xe9\xad\xe4\x04\xe4\x010p\xa4\xcd\xe6`(\x8e\\g\xa7\x19\xd9~\xe8;\xddu\x12\xa0'
key = b'\x02\x8a\xeb\x96\xfe$r\xdaG\xc9Q\x1e(+\x8e\x0e\x8a\xcfr\xe1\xb5G\x8d\x12\xc0\xa6Qe\x90\xcc\xf5\xdb'


class ConversionQueue:
    def __init__(self, name="job_queue", update=10000):
        self.name=name
        self.update = update
        self.results = {}
        self.threads = {}
        self.garbage_deleting = False
        self.threads_to_del = []
        self.last_update = time.time()
        self.first_run = True
        self.main_t = threading.Thread(target=self.running, daemon=True)
        self.main_t.start()


    def enqueue(self, input_text="", entities_names=None, entities_names_file="converter/converter_config.xml",
                analyzer=None, marker_words=None, marker_words_file="converter/marker_words.xml", templates=None,
                query_templates_file="converter/query_template.xml", ontology_config=None,
                ontology_config_file="converter/ontologies_list.xml",  mongo_data_base=None,
                ttl=1000, result_ttl=10000, failure_ttl=1000, method_of_conversion="convert_common"):

        job_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
        start_time = time.time()
        kwargs = {
            "input_text": input_text,
            "entities_names": entities_names_description,
            "entities_names_file": entities_names_file,
            "analyzer": analyzer,
            "marker_words": marker_words,
            "marker_words_file": marker_words_file,
            "templates": query_templates,
            "query_templates_file": query_templates_file,
            "ontology_config": ontologies,
            "ontology_config_file": ontology_config_file,
            "mongo_data_base": collection,
            "job_id": job_id,
            "ttl": ttl,
            "result_ttl": result_ttl,
            "failure_ttl": failure_ttl,
            "start_time": start_time,
            "method_of_conversion": method_of_conversion
        }

        t = threading.Thread(target=self.execute, kwargs=kwargs, daemon=True)
        self.threads[job_id] = {
            "job": t,
            "start_time": start_time,
            "ttl": ttl,
            "result_ttl": result_ttl,
            "failure_ttl": failure_ttl
        }

        return job_id

    def execute(self, input_text="", entities_names=None, entities_names_file="converter/converter_config.xml",
                analyzer=None, marker_words=None, marker_words_file="converter/marker_words.xml", templates=None,
                query_templates_file="converter/query_template.xml", ontology_config=None,
                ontology_config_file="converter/ontologies_list.xml",  mongo_data_base=None,
                ttl=1000, result_ttl=10000, failure_ttl=1000, start_time=0, job_id="",
                method_of_conversion="convert_common"):
        lock = threading.Lock()
        lock.acquire()
        try:
            print(input_text)
            current_result = make_conversion(input_text=input_text, entities_names=entities_names,
                                                       entities_names_file=entities_names_file,
                                                       analyzer=analyzer, marker_words=marker_words,
                                                       marker_words_file=marker_words_file, templates=templates,
                                                       query_templates_file=query_templates_file,
                                                       ontology_config=ontology_config,
                                                       ontology_config_file=ontology_config_file,
                                                       mongo_data_base=mongo_data_base,
                                                       method_of_conversion=method_of_conversion)
            print("current_result", current_result)

            failure = False
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            current_result = []
            failure = True
        finally:
            lock.release()

        lock.acquire()
        try:
            self.results[job_id] = {"result": current_result,
                                "start_time": start_time,
                                "ttl": ttl,
                                "result_ttl": result_ttl,
                                "failure_ttl": failure_ttl,
                                 "failure": failure
                                 }

            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url, io_loop=new_loop)
            new_db_results = eval('new_client_results.' + results_db_config.db_name)
            new_collection_results = eval('new_db_results.' + results_db_config.collection_name)
            dict_item = {
                "result": current_result,
                "start_time": start_time,
                "ttl": ttl,
                "result_ttl": result_ttl,
                "failure_ttl": failure_ttl,
                "failure": failure,
                "job_id": job_id
            }
            print(new_collection_results)

            print(current_result)

            results_obj_id = new_loop.run_until_complete(put_data_to_db(
                dict_item=dict_item,
                mongo_data_base=new_collection_results))
            new_loop.close()


            is_successful = send_response_on_finishing(question_id=job_id)
            counter = 0
            while not is_successful and counter < agent_constants.ansver_attempts:
                is_successful = send_response_on_finishing(question_id=job_id)
                counter += 1
                time.sleep(0.1)

        except:
            self.results[job_id] = {"result": [],
                                    "start_time": start_time,
                                    "ttl": ttl,
                                    "result_ttl": result_ttl,
                                    "failure_ttl": failure_ttl,
                                    "failure": True
                                    }
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url, io_loop=new_loop)
            new_db_results = eval('new_client_results.' + results_db_config.db_name)
            new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

            dict_item = {
                "result": [],
                "start_time": start_time,
                "ttl": ttl,
                "result_ttl": result_ttl,
                "failure_ttl": failure_ttl,
                "failure": True,
                "job_id": job_id
            }

            results_obj_id = new_loop.run_until_complete(put_data_to_db(dict_item=dict_item,
                                                                        mongo_data_base=new_collection_results))
            new_loop.close()

        finally:
            lock.release()

    def running(self):
        lock = threading.Lock()
        while True:
            lock.acquire()
            try:
                for job_id in self.threads:

                    if not self.threads[job_id]["job"].isAlive() and job_id not in self.results:
                        try:
                            print("hyyjjhgjhgjkhkhjkhkhg")
                            self.threads[job_id]["job"].start()
                            print("ffddfgdfgfghgfghjghjg")
                        except:
                            pass
                    if not self.threads[job_id]["job"].isAlive() and (time.time() - self.threads[job_id]["start_time"]) > self.threads[job_id]["result_ttl"]:
                        if job_id not in self.threads_to_del:
                            try:
                                self.threads_to_del.append(job_id)
                            except:
                                pass
                    if self.threads[job_id]["job"].isAlive() and (time.time() - self.threads[job_id]["start_time"]) > self.threads[job_id]["ttl"]:
                        if job_id not in self.threads_to_del:
                            try:
                                self.threads_to_del.append(job_id)
                            except:
                                pass
                    if job_id in self.results:
                        if self.results[job_id]["failure"] and (time.time() - self.threads[job_id]["start_time"]) > self.threads[job_id]["failure_ttl"]:
                            if job_id not in self.threads_to_del:
                                try:
                                    self.threads_to_del.append(job_id)
                                except:
                                    pass
            except Exception as e:
                print(e)
                print(traceback.format_exc())
            finally:
                lock.release()

            lock.acquire()
            try:
                #print((time.time() - self.last_update), self.update)
                if ((time.time() - self.last_update) >= self.update) or self.first_run:
                    self.first_run = False
                    self.garbage_deleting = True
                    # print("self.threads_to_del", self.threads_to_del)
                    for job_id in self.threads_to_del:
                        try:
                            if job_id in self.threads:
                                del self.threads[job_id]
                                print("old task with id ", job_id, " was deleted")
                        except:
                            print("cant delete ", job_id, " threads")
                        if job_id in self.results:
                            try:
                                del self.results[job_id]

                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url,
                                                                                            io_loop=new_loop)
                                new_db_results = eval('new_client_results.' + results_db_config.db_name)
                                new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

                                dict_item = {
                                    "job_id": job_id
                                }

                                results_obj_id = new_loop.run_until_complete(delete_data_from_db(dict_item=dict_item,
                                                                                                 mongo_data_base=new_collection_results))
                                new_loop.close()

                                print("old result with id ", job_id, " was deleted")
                            except:
                                print("cant delete ", job_id, " from results")
                        try:
                            del_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(del_loop)
                            new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url,
                                                                                        io_loop=del_loop)
                            new_db_results = eval('new_client_results.' + results_db_config.db_name)
                            new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

                            dict_item = {
                                "job_id": job_id
                            }

                            curr_results_obj = del_loop.run_until_complete(get_data_from_db(dict_item=dict_item,
                                                                                             mongo_data_base=new_collection_results))

                            if curr_results_obj is not None:
                                results_obj_id = del_loop.run_until_complete(delete_data_from_db(dict_item=dict_item,
                                                                                                 mongo_data_base=new_collection_results))
                            del_loop.close()
                            print("old result with id ", job_id, " was deleted from db")
                        except:
                            print("cant delete result with id ", job_id, " from db")
                    try:
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url, io_loop=new_loop)
                        new_db_results = eval('new_client_results.' + results_db_config.db_name)
                        new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

                        results_docs = new_loop.run_until_complete(get_all_data_from_db(
                            mongo_data_base=new_collection_results))
                        new_loop.close()

                        for doc in results_docs:
                            # for conversation_id in conversation_ids:
                            if (time.time() - doc.get("start_time")) > doc.get("result_ttl"):
                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url,
                                                                                            io_loop=new_loop)
                                new_db_results = eval('new_client_results.' + results_db_config.db_name)
                                new_collection_results = eval('new_db_results.' + results_db_config.collection_name)
                                # print(doc)
                                res = new_loop.run_until_complete(delete_data_from_db(
                                    dict_item={'job_id': doc.get('job_id')},
                                    mongo_data_base=new_collection_results))
                                new_loop.close()
                                print("old result ", doc.get('job_id'), " was deleted")
                    except:
                        print("cant delete old result from db")

                    self.threads_to_del = []
                    self.garbage_deleting = False
                    self.last_update = time.time()
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                self.threads_to_del = []
                self.garbage_deleting = False
                self.last_update = time.time()
                lock.release()
            finally:
                self.threads_to_del = []
                self.garbage_deleting = False
                lock.release()
            time.sleep(0.001)

    def fetch_job(self, job_id):
        result_obj = None
        try:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url, io_loop=new_loop)
            new_db_results = eval('new_client_results.' + results_db_config.db_name)
            new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

            dict_item = {
                "job_id": job_id
            }

            result_obj = new_loop.run_until_complete(get_data_from_db(dict_item=dict_item,
                                                                      mongo_data_base=new_collection_results))
            new_loop.close()
        except:
            return {"status": "error",
                    "result": []
                    }

        if result_obj:
            output = {"status": "finished",
                      "result": result_obj.get("result")}
            try:
                while self.garbage_deleting:
                    time.sleep(0.001)
                if not self.garbage_deleting:
                    try:
                        del self.results[job_id]
                        del self.threads[job_id]
                    except:
                        pass

                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_client_results = motor.motor_asyncio.AsyncIOMotorClient(results_db_url, io_loop=new_loop)
                    new_db_results = eval('new_client_results.' + results_db_config.db_name)
                    new_collection_results = eval('new_db_results.' + results_db_config.collection_name)

                    dict_item = {
                        "job_id": job_id
                    }

                    result_obj = new_loop.run_until_complete(delete_data_from_db(dict_item=dict_item,
                                                                                 mongo_data_base=new_collection_results))
                    new_loop.close()

            except Exception as e:
                print("cant delete ", job_id, " from results or/and threads")
                print(e)
                print(traceback.format_exc())
            return output
        elif job_id in self.threads:
            return {"status": "executing",
                    "result": []
                    }
        else:
            return {"status": "absent",
                    "result": []
                    }

q = ConversionQueue(update=agent_constants.garbage_deleting)


@app.route("/")
def ping_test():
    return "Ukrainian text to SPARQL conversion service is working"

@app.route('/<method_of_conversion>/', methods=['GET', 'POST'])
def process(method_of_conversion="convert_common"):
    if request.method == 'POST':
        input_data = request.json
        if ("receivers" in input_data and "performative" in input_data and "content" in input_data
            and "sender" in input_data and "language" in input_data and "protocol" in input_data
            and "conversationID" in input_data):
            if "password" in input_data:
                new_key = hashlib.pbkdf2_hmac('sha256', input_data.get("password").encode('utf-8'), salt, 100000)
                if new_key != key:
                    message = {
                        "performative": "refuse",
                        "sender": agent_constants.name,
                        "receivers": [input_data.get("sender")],
                        "reply-to": input_data.get("content"),
                        "content": "Wrong password",
                        "language": "text",
                        "protocol": "fipa-request protocol",
                        "reply-with": "Wrong password",
                        "conversationID": input_data.get('conversationID'),
                        "enconding": "utf-8",
                        "ontology": "",
                        "in-reply-to": "",
                        "reply-by": ""
                    }
                    return json.dumps(message, ensure_ascii=False)
                # print("input_data", input_data)
                # print("conversationID", input_data.get("conversationID"))

                new_loop = asyncio.new_event_loop()
                asyncio.set_event_loop(new_loop)
                new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                        io_loop=new_loop)
                new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                conversationID_obj = new_loop.run_until_complete(get_data_from_db(
                    dict_item={"conversationID": input_data.get("conversationID").strip()},
                    mongo_data_base=new_collection_ids))
                new_loop.close()

                if conversationID_obj is not None:
                    if agent_constants.name in input_data.get("receivers"):
                        if input_data.get("protocol") == "fipa-request protocol":
                            if (input_data.get("language").lower() == "no"
                                or input_data.get("language").lower() == "norw"
                                    or input_data.get("language").lower() == "en"
                                or input_data.get("language").lower() == "norwegian"
                                or input_data.get("language").lower() == "text"
                                or input_data.get("language").lower() == "norsk"):
                                    if input_data.get("performative") == "inform":
                                        input_text = input_data.get("content")

                                        job_id = q.enqueue(input_text=input_text, entities_names=entities_names_description,
                                                           entities_names_file="converter/converter_config.xml",
                                                           analyzer=analyzer, marker_words=marker_words,
                                                           marker_words_file="converter/marker_words.xml",
                                                           templates=query_templates,
                                                           query_templates_file="converter/query_template.xml",
                                                           ontology_config=ontologies,
                                                           ontology_config_file="converter/ontologies_list.xml",
                                                           mongo_data_base=collection,
                                                           ttl=agent_constants.ttl, result_ttl=agent_constants.result_ttl,
                                                           failure_ttl=agent_constants.failure_ttl,
                                                           method_of_conversion=method_of_conversion)
                                        print(job_id)

                                        message = {
                                            "performative": "confirm",
                                            "sender": agent_constants.name,
                                            "receivers": [input_data.get("sender")],
                                            "reply-to": input_data.get("content"),
                                            "content": str(job_id),
                                            "language": "text",
                                            "protocol": "fipa-request protocol",
                                            "reply-with": str(job_id),
                                            "conversationID": input_data.get('conversationID'),
                                            "enconding": "utf-8",
                                            "ontology": "",
                                            "in-reply-to": "",
                                            "reply-by": ""
                                        }

                                        new_loop = asyncio.new_event_loop()
                                        asyncio.set_event_loop(new_loop)
                                        new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                                                io_loop=new_loop)
                                        new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                        new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                        db_id = new_loop.run_until_complete(replace_data_in_db(
                                            dict_item={"conversationID": input_data.get("conversationID").strip(),
                                                       "start_time": time.time()}, key="conversationID",
                                            mongo_data_base=new_collection_ids))
                                        new_loop.close()

                                        # conversation_ids[input_data.get("conversationID")] = time.time()
                                        return json.dumps(message, ensure_ascii=False)

                                    elif input_data.get("performative") == "request":
                                        try:
                                            question_id = input_data.get("content")
                                            job = q.fetch_job(question_id)
                                            print(job["status"])
                                            if job is not None and job.get("status") == "finished":
                                                result = json.dumps(job["result"], ensure_ascii=False)
                                                message = {
                                                    "performative": "inform",
                                                    "sender": agent_constants.name,
                                                    "receivers": [input_data.get("sender")],
                                                    "reply-to": input_data.get("content"),
                                                    "content": result,
                                                    "language": "sparql",
                                                    "protocol": "fipa-request protocol",
                                                    "reply-with": result,
                                                    "conversationID": input_data.get('conversationID'),
                                                    "enconding": "utf-8",
                                                    "ontology": "",
                                                    "in-reply-to": "",
                                                    "reply-by": ""
                                                }

                                                new_loop = asyncio.new_event_loop()
                                                asyncio.set_event_loop(new_loop)
                                                new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                                                        io_loop=new_loop)
                                                new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                                new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                                db_id = new_loop.run_until_complete(replace_data_in_db(
                                                    dict_item={
                                                        "conversationID": input_data.get("conversationID").strip(),
                                                        "start_time": time.time()}, key="conversationID",
                                                    mongo_data_base=new_collection_ids))
                                                new_loop.close()

                                                # conversation_ids[input_data.get("conversationID")] = time.time()
                                                return json.dumps(message, ensure_ascii=False)
                                            elif job["status"] == "executing":
                                                return 'Not ready', 202
                                            else:
                                                return "Not found", 404
                                        except:
                                            return "Not found", 404
                                    elif input_data.get("performative") == "subscribe":
                                        #if input_data.get("conversationID") not in conversation_ids:
                                        if conversationID_obj is None:

                                            new_loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(new_loop)
                                            new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                                                    io_loop=new_loop)
                                            new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                            new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                            db_id = new_loop.run_until_complete(put_data_to_db(
                                                dict_item={"conversationID": input_data.get("conversationID").strip(),
                                                           "start_time": time.time()},
                                                mongo_data_base=new_collection_ids))
                                            new_loop.close()

                                            #conversation_ids[input_data.get("conversationID")] = time.time()
                                            message = {
                                                "performative": "confirm",
                                                "sender": agent_constants.name,
                                                "receivers": [input_data.get("sender")],
                                                "reply-to": input_data.get("content"),
                                                "content": "registed",
                                                "language": "en",
                                                "protocol": "fipa-request protocol",
                                                "reply-with": "registed",
                                                "conversationID": input_data.get('conversationID'),
                                                "enconding": "utf-8",
                                                "ontology": "",
                                                "in-reply-to": "",
                                                "reply-by": ""
                                            }
                                            return json.dumps(message, ensure_ascii=False)
                                        else:
                                            # conversation_ids[input_data.get("conversationID")] = time.time()

                                            new_loop = asyncio.new_event_loop()
                                            asyncio.set_event_loop(new_loop)
                                            new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                                                    io_loop=new_loop)
                                            new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                            new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                            db_id = new_loop.run_until_complete(replace_data_in_db(
                                                dict_item={
                                                    "conversationID": input_data.get("conversationID").strip(),
                                                    "start_time": time.time()}, key="conversationID",
                                                mongo_data_base=new_collection_ids))
                                            new_loop.close()


                                            message = {
                                                    "performative": "refuse",
                                                    "sender": agent_constants.name,
                                                    "receivers": [input_data.get("sender")],
                                                    "reply-to": input_data.get("content"),
                                                    "content": "This ID already exists",
                                                    "language": "en",
                                                    "protocol": "fipa-request protocol",
                                                    "reply-with": "This ID already exists",
                                                    "conversationID": input_data.get('conversationID'),
                                                    "enconding": "utf-8",
                                                    "ontology": "",
                                                    "in-reply-to": "",
                                                    "reply-by": ""
                                                }
                                            return json.dumps(message, ensure_ascii=False)
                                    elif input_data.get("performative") == "unsubscribe":
                                        #if input_data.get("conversationID") in conversation_ids:
                                        if conversationID_obj is not None:
                                            message = {
                                                "performative": "confirm",
                                                "sender": agent_constants.name,
                                                "receivers": [input_data.get("sender")],
                                                "reply-to": input_data.get("content"),
                                                "content": "logout",
                                                "language": "en",
                                                "protocol": "fipa-request protocol",
                                                "reply-with": "logout",
                                                "conversationID": input_data.get('conversationID'),
                                                "enconding": "utf-8",
                                                "ontology": "",
                                                "in-reply-to": "",
                                                "reply-by": ""
                                            }
                                            try:

                                                new_loop = asyncio.new_event_loop()
                                                asyncio.set_event_loop(new_loop)
                                                new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url,
                                                                                                        io_loop=new_loop)
                                                new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                                new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                                db_id = new_loop.run_until_complete(delete_data_from_db(
                                                    dict_item={
                                                        "conversationID": input_data.get("conversationID").strip()},
                                                    mongo_data_base=new_collection_ids))
                                                new_loop.close()

                                                #del conversation_ids[input_data.get("conversationID")]
                                            except Exception as e:
                                                print(e)
                                                print(traceback.format_exc())

                                                message = {
                                                    "performative": "error",
                                                    "sender": agent_constants.name,
                                                    "receivers": [input_data.get("sender")],
                                                    "reply-to": input_data.get("content"),
                                                    "content": "Unable to delete ID",
                                                    "language": "en",
                                                    "protocol": "fipa-request protocol",
                                                    "reply-with": "Unable to delete ID",
                                                    "conversationID": input_data.get('conversationID'),
                                                    "enconding": "utf-8",
                                                    "ontology": "",
                                                    "in-reply-to": "",
                                                    "reply-by": ""
                                                }
                                                return json.dumps(message, ensure_ascii=False)
                                            return json.dumps(message, ensure_ascii=False)
                                        else:
                                            message = {
                                                "performative": "refuse",
                                                "sender": agent_constants.name,
                                                "receivers": [input_data.get("sender")],
                                                "reply-to": input_data.get("content"),
                                                "content": "This ID does not exist",
                                                "language": "en",
                                                "protocol": "fipa-request protocol",
                                                "reply-with": "This ID does not exist",
                                                "conversationID": input_data.get('conversationID'),
                                                "enconding": "utf-8",
                                                "ontology": "",
                                                "in-reply-to": "",
                                                "reply-by": ""
                                            }
                                            return json.dumps(message, ensure_ascii=False)

                            else:
                                message = {
                                    "performative": "refuse",
                                    "sender": agent_constants.name,
                                    "receivers": [input_data.get("sender")],
                                    "reply-to": input_data.get("content"),
                                    "content": "This service is for Ukrainian language",
                                    "language": "en",
                                    "protocol": "fipa-request protocol",
                                    "reply-with": "This service is for Ukrainian language",
                                    "conversationID": input_data.get('conversationID'),
                                    "enconding": "utf-8",
                                    "ontology": "",
                                    "in-reply-to": "",
                                    "reply-by": ""
                                }

                                new_loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(new_loop)
                                new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
                                new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                                new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                                db_id = new_loop.run_until_complete(replace_data_in_db(
                                    dict_item={
                                        "conversationID": input_data.get("conversationID").strip(),
                                        "start_time": time.time()}, key="conversationID",
                                    mongo_data_base=new_collection_ids))
                                new_loop.close()

                                # conversation_ids[input_data.get("conversationID")] = time.time()
                                return json.dumps(message, ensure_ascii=False)
                        else:
                            message = {
                                "performative": "refuse",
                                "sender": agent_constants.name,
                                "receivers": [input_data.get("sender")],
                                "reply-to": input_data.get("content"),
                                "content": "Messeges must have fipa-request protocol",
                                "language": "en",
                                "protocol": "fipa-request protocol",
                                "reply-with": "Messeges must have fipa-request protocol",
                                "conversationID": input_data.get('conversationID'),
                                "enconding": "utf-8",
                                "ontology": "",
                                "in-reply-to": "",
                                "reply-by": ""
                            }

                            new_loop = asyncio.new_event_loop()
                            asyncio.set_event_loop(new_loop)
                            new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
                            new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                            new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                            db_id = new_loop.run_until_complete(replace_data_in_db(
                                dict_item={
                                    "conversationID": input_data.get("conversationID").strip(),
                                    "start_time": time.time()}, key="conversationID",
                                mongo_data_base=new_collection_ids))
                            new_loop.close()

                            # conversation_ids[input_data.get("conversationID")] = time.time()
                            return json.dumps(message, ensure_ascii=False)
                    else:
                        message = {
                            "performative": "refuse",
                            "sender": agent_constants.name,
                            "receivers": [input_data.get("sender")],
                            "reply-to": input_data.get("content"),
                            "content": "This massage is not destinated to this service",
                            "language": "en",
                            "protocol": "fipa-request protocol",
                            "reply-with": "This massage is not destinated to this service",
                            "conversationID": input_data.get('conversationID'),
                            "enconding": "utf-8",
                            "ontology": "",
                            "in-reply-to": "",
                            "reply-by": ""
                        }
                        return json.dumps(message, ensure_ascii=False)
                elif input_data.get("performative") == "subscribe":
                    if conversationID_obj is None: #input_data.get("conversationID") not in conversation_ids:

                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
                        new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                        new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                        db_id = new_loop.run_until_complete(put_data_to_db(
                            dict_item={
                                "conversationID": input_data.get("conversationID").strip(),
                                "start_time": time.time()},
                            mongo_data_base=new_collection_ids))
                        new_loop.close()

                        # conversation_ids[input_data.get("conversationID")] = time.time()
                        message = {
                            "performative": "confirm",
                            "sender": agent_constants.name,
                            "receivers": [input_data.get("sender")],
                            "reply-to": input_data.get("content"),
                            "content": "registed",
                            "language": "en",
                            "protocol": "fipa-request protocol",
                            "reply-with": "registed",
                            "conversationID": input_data.get('conversationID'),
                            "enconding": "utf-8",
                            "ontology": "",
                            "in-reply-to": "",
                            "reply-by": ""
                        }
                        return json.dumps(message, ensure_ascii=False)
                    else:

                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
                        new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                        new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

                        db_id = new_loop.run_until_complete(replace_data_in_db(
                            dict_item={
                                "conversationID": input_data.get("conversationID").strip(),
                                "start_time": time.time()}, key="conversationID",
                            mongo_data_base=new_collection_ids))
                        new_loop.close()


                        # conversation_ids[input_data.get("conversationID")] = time.time()
                        message = {
                            "performative": "refuse",
                            "sender": agent_constants.name,
                            "receivers": [input_data.get("sender")],
                            "reply-to": input_data.get("content"),
                            "content": "This ID already exists",
                            "language": "en",
                            "protocol": "fipa-request protocol",
                            "reply-with": "This ID already exists",
                            "conversationID": input_data.get('conversationID'),
                            "enconding": "utf-8",
                            "ontology": "",
                            "in-reply-to": "",
                            "reply-by": ""
                        }
                        return json.dumps(message, ensure_ascii=False)
                else:
                    message = {
                        "performative": "refuse",
                        "sender": agent_constants.name,
                        "receivers": [input_data.get("sender")],
                        "reply-to": input_data.get("content"),
                        "content": "Unregisted conversation ID",
                        "language": "en",
                        "protocol": "fipa-request protocol",
                        "reply-with": "Unregisted conversation ID",
                        "conversationID": input_data.get('conversationID'),
                        "enconding": "utf-8",
                        "ontology": "",
                        "in-reply-to": "",
                        "reply-by": ""
                    }
                    return json.dumps(message, ensure_ascii=False)
            else:
                message = {
                    "performative": "refuse",
                    "sender": agent_constants.name,
                    "receivers": [input_data.get("sender")],
                    "reply-to": input_data.get("content"),
                    "content": "No password",
                    "language": "en",
                    "protocol": "fipa-request protocol",
                    "reply-with": "No password",
                    "conversationID": input_data.get('conversationID'),
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
                }
                return json.dumps(message, ensure_ascii=False)
        elif "sender" in input_data:
            message = {
                "performative": "refuse",
                "sender": agent_constants.name,
                "receivers": [input_data.get("sender")],
                "reply-to": input_data.get("content"),
                "content": "Wrong message format",
                "language": "en",
                "protocol": "fipa-request protocol",
                "reply-with": "Wrong message format",
                "conversationID": input_data.get('conversationID'),
                "enconding": "utf-8",
                "ontology": "",
                "in-reply-to": "",
                "reply-by": ""
            }
            # conversation_ids[input_data.get("conversationID")] = time.time()
            return json.dumps(message, ensure_ascii=False)
        else:
            return "Wromg message format", 400

    else:
        return "Ukrainian text to common SPARQL queries conversion service is working"


def remove_old_ids(sleep_interval=10, limitation=10000):
    global is_running
    lock = threading.Lock()
    while is_running:
        lock.acquire()
        try:
            # print("removing old IDs")
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
            new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
            new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)

            id_docs = new_loop.run_until_complete(get_all_data_from_db(
                                                  mongo_data_base=new_collection_ids))
            new_loop.close()

            for doc in id_docs:
            #for conversation_id in conversation_ids:
                if (time.time() - doc.get("start_time")) > limitation:
                    new_loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(new_loop)
                    new_client_ids = motor.motor_asyncio.AsyncIOMotorClient(id_db_url, io_loop=new_loop)
                    new_db_ids = eval('new_client_ids.' + id_db_config.db_name)
                    new_collection_ids = eval('new_db_ids.' + id_db_config.collection_name)
                    # print("id doc", doc)
                    cur_id = doc.get('conversationID')
                    res = new_loop.run_until_complete(delete_data_from_db(
                        dict_item={'conversationID': cur_id},
                        mongo_data_base=new_collection_ids))
                    new_loop.close()
                    print("Old conversation ID ", cur_id, " was deleted")
                    # ids_to_delete.append(conversation_id)
            #for conversation_id in ids_to_delete:
            #    del conversation_ids[conversation_id]
            #    print("Old conversation ID ", conversation_id, " was deleted")
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            print("Unable to delete old IDs ")
        finally:
            lock.release()

        time.sleep(sleep_interval)


def make_conversion(input_text="", entities_names=None, entities_names_file="converter/converter_config.xml",
                    analyzer=None, marker_words=None, marker_words_file="converter/marker_words.xml", templates=None,
                    query_templates_file="converter/query_template.xml", ontology_config=None,
                    ontology_config_file="converter/ontologies_list.xml",  mongo_data_base=None,
                    method_of_conversion="convert_common"):
    global keywords, keywords_ep, keywords_aliyev
    s_time = time.time()
    print("method_of_conversion", method_of_conversion)
    if method_of_conversion == "convert_common":
        entities = converter.sparql_converter.get_entities_for_common_query(input_text=input_text,
                                                                            entities_names=entities_names,
                                                 entities_names_file=entities_names_file,
                                                 analyzer=analyzer, marker_words=marker_words,
                                                 marker_words_file=marker_words_file)
        print("entities extraction", (time.time() - s_time))

        s_time = time.time()
        query_set = converter.sparql_converter.form_set_of_common_queries_with_randomization(entities_list=entities, templates=templates,
                                                                  query_templates_file=query_templates_file,
                                                                  ontology_config=ontology_config,
                                                                  ontology_config_file=ontology_config_file,
                                                                  mongo_data_base=mongo_data_base)
    elif method_of_conversion == "convert_special":
        query_template, query_type, entities_for_query = converter.sparql_converter.select_query_template(
            input_text=input_text, templates=templates, current_keywords=keywords)
        query_set = converter.sparql_converter.form_set_of_special_queries(query_template=query_template,
                                                                           entities_for_query=entities_for_query,
                                                                           query_type=query_type)
    elif method_of_conversion == "convert_special_ep":
        query_template, query_type, entities_for_query = converter.sparql_converter.select_query_template(
            input_text=input_text, templates=templates, current_keywords=keywords_ep)
        query_set = converter.sparql_converter.form_set_of_special_queries(query_template=query_template,
                                                                           entities_for_query=entities_for_query,
                                                                           query_type=query_type,
                                                                           ontology="ontology_ep")
    elif method_of_conversion == "convert_special_aliyev":
        print("keywords_aliyev ", keywords_aliyev)
        query_template, query_type, entities_for_query = converter.sparql_converter.select_query_template(
            input_text=input_text, templates=templates, current_keywords=keywords_aliyev)
        query_set = converter.sparql_converter.form_set_of_special_queries(query_template=query_template,
                                                                           entities_for_query=entities_for_query,
                                                                           query_type=query_type,
                                                                           ontology="aliyev")
    else:
        query_template, query_type, entities_for_query = converter.sparql_converter.select_query_template(
            input_text=input_text, templates=templates, current_keywords=keywords)
        query_set = converter.sparql_converter.form_set_of_special_queries(query_template=query_template,
                                                                           entities_for_query=entities_for_query,
                                                                           query_type=query_type,
                                                                           ontology=method_of_conversion)

    print("query formation", (time.time() - s_time))


    return query_set


def send_response_on_finishing(question_id=""):
    try:
        resp_message = {
            "performative": "inform",
            "sender": agent_constants.name,
            "receivers": [],
            "reply-to": "",
            "content": question_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": question_id,
            "conversationID": "",
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        resp = requests.post(url=agent_constants.responding_url, json=resp_message)
        return True
    except Exception as e:
        print(e)
        print(traceback.format_exc())
        return False


def shutdown_server():
    global is_running
    is_running = False
    for t in global_threads:
        t.join()

    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        return False
    func()
    return True

@app.route('/shutdown', methods=['POST'])
def shutdown():
    input_data = request.json
    try:
        if "password" in input_data:
            new_key = hashlib.pbkdf2_hmac('sha256', input_data.get("password").encode('utf-8'), salt, 100000)
            if new_key == key:
                shutdown_result = shutdown_server()
                if shutdown_result:
                    resp_message = {
                        "performative": "confirm",
                        "sender": agent_constants.name,
                        "receivers": [input_data.get("sender")],
                        "reply-to": "",
                        "content": 'Server shutting down',
                        "language": "en",
                        "protocol": "fipa-request protocol",
                        "reply-with": 'Server shutting down',
                        "conversationID": "",
                        "enconding": "utf-8",
                        "ontology": "",
                        "in-reply-to": "",
                        "reply-by": ""
                    }
                    return json.dumps(resp_message, ensure_ascii=False)
                else:
                    resp_message = {
                        "performative": "failure",
                        "sender": agent_constants.name,
                        "receivers": [input_data.get("sender")],
                        "reply-to": "",
                        "content": 'Failure to shut down the server',
                        "language": "en",
                        "protocol": "fipa-request protocol",
                        "reply-with": 'Failure to shut down the server',
                        "conversationID": "",
                        "enconding": "utf-8",
                        "ontology": "",
                        "in-reply-to": "",
                        "reply-by": ""
                    }
                    return json.dumps(resp_message, ensure_ascii=False)
            else:
                resp_message = {
                    "performative": "refuse",
                    "sender": agent_constants.name,
                    "receivers": [input_data.get("sender")],
                    "reply-to": "",
                    "content": 'Wrong password',
                    "language": "en",
                    "protocol": "fipa-request protocol",
                    "reply-with": 'Wrong password',
                    "conversationID": "",
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
                }
                return json.dumps(resp_message, ensure_ascii=False)
        else:
            resp_message = {
                "performative": "refuse",
                "sender": agent_constants.name,
                "receivers": [input_data.get("sender")],
                "reply-to": "",
                "content": 'No password',
                "language": "en",
                "protocol": "fipa-request protocol",
                "reply-with": 'Wrong password',
                "conversationID": "",
                "enconding": "utf-8",
                "ontology": "",
                "in-reply-to": "",
                "reply-by": ""
            }
            return json.dumps(resp_message, ensure_ascii=False)
    except:
        resp_message = {
            "performative": "refuse",
            "sender": agent_constants.name,
            "receivers": [],
            "reply-to": "",
            "content": 'Wrong format',
            "language": "en",
            "protocol": "fipa-request protocol",
            "reply-with": 'Wrong password',
            "conversationID": "",
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        return json.dumps(resp_message, ensure_ascii=False)

thr = threading.Thread(target=remove_old_ids, kwargs={"sleep_interval": agent_constants.check_ids_interval,
                                                      "limitation": agent_constants.limitation},
                                                      name="remove_old_ids", daemon=True)
global_threads.append(thr)
thr.start()

if __name__ == "__main__":
    app.run(threaded=True, host=agent_constants.host, port=int(os.environ.get("PORT", 6015))) #port=agent_constants.port)
    thr.join()

