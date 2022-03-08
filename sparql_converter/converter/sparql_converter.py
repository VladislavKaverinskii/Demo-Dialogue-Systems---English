# -*- coding: utf8 -*-

import asyncio
import json
import xml.etree.ElementTree as Et
from argparse import ArgumentParser
import random
import time
import hashlib
# from rq import job

# import text_analysis_handlers

import nltk
from nltk.stem.porter import PorterStemmer

nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('maxent_ne_chunker')
nltk.download('words')
nltk.download('maxent_treebank_pos_tagger')
nltk.download('treebank')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger_ru')
porter = PorterStemmer()


try:
    import query_template_qualifier_special
except:
    import converter.query_template_qualifier_special as query_template_qualifier_special

'''
try:
    qualifier_config = query_template_qualifier_special.QualifierConfig.get_instance(
        config_file="converter/tree.xml")
except FileNotFoundError as e:
    print(e)
    qualifier_config = query_template_qualifier_special.QualifierConfig.get_instance(
        config_file="tree.xml")
'''
qualifier_config = query_template_qualifier_special.QualifierConfig.get_instance(
        config_file="tree.xml")


class DBConstants:
    __instance = None
    def __init__(self):
        if not DBConstants.__instance:
            self.admin = ""
            self.password = ""
            self.db_url = ""
            self.db_name = ""
            self.collection_name = ""
            self.url_base = ""
        else:
            print("Instance already created:", self.getInstance())

    @classmethod
    def get_instance(cls, config_file="mongo_client_config_ontology.xml"):
        if not cls.__instance:
            cls.__instance = DBConstants()
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


class QueryTemplates:
    __instance = None

    def __init__(self):
        if not QueryTemplates.__instance:
            self.templates = []
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="query_template.xml"):
        if not cls.__instance:
            cls.__instance = QueryTemplates()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                tree = Et.fromstring((xml_file).read().encode('utf-8').decode('utf-8'))
            # tree = Et.parse(config_file)
            # root = tree.getroot()
            for query_template in tree:
                if query_template.tag == "template":
                    new_template = {}
                    for item in query_template:
                        if item.tag == "language":
                            new_template["language"] = item.text.strip()
                        elif item.tag == "type":
                            new_template["type"] = item.text.strip()
                        elif item.tag == "marker_words":
                            if len(item) > 0:
                                new_template["marker_words"] = [m_word.text.strip() for m_word in item]
                            else:
                                new_template["marker_words"] = []
                        elif item.tag == "variables":
                            variables = {}
                            for variable in item:
                                if variable.tag == "variable":
                                    var_name = variable.find("name").text.strip()
                                    if var_name is not None:
                                        variables[var_name] = {
                                            "name": var_name,
                                            "type": variable.find("var_type").text.strip(),
                                            "destination": variable.find("destination").text.strip(),
                                            "allow_list": variable.find("allow_list").text.strip()
                                        }
                            new_template["variables"] = variables
                        elif item.tag == "query_base":
                            new_template["query_base"] = item.text.strip()
                        elif item.tag == "conditions":
                            if len(item) > 0:
                                new_template["conditions"] = [condition.text.strip() for condition in item]
                            else:
                                new_template["conditions"] = []
                        elif item.tag == "ordering":
                            new_template["ordering"] = item.text.strip()
                    cls.__instance.templates.append(new_template)

        return cls.__instance


class InputVarsNames:
    __instance = None

    def __init__(self):
        if not InputVarsNames.__instance:
            self.any = ""
            self.marker_word = ""
            self.action_entity = ""
            self.object_entity = ""
            self.number_entity = ""
            self.adjective_entity = ""
            self.adverb_entity = ""
        else:
            print("Instance already created:", self.getInstance())

    @classmethod
    def get_instance(cls, config_file="converter_config.xml"):
        if not cls.__instance:
            cls.__instance = InputVarsNames()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for item in root:
                if item.tag == "input_variables_names_description":
                    for variable in item:
                        if variable.find("destination") is not None:
                            if variable.find("destination").text.strip() == "any":
                                if variable.find("name") is not None:
                                    cls.__instance.any = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "marker_word":
                                if variable.find("name") is not None:
                                    cls.__instance.marker_word = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "action_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.action_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "object_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.object_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "number_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.number_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "adjective_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.adjective_entity = variable.find("name").text.strip()
                            elif variable.find("destination").text.strip() == "adverb_entity":
                                if variable.find("name") is not None:
                                    cls.__instance.adverb_entity = variable.find("name").text.strip()
        return cls.__instance


class MarkerWords:
    __instance = None
    def __init__(self):
        if not MarkerWords.__instance:
            self.marker_words = {}
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="marker_words.xml"):
        if not cls.__instance:
            cls.__instance = MarkerWords()
            cls.__instance.config_file = config_file
            f = open(config_file, 'r', encoding='utf-8')
            tree = Et.ElementTree(Et.fromstring(f.read()))
            root = tree.getroot()
            for i in root:
                if i.tag == "item":
                    word = i.find("word").text.strip()
                    type = i.find("type").text.strip()
                    cls.__instance.marker_words[word] = type
        return cls.__instance


class Ontologies:
    __instance = None
    def __init__(self):
        if not Ontologies.__instance:
            self.ontologies_names = []
            self.ontology_key_words = {}
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
            loop = asyncio.get_event_loop()
            for i in root:
                if i.tag == "ontologies":
                    for onto_name in i:
                        cls.__instance.ontologies_names.append(onto_name.text.strip())
                        #try:
                        #    loop = asyncio.get_event_loop()
                        #except RuntimeError:

                        '''
                        new_loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(new_loop)
                        new_client_ontology = motor.motor_asyncio.AsyncIOMotorClient(ontology_db_url, io_loop=new_loop)
                        new_db_ontology = eval('new_client_ontology.' + ontology_db_config.db_name)
                        new_collection_ontology = eval('new_db_ontology.' + ontology_db_config.collection_name)

                        '''
                        data = loop.run_until_complete(get_data_from_db(dict_item={"name": onto_name.text.strip()},
                                                                        mongo_data_base=mongo_data_base))

                        # print(data)
                        cls.__instance.ontology_key_words[onto_name.text.strip()] = data.get('key_words')
                elif i.tag == "default_ontology":
                    cls.__instance.default_ontology = i.text.strip()
            loop.close()
        return cls.__instance


class ApiConstants:
    __instance = None
    def __init__(self):
        if not ApiConstants.__instance:
            self.config_file = ""
            self.main_host = ""
            self.api_address = ""
            self.allterms_address = ""
            self.parce_address = ""
            self.headers = {
                'Content-Type': "",
                'content-type': ""
            }
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="api_config.xml"):
        if not cls.__instance:
            cls.__instance = ApiConstants()
            cls.__instance.config_file = config_file
            tree = Et.parse(config_file)
            root = tree.getroot()
            for i in root:
                if i.tag == "main_host":
                    cls.__instance.main_host = i.text.strip()
                if i.tag == "api_address":
                    cls.__instance.api_address = i.text.strip()
                if i.tag == "allterms_address":
                    cls.__instance.allterms_address = i.text.strip()
                if i.tag == "parce_address":
                    cls.__instance.parce_address = i.text.strip()
                if i.tag == "headers":
                    for j in i:
                        if j.tag == "Content-Type":
                            cls.__instance.headers["Content-Type"] = j.text.strip()
                        if j.tag == "content_type":
                            cls.__instance.headers["content-type"] = j.text.strip()
        return cls.__instance

api_config = ApiConstants()

class AnalyzerAPIWrapper:
    def __init__(self, config=None, config_file="api_config.xml"):
        if config is None:
            self.config = ApiConstants().get_instance(config_file=config_file)
        else:
            self.config = config.get_instance(config_file=config_file)

    def __api_request__(self, url_ip="test.ulif.org.ua:51080", api_address="/ken/api/en/", command="alltermsxml",
                        text="", headers=None):
        data = {"message": text}

        if headers is None:
            headers = {
                'Content-Type': "multipart/form-data",
                'content-type': "multipart/form-data"
            }
        result = ""
        request_done = False
        counter = 0
        while not request_done and counter < 100:
            counter += 1
            try:
                result = requests.post(url="http://" + url_ip + api_address + command, json=data).text
                request_done = True
                counter = 101
            except Exception as e:
                print(e)
                request_done = False
        return result

    def get_allterms_xml(self, text=""):
        return self.__api_request__(url_ip=self.config.main_host, api_address=self.config.api_address,
                                    command=self.config.allterms_address, text=text, headers=self.config.headers)

    def get_parce_xml(self, text=""):
        return self.__api_request__(url_ip=self.config.main_host, api_address=self.config.api_address,
                                    command=self.config.parce_address, text=text, headers=self.config.headers)


analyzer = AnalyzerAPIWrapper(config=api_config, config_file="api_config.xml")


def form_query(query_template=None, input_vars=None):
    if query_template is not None and input_vars is not None:
        print(input_vars)
        if isinstance(query_template, dict) and isinstance(input_vars, dict):
            query_base = query_template.get("query_base")
            for variable in query_template.get("variables"):
                print("destination", query_template.get("variables").get(variable).get("destination").lower())
                if query_template.get("variables").get(variable).get("destination").lower() == "result":
                    print(query_template.get("variables").get(variable).get("name"))
                    if "[" + query_template.get("variables").get(variable).get("name") + "]" in query_base:
                        query_base = query_base.replace(
                            "[" + query_template.get("variables").get(variable).get("name") + "]",
                            "?" + query_template.get("variables").get(variable).get("name"))
            template_text = query_base
            # print(input_vars)
            key_to_del = [key for key in input_vars if len(input_vars[key]) < 1]
            for key in key_to_del:
                del input_vars[key]
            # if len(input_vars) < 1:
            #    return ""
            if len(query_template.get("conditions")) > 0:
                template_text += " WHERE {"
                for condition in query_template.get("conditions"):
                    new_condition_string = condition
                    if len(condition) > 0:
                        if condition[-1] != ".":
                            new_condition_string += "."
                        for variable in query_template.get("variables"):
                            if ((query_template.get("variables").get(variable).get("destination").lower() ==
                                 "inner")
                                or (query_template.get("variables").get(variable).get("destination").lower() ==
                                    "result")):
                                if "["+query_template.get("variables").get(variable).get("name") + "]" in condition:
                                    new_condition_string = new_condition_string.replace(
                                        "[" + query_template.get("variables").get(variable).get("name") + "]",
                                        "?" + query_template.get("variables").get(variable).get("name"))
                            elif query_template.get("variables").get(variable).get("destination").lower() == "input":
                                for input_var in input_vars:
                                    if input_var == query_template.get("variables").get(variable).get("name"):
                                        if "[" + input_var + "]" in condition:
                                            if isinstance(input_vars.get(input_var), list) or isinstance(input_vars.get(input_var), set):
                                                if len(input_vars.get(input_var)) > 0:
                                                    if query_template.get("variables").get(variable).get(
                                                            "allow_list").lower() == "true":
                                                        new_condition_string = " ".join(
                                                            [new_condition_string.replace(
                                                                "[" + query_template.get("variables").get(variable).get(
                                                                    "name") + "]", ":" + str(var_value)) for var_value
                                                                in input_vars.get(input_var)])
                                                    else:
                                                        new_condition_string = new_condition_string.replace(
                                                            "[" + query_template.get("variables").get(variable).get(
                                                                "name") + "]",
                                                            ":" + str(input_vars.get(input_var)[0]))
                                            else:
                                                new_condition_string = new_condition_string.replace(
                                                    "[" + query_template.get("variables").get(variable).get(
                                                        "name") + "]",
                                                    ":" + str(input_vars.get(input_var)))
                                # print(new_condition_string)
                    template_text += " " + new_condition_string + " "
                template_text += "}"
            if 'ordering' in query_template and len(query_template.get('ordering')) > 0:
                template_text += " ORDER BY ?" + query_template.get('ordering').replace("[", "").replace("]", "").strip()
            return template_text
    return ""


def digit_symbol_replacer(input_digit_string="0"):
    if input_digit_string == "0":
        return "Null"
    elif input_digit_string == "1":
        return "En"
    elif input_digit_string == "2":
        return "To"
    elif input_digit_string == "3":
        return "Tre"
    elif input_digit_string == "4":
        return "Fire"
    elif input_digit_string == "5":
        return "Fem"
    elif input_digit_string == "6":
        return "Seks"
    elif input_digit_string == "7":
        return "Sju"
    elif input_digit_string == "8":
        return "Åtte"
    elif input_digit_string == "9":
        return "Ni"
    else:
        return input_digit_string


def digit_string_replacer(input_digit_string="0"):
    out_str = ""
    for symbol in input_digit_string:
        if symbol.isdigit():
            out_str += digit_symbol_replacer(symbol)
        else:
            out_str += symbol
    return out_str


class WordObj:
    def __init__(self, pos="", word=""):
        self.pos = pos
        self.word = word

    def __hash__(self):
        return int(hashlib.md5((self.pos + self.word).encode()).hexdigest(), 16)

    def serialize(self):
        return {self.word: self.pos}


def get_entities_for_common_query(input_text="", entities_names=None, entities_names_file="converter_config.xml",
                                  analyzer=None, marker_words=None, marker_words_file="marker_words.xml"):
    if entities_names is None:
        names_description = InputVarsNames().get_instance(config_file=entities_names_file)
    else:
        names_description = entities_names.get_instance(config_file=entities_names_file)
    if analyzer is None:
        analyzer = AnalyzerAPIWrapper()

    if marker_words is None:
        marker_words = MarkerWords().get_instance(config_file=marker_words_file)
    else:
        marker_words = marker_words.get_instance(config_file=marker_words_file)


    work_text = input_text.replace('"', "").replace('?', "").replace("'", "").replace("(", " ").replace(")", " ").replace("+", "Plus").replace("&", " Og ").replace("%", " Prosent").replace("- ", " ")

    entities = []

    graph =analyzer.get_parce_xml(work_text)

    tree = Et.ElementTree(Et.fromstring(graph))
    root = tree.getroot()
    text_block = root.find("text")
    for sentence in text_block:
        current_classes = set()
        for item in sentence:
            if item.tag == "item":
                # print(item.find("lemma").text)
                if item.find("speech").text.lower() == "s4":
                    if item.find("lemma") is not None and item.find("lemma").text is not None:
                        class_id = item.find("lemma").text.capitalize().replace('.', "")
                        add_to_current = True
                        for obj in current_classes:
                            if obj.word != item.find("lemma").text.capitalize() and item.find(
                                    "lemma").text.capitalize() in obj.word:
                                add_to_current = False
                        if add_to_current:
                            current_classes.add(WordObj(pos="verb", word=class_id.replace('.', "")))
                elif (item.find("speech").text.lower() == "s1" or item.find("speech").text.lower() == "s6"
                          or item.find("speech").text.lower() == "s13" or item.find("speech").text.lower() == "s5"
                          or item.find("speech").text.lower() == "s11" or item.find("speech").text.lower() == "s518"
                          or item.find("speech").text.lower() == "s22" or item.find("speech").text.lower() == "s25"
                          or item.find("speech").text.lower() == "s28" or item.find("speech").text.lower() == "s29"):
                    if item.find("lemma") is not None and item.find("lemma").text is not None:
                        class_id = item.find("lemma").text.capitalize().replace('.', "")
                        add_to_current = True
                        for obj in current_classes:
                            if obj.word.replace('.', "") != item.find("lemma").text.capitalize().replace('.', "") and item.find(
                                    "lemma").text.capitalize().replace('.', "") in obj.word.replace('.', ""):
                                add_to_current = False
                        if add_to_current:
                            current_classes.add(WordObj(pos="object", word=class_id.replace('.', "")))
                elif item.find("speech").text.lower() == "s7":
                    if item.find("lemma") is not None and item.find("lemma").text is not None:
                        class_id = digit_string_replacer(item.find("lemma").text.capitalize()).replace('.', "")
                        current_classes.add(WordObj(pos="number", word=class_id.replace('.', "")))
                elif (item.find("speech").text.lower() == "s2" or item.find("speech").text.lower() == "s20"
                          or item.find("speech").text.lower() == "s10" or item.find("speech").text.lower() == "s14"):
                    linked_noun_found = False
                    for item_2 in sentence:
                        if item_2.tag == "item":
                            if (item_2.find("speech").text.lower() == "s1"
                                      or item_2.find("speech").text.lower() == "s6"
                                      or item_2.find("speech").text.lower() == "s13"
                                      or item_2.find("speech").text.lower() == "s5"
                                      or item_2.find("speech").text.lower() == "s11"
                                      or item_2.find("speech").text.lower() == "s518"
                                      or item_2.find("speech").text.lower() == "s22"
                                      or item_2.find("speech").text.lower() == "s25"
                                      or item_2.find("speech").text.lower() == "s28"
                                      or item_2.find("speech").text.lower() == "s29"):
                                if (item_2.find("relate") is not None and item_2.find("relate").text is not None
                                        and item.find("relate") is not None and item.find("relate").text is not None and
                                        item.find("number") is not None and item.find("number").text is not None and
                                        item_2.find("number") is not None and item_2.find("number").text is not None):
                                    if ((item_2.find("relate").text.lower() == item.find("number").text.lower()) or
                                            (item.find("relate").text.lower() == item_2.find("number").text.lower())):
                                        new_class_id = item.find("lemma").text.capitalize().replace('.', "") + item_2.find(
                                            "lemma").text.capitalize().replace('.', "")
                                        #objects.add(new_class_id)
                                        obj_to_del = set()
                                        tmp_pos = "object"

                                        for obj in current_classes:
                                            if obj.word.replace('.', "") == item_2.find("lemma").text.capitalize().replace('.', ""):
                                                obj.word = obj.word.replace('.', "")
                                                obj_to_del.add(obj)
                                                break
                                        for obj in obj_to_del:
                                            tmp_obj = obj
                                            tmp_obj.word = obj.word.replace('.', "")
                                            current_classes.discard(tmp_obj)
                                        current_classes.add(WordObj(pos=tmp_pos, word=new_class_id.replace('.', "")))
                                        linked_noun_found = True
                    if not linked_noun_found:
                        if item.find("lemma") is not None and item.find("lemma").text is not None:
                            class_id = item.find("lemma").text.capitalize()
                            current_classes.add(WordObj(pos="adjective", word=class_id.replace('.', "")))
                elif (item.find("speech").text.lower() == "s12" or item.find("speech").text.lower() == "s19"
                          or item.find("speech").text.lower() == "s16" or item.find("speech").text.lower() == "s24"
                          or item.find("speech").text.lower() == "s23"):
                    if item.find("number") is not None and item.find("lemma").text is not None:
                        if (item.find("number") != "1" and item.find("lemma").text.lower().replace('.', "")
                                not in marker_words.marker_words):
                            linked_noun_found = False
                            for item_2 in sentence:
                                if item_2.tag == "item":
                                    if (item_2.find("speech").text.lower() == "s4" or
                                        item_2.find("speech").text.lower() == "s12" or
                                        item_2.find("speech").text.lower() == "s19"
                                        or item_2.find("speech").text.lower() == "s16"
                                        or item_2.find("speech").text.lower() == "s24"
                                        or item_2.find("speech").text.lower() == "s23"):
                                        if item_2.find("relate") is not None and item_2.find("relate").text is not None:
                                            if ((item_2.find("relate").text.lower() == item.find("number").text.lower())
                                                    or (item.find("relate").text.lower() == item_2.find(
                                                        "number").text.lower())):
                                                if (item_2.find("speech").text.lower() == "s12" or
                                                    item_2.find("speech").text.lower() == "s19"
                                                    or item_2.find("speech").text.lower() == "s16"
                                                    or item_2.find("speech").text.lower() == "s24"
                                                    or item_2.find("speech").text.lower() == "s23"):
                                                    for item_3 in sentence:
                                                        if item_3.tag == "item":
                                                            if (item_3.find("speech").text.lower() == "s1" or item_3.find("speech").text.lower() == "s6"
                                                                or item_3.find("speech").text.lower() == "s13" or item_3.find("speech").text.lower() == "s5"
                                                                or item_3.find("speech").text.lower() == "s11" or item_3.find("speech").text.lower() == "s518"
                                                                or item_3.find("speech").text.lower() == "s22" or item_3.find("speech").text.lower() == "s25"
                                                                or item_3.find("speech").text.lower() == "s28" or item_3.find("speech").text.lower() == "s29"):
                                                                if (item_3.find("relate") is not None and item_3.find("relate").text is not None
                                                                    and item_3.find("relate") is not None and item_3.find("relate").text is not None
                                                                    and item_2.find("number") is not None and item_2.find("number").text is not None
                                                                    and item_3.find("number") is not None and item_3.find("number").trxe is not None
                                                                    and item_2.find("relate") is not None and item_2.find("relate").text):
                                                                    if ((item_3.find("relate").text.lower() == item_2.find(
                                                                            "number").text.lower()) or
                                                                            (item_2.find("relate").text.lower() == item_3.find(
                                                                                "number").text.lower())):
                                                                        new_class_id = item.find(
                                                                            "lemma").text.capitalize().replace('.', "") + item.find(
                                                                            "lemma").text.capitalize().replace('.', "") + item_2.find(
                                                                            "lemma").text.capitalize().replace('.', "") + item_3.find(
                                                                            "lemma").text.capitalize().replace('.', "")

                                                                        objects.add(new_class_id.replace('.', ""))

                                                                        obj_to_del = set()
                                                                        tmp_pos = "object"
                                                                        for obj in current_classes:
                                                                            if (obj.word == item_2.find("lemma").text.capitalize().replace('.', "")
                                                                                    or obj.word == item_3.find(
                                                                                        "lemma").text.capitalize().replace('.', "") or
                                                                                    obj.word == item_2.find(
                                                                                        "lemma").text.capitalize().replace('.', "") + item_3.find(
                                                                                        "lemma").text.capitalize().replace('.', "")):
                                                                                new_word = obj.word.replace('.', "")
                                                                                obj.word = new_word
                                                                                obj_to_del.add(obj)
                                                                        for obj in obj_to_del:
                                                                            tmp_obj = obj

                                                                            tmp_obj.word = obj.replace('.', "")
                                                                            current_classes.discard(tmp_obj)
                                                                        current_classes.add(WordObj(pos=tmp_pos, word=new_class_id.replace('.', "")))
                                                                        linked_noun_found = True
                                                else:
                                                    new_class_id = item.find("lemma").text.capitalize().replace('.', "") + item_2.find(
                                                        "lemma").text.capitalize().replace('.', "")
                                                    # actions.add(new_class_id.replace('.', ""))
                                                    obj_to_del = set()

                                                    tmp_pos = "verb"

                                                    for obj in current_classes:
                                                        if obj.word == item_2.find("lemma").text.capitalize().replace('.', ""):
                                                            obj.word = obj.word.replace('.', "")
                                                            obj_to_del.add(obj)
                                                    for obj in obj_to_del:
                                                        tmp_obj = obj
                                                        tmp_obj.word = obj.word.replace('.', "")
                                                        current_classes.discard(tmp_obj)
                                                    current_classes.add(WordObj(pos=tmp_pos, word=new_class_id.replace('.', "")))
                                                    linked_noun_found = True
                            if not linked_noun_found:
                                if item.find("lemma") is not None and item.find("lemma").text is not None:
                                    class_id = item.find("lemma").text.capitalize()
                                    current_classes.add(WordObj(pos="adverb", word=class_id.replace('.', "")))
                    elif item.find("lemma").text.lower().replace('.', "") in marker_words.marker_words:
                        class_id = item.find("lemma").text.capitalize()
                        current_classes.add(WordObj(pos="marker", word=class_id.replace('.', "")))

                elif (item.find("lemma") is not None and item.find("lemma").text is not None and
                        item.find("lemma").text.lower().replace('.', "") in marker_words.marker_words):
                    class_id = item.find("lemma").text.capitalize()
                    current_classes.add(WordObj(pos="marker", word=class_id.replace('.', "")))
                elif (item.find("word") is not None and item.find("word").text is not None and
                      item.find("word").text.lower().replace('.', "") in marker_words.marker_words):
                    class_id = item.find("word").text.capitalize()
                    current_classes.add(WordObj(pos="marker", word=class_id.replace('.', "")))

        current_classes_dict = {}
        for obj in current_classes:
            pos = obj.pos
            if pos in current_classes_dict:
                current_classes_dict[pos].append(obj.word)
            else:
                current_classes_dict[pos] = [obj.word]
        # print(current_classes_dict)
        entities.append(current_classes_dict)
    result = []
    for sent_list in entities:
        result.append({names_description.any: sent_list})
    print (result)
    return result





def reduce_by_pos(entities_list=None, pos_to_del=None):
    if entities_list is not None and isinstance(pos_to_del, list):
        entities_list_tmp_verbs_del = []
        for sentence_entities in entities_list:
            sentence_entities_tmp = {}
            for entity_type in sentence_entities:
                words = []
                for w_type in sentence_entities[entity_type]:
                    if w_type not in pos_to_del:
                        for word in sentence_entities[entity_type][w_type]:
                            words.append(word)
                if len(words) > 0:
                    sentence_entities_tmp[entity_type] = words
            if len(sentence_entities_tmp) > 0:
                entities_list_tmp_verbs_del.append(sentence_entities_tmp)
        return entities_list_tmp_verbs_del
    return []


def random_reduce_entities_list(entities_list=None):
    if entities_list is not None:
        random.seed()

        modified_entities_list = reduce_by_pos(entities_list=entities_list, pos_to_del=[])

        result_entities_list = [modified_entities_list]

        entities_list_tmp_verbs_del = reduce_by_pos(entities_list=entities_list, pos_to_del=["verb"])

        if len(entities_list_tmp_verbs_del) > 0 and entities_list_tmp_verbs_del not in result_entities_list:
            result_entities_list.append(entities_list_tmp_verbs_del)

        entities_list_tmp_number_del = reduce_by_pos(entities_list=entities_list, pos_to_del=["number"])

        if len(entities_list_tmp_number_del) > 0 and entities_list_tmp_number_del not in result_entities_list:
            result_entities_list.append(entities_list_tmp_number_del)

        entities_list_tmp_marker = reduce_by_pos(entities_list=entities_list, pos_to_del=["marker"])

        if len(entities_list_tmp_marker) > 0 and entities_list_tmp_marker not in result_entities_list:
            result_entities_list.append(entities_list_tmp_marker)

        entities_list_tmp_verbs_marker = reduce_by_pos(entities_list=entities_list, pos_to_del=["marker", "verb"])

        if len(entities_list_tmp_verbs_marker) > 0 and entities_list_tmp_verbs_marker not in result_entities_list:
            result_entities_list.append(entities_list_tmp_verbs_marker)

        entities_list_tmp_verbs_marker_num = reduce_by_pos(entities_list=entities_list, pos_to_del=["marker", "verb", "number"])

        if len(entities_list_tmp_verbs_marker_num) > 0 and entities_list_tmp_verbs_marker_num not in result_entities_list:
            result_entities_list.append(entities_list_tmp_verbs_marker_num)

        new_entities_list = []
        for item in entities_list_tmp_verbs_marker_num:

            # print(item)

            actual_words_list = {}
            for w_type in item:
                actual_words_list[w_type] = []
                for i, word_1 in enumerate(item[w_type]):
                    actual_words = []
                    for j, word_2 in enumerate(item[w_type]):
                        if i != j:
                            actual_words.append(word_2)
                    actual_words_list[w_type].append(actual_words)
            new_entities_list.append(actual_words_list)
        #print(new_entities_list)

        reduced_nouns_list = []
        for item in new_entities_list:
            for w_type in item:
                for i, word_1 in enumerate(item[w_type]):
                    reduced_nouns_list.append({w_type: word_1})
        #print(reduced_nouns_list)

        for position in reduced_nouns_list:
            if len(position) > 0 and position not in result_entities_list:
                result_entities_list.append([position])

        entities_list_tmp_obj_del = reduce_by_pos(entities_list=entities_list, pos_to_del=["object", "adjective"])

        if len(entities_list_tmp_obj_del) > 0 and entities_list_tmp_obj_del not in result_entities_list:
            result_entities_list.append(entities_list_tmp_obj_del)

        entities_list_tmp_obj_marker = reduce_by_pos(entities_list=entities_list, pos_to_del=["marker", "object", "adjective"])

        if len(entities_list_tmp_obj_marker) > 0 and entities_list_tmp_obj_marker not in result_entities_list:
            result_entities_list.append(entities_list_tmp_obj_marker)

        '''
        print("entities_list_tmp_verbs_del", entities_list_tmp_verbs_del)
        print("entities_list_tmp_marker", entities_list_tmp_marker)
        print("entities_list_tmp_verbs_marker", entities_list_tmp_verbs_marker)
        print("entities_list_tmp_number_del", entities_list_tmp_number_del)
        print("entities_list_tmp_obj_del", entities_list_tmp_obj_del)
        print("entities_list_tmp_obj_marker", entities_list_tmp_obj_marker)
        print(result_entities_list)
        '''


        new_entities_list = []
        entities_list_tmp = modified_entities_list
        # print("modified_entities_list", modified_entities_list)
        max_len = 0
        for sentence_entities in entities_list_tmp:
            for entity_type in sentence_entities:
                if len(sentence_entities[entity_type]) > max_len:
                    max_len = len(sentence_entities[entity_type])

        while max_len > 1:
            max_len = 0
            new_entities_list = []
            for num, sentence_entities in enumerate(entities_list_tmp):
                new_sentence_entities = {}
                for entity_type in sentence_entities:
                    if len(sentence_entities[entity_type]) > 0:
                        # print(len(sentence_entities[entity_type]))
                        new_sentence_entities[entity_type] = random.sample(modified_entities_list[num][entity_type],
                                                                           len(sentence_entities[entity_type]) - 1)
                        max_len = len(new_sentence_entities[entity_type])
                if max_len > 0:
                    new_entities_list.append(new_sentence_entities)

            entities_list_tmp = new_entities_list
            result_entities_list.append(new_entities_list)
        return result_entities_list

    else:
        return []


def form_set_of_common_queries_with_randomization(entities_list=None, templates=None,
                                                  query_templates_file="query_template.xml",
                                                  ontology_config=None, ontology_config_file="ontologies_list.xml",
                                                  mongo_data_base=None):
    if entities_list is not None:
        if templates is None:
            templates = QueryTemplates().get_instance(config_file=query_templates_file)
        else:
            templates = templates.get_instance(config_file=query_templates_file)

        extended_entities_list = random_reduce_entities_list(entities_list=entities_list)

        list_of_versions = []
        for version in extended_entities_list:
            list_of_sentences = []
            for inp in version:
                for temp in templates.templates:
                    if temp.get("type") == "ready_answer":
                        current_query = form_query(query_template=temp, input_vars=inp)

                        print("inp", inp)
                        ontology = choose_ontology(entities=inp, ontology_config=ontology_config,
                                                   ontology_config_file=ontology_config_file,
                                                   mongo_data_base=mongo_data_base)

                        list_of_sentences.append({"ontology": ontology, "query": current_query})
                list_of_versions.append(list_of_sentences)
        return list_of_versions
    else:
        return []


def form_set_of_special_queries(query_template=None, entities_for_query=None, query_type=None, ontology="ontology"):
    print("burum-burum", entities_for_query, query_type, query_template)

    if entities_for_query is not None and query_template is not None:
        if isinstance(query_template, str):
            current_query = form_query(query_template=query_template, input_vars=entities_for_query)
            return [[{"ontology": ontology, "query": current_query, "query_type": query_type}]]
        elif isinstance(query_template, list) or isinstance(query_template, set):
            result = list()
            for i, type in enumerate(query_type):
                if type.strip().lower() == "predicate_definition":
                    defined_by_predicates = query_template_qualifier_special.keywords["defined_classes"]
                    definition_exist = False
                    for entity in entities_for_query:
                        if entities_for_query[entity].lower().strip() in [pr.lower().strip() for pr in
                                                                          defined_by_predicates]:
                            definition_exist = True
                            break
                else:
                    definition_exist = True
                if definition_exist:
                    for template in query_template:
                        if template["type"].lower().strip() == type.strip().lower():
                            current_query = form_query(query_template=template, input_vars=entities_for_query)
                            print("current_query 11111111111111111", current_query)
                            result.append(
                                [{"ontology": ontology, "query": current_query, "query_type": template["type"],
                                  "entities_for_query": entities_for_query}])
                            break
            return result
        else:
            return [[{"ontology": ontology, "query": "", "query_type": ""}]]
    elif entities_for_query is None and query_template is not None:
        if isinstance(query_template, str):
            current_query = form_query(query_template=query_template, input_vars={})
            return [[{"ontology": ontology, "query": current_query, "query_type": query_type,
                      "entities_for_query": {}}]]
        elif isinstance(query_template, list) or isinstance(query_template, set):
            result = list()
            for i, template in enumerate(query_template):
                current_query = form_query(query_template=template, input_vars={})
                print("current_query 11111111111111111", current_query)
                result.append([{"ontology": ontology, "query": current_query, "query_type": template["type"],
                                "entities_for_query": {}}])
            return result
        else:
            return [[{"ontology": ontology, "query": "", "query_type": ""}]]



def choose_ontology(entities=None, ontology_config=None, ontology_config_file="ontologies_list.xml",
                    mongo_data_base=None):
    if entities is not None and isinstance(entities, dict):
        if ontology_config is None:
            ontology_config = Ontologies().get_instance(config_file=ontology_config_file, mongo_data_base=mongo_data_base)
        else:
            ontology_config = ontology_config.get_instance(config_file=ontology_config_file, mongo_data_base=mongo_data_base)
        ontologies_rating = {}


        for onto_name in ontology_config.ontology_key_words:
            score = 0
            total_n = 0

            for entity_type in entities:
                for entity in entities.get(entity_type):
                    total_n += 1
                    if entity in ontology_config.ontology_key_words.get(onto_name):
                        score += 1
            if total_n > 0:
                ontologies_rating[onto_name] = float(score) / float(total_n)
            else:
                ontologies_rating[onto_name] = 0
        best_fit = max(ontologies_rating.keys(), key=(lambda k: ontologies_rating.get(k)))
        if ontologies_rating.get(best_fit) < 0.00001:
            return ontology_config.default_ontology
        else:
            return best_fit

    else:
        return ontology_config.default_ontology


async def get_data_from_db(dict_item=None, mongo_data_base=None):
    if dict_item is not None:
        if mongo_data_base is not None:
            document = await mongo_data_base.find_one(dict_item, projection={'_id': False})
            return document
    return {}


def select_query_template(input_text="", templates=None, query_templates_file="query_template.xml", current_keywords=[]):
    if templates is None:
        templates = QueryTemplates().get_instance(config_file=query_templates_file)
    else:
        templates = templates.get_instance(config_file=query_templates_file)
    query_templates = None
    analysis_result = query_template_qualifier_special.fit_input_entities(
        query_template_qualifier_special.choise_query_template(
        input_str=input_text,
        qualifier_config=qualifier_config), current_keywords)
    print(analysis_result)
    query_type = analysis_result.get('query_type')
    input_entities = analysis_result.get('input_entity')
    print("input_entities", input_entities)
    if input_entities is not None:
        if len(input_entities) < 2:
            if isinstance(input_entities, list):
                try:
                    input_entities = {"inputEntity": [i if not isinstance(i, list) else [j for j in i]
                                                      for i in input_entities][0]}
                    print("sddfgdfdfbfv")
                except:
                    input_entities = {"inputEntity": []}
            else:
                input_entities = {"inputEntity": input_entities}

            print(input_entities)
        else:
            input_entities_tmp = dict()
            for i, entity in enumerate(input_entities):
                if isinstance(entity, list):
                    input_entities_tmp["inputEntity_" + str(i+1)] = [j for j in entity if (len(j) > 0)]
                else:
                    if len(entity) > 0:
                        input_entities_tmp["inputEntity_" + str(i + 1)] = entity
            input_entities = input_entities_tmp

    for t in templates.templates:
        print("type", t.get("type"))
        if t.get("type") is not None and t.get("type").strip() in query_type:
            if query_templates is None:
                query_templates = [t]
            elif isinstance(query_templates, list):
                query_templates.append(t)
            if len(query_templates) >= len(query_type):
                break

    return query_templates, query_type, input_entities

def lettres_types_replacer(input_str=""):
    input_str = input_str.lower()
    congratulations_list = ["привітання", "поздоровлення", "що містять привітання", "що містять поздоровлення",
                            "що містять у собі привітання", "що містять у собі поздоровлення", "які містять привітання",
                            "які містять поздоровлення", "що мають привітання", "що мають поздоровлення",
                            "з привітаннями", "з поздоровленнями", "що є привітаннями", "що є поздоровленнями",
                            "які є привітаннями", "які є поздоровленнями", "привітаннями", "поздоровленнями"]
    apology_list = ["вибачення", "що містять вибачення", "які містять вибачення", "що містять у собі вибачення",
                   "які містять у собі вибачення", "що мають вибачення", "з вибаченнями", "що є вибаченнями",
                   "які є вибаченнями", "вибаченнями"]
    narration_list = ["з розповілями", "розповідні листи", "довгі розповідні листи", "розповідями",
                      "довгими розповідями", "довгими", "довгі", "розповідні"]
    invitation_list = ["запрошення", "що містять запрошення", "які містять запрошення", "що містять у собі запрошення",
                       "які містять у собі запрошення", "що мають запрошення", "з запрошеннями", "що є запрошеннями",
                       "які є запрошеннями", "запрошеннями"]
    letter_list = ["рукописні листи", "звичайні листи", "традиційні листи", "листи"]
    telegram_list = ["телеграми", "телеграмами"]
    attachment_list = ["посилки", "посилки з вкладеннями", "посилку", "посилка", "посилками", "вкладеннями"]
    with_poems_list = ["вірші", "поезії", "що містять вірші", "що містять поезії", "що містять у собі вірші",
                       "що містять у собі поезії", "які містять вірші", "які містять поезії", "що мають вірші",
                       "що мають поезії", "з віршами", "з поезіями", "що є віршами", "що є поезіями",
                       "які є віршами", "які є поезіями", "віршами", "поезіями"]
    if input_str in congratulations_list:
        return "congratulation"
    if input_str in apology_list:
        return "apology"
    if input_str in narration_list:
        return "narration"
    if input_str in invitation_list:
        return "invitation"
    if input_str in letter_list:
        return "letter"
    if input_str in telegram_list:
        return "telegram"
    if input_str in attachment_list:
        return "attachment"
    if input_str in with_poems_list:
        return "withPoems"
    if isinstance(input_str, str):
        p = query_template_qualifier_special.morph.parse(input_str)
        for option in p:
            nf = option.normal_form
            if nf in congratulations_list:
                return "congratulation"
            if nf in apology_list:
                return "apology"
            if nf in narration_list:
                return "narration"
            if nf in invitation_list:
                return "invitation"
            if nf in letter_list:
                return "letter"
            if nf in telegram_list:
                return "telegram"
            if nf in attachment_list:
                return "attachment"
            if nf in with_poems_list:
                return "withPoems"
    return input_str


def test_q_funktion():
    return '1'




if __name__ == "__main__":
    start_time = time.time()
    query_templates = QueryTemplates()
    query_templates_1 = query_templates.get_instance(config_file="query_template.xml")
    entities_names_description = InputVarsNames()

    analyzer =AnalyzerAPIWrapper(config=api_config, config_file="api_config.xml")

    marker_words = MarkerWords()

    '''
    db_config = DBConstants().get_instance(config_file="mongo_client_config_ontology.xml")
    db_url = db_config.url_base + '://' + db_config.admin + ':' + db_config.password + '@' + db_config.db_url
    # print(db_url)
    client = motor.motor_asyncio.AsyncIOMotorClient(db_url)
    # print(client)
    db = eval('client.' + db_config.db_name)
    collection = eval('db.' + db_config.collection_name)
    '''
    ontologies = Ontologies()


    print("--- load time %s s ---" % (time.time() - start_time))

    # input_text = "В які дати Олесю Гончару надсилали листи з привітаннями?"
    input_text = "Що включають процеси навчання у фізичній та реабілітаційній медицині?"
    start_time = time.time()
    query_templates, query_type, entities_for_query = select_query_template(input_text=input_text, templates=query_templates)

    print(query_templates)
    print(query_type)
    print(entities_for_query)


    query_set = form_set_of_special_queries(query_template=query_templates, entities_for_query=entities_for_query)
    print(query_set)
    print("query formation %s s" % (time.time() - start_time))




