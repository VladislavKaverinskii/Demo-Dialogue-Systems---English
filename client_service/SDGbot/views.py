# -*- coding: utf-8 -*-

from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.template.response import SimpleTemplateResponse
from django.views.generic import View
from django.forms import Form
from rest_framework import status
from django.db.models import Q
import json

import datetime
import xml.etree.ElementTree as Et
import string
import random
import json
import traceback
import time
from datetime import datetime, timedelta, timezone
from threading import Thread

import requests
import asyncio
import motor.motor_asyncio
import hashlib

# import text_analysis_handlers
# from foreign_libraries import morph

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

from .models import *

import locale
try:
    locale.setlocale(locale.LC_ALL, 'uk_UA')
except:
    pass

porter = PorterStemmer()



class ChatbotConstants:
    __instance = None

    def __init__(self):
        if not ChatbotConstants.__instance:
            self.name = ""
            self.sparql_converter_url = ""
            self.sparql_converter_url_letters = ""
            self.sparql_converter_ep_url = ""
            self.sparql_converter_aliev_url = ""
            self.ontology_agent_url = ""
            self.conversation_limitation = 1000
            self.garbage_deleting = 100
            self.wait_time = 20.0
            self.sparql_converter_password = ""
            self.ontology_agent_password = ""
            self.sparql_converter_name = ""
            self.ontology_agent_name = ""
            self.answer_comments = {}
            self.greeting_phrases = {}
            self.greeting_phrases_aliyev = {}
            self.standard_answers = {}
            self.standard_answers_aliyev = {}
            self.explanations = {}
            self.dialog_answers = {}
            self.goodbye_phrases = []
            self.db_clean_time = 1000000.0
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="chatbot_config.xml"):
        if not cls.__instance:
            cls.__instance = ChatbotConstants()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                xml_file_data = xml_file.read()
                tree = Et.ElementTree(Et.fromstring(xml_file_data.encode('utf-8').decode('utf-8')))

            root = tree.getroot()
            for i in root:
                if i.tag == "name":
                    cls.__instance.name = i.text.strip()
                elif i.tag == "sparql_converter_url":
                    cls.__instance.sparql_converter_url = i.text.strip()
                elif i.tag == "sparql_converter_ep_url":
                    cls.__instance.sparql_converter_ep_url = i.text.strip()
                elif i.tag == "sparql_converter_aliev_url":
                    cls.__instance.sparql_converter_aliev_url = i.text.strip()
                elif i.tag == "sparql_converter_url_letters":
                    cls.__instance.sparql_converter_url_letters = i.text.strip()
                elif i.tag == "ontology_agent_url":
                    cls.__instance.ontology_agent_url = i.text.strip()
                elif i.tag == "conversation_limitation":
                    cls.__instance.conversation_limitation = int(i.text.strip())
                elif i.tag == "garbage_deleting":
                    cls.__instance.garbage_deleting = int(i.text.strip())
                elif i.tag == "wait_time":
                    cls.__instance.wait_time = float(i.text.strip())
                elif i.tag == "sparql_converter_password":
                    cls.__instance.sparql_converter_password = i.text.strip()
                elif i.tag == "ontology_agent_password":
                    cls.__instance.ontology_agent_password = i.text.strip()
                elif i.tag == "sparql_converter_name":
                    cls.__instance.sparql_converter_name = i.text.strip()
                elif i.tag == "ontology_agent_name":
                    cls.__instance.ontology_agent_name = i.text.strip()
                elif i.tag == "answers_comments":
                    for comment_type in i:
                        cls.__instance.answer_comments[comment_type.tag] = comment_type.text.strip()
                elif i.tag == "greeting_phrases":
                    for phrase in i:
                        cls.__instance.greeting_phrases[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "greeting_phrases_aliyev":
                    for phrase in i:
                        cls.__instance.greeting_phrases_aliyev[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "standard_answers":
                    for phrase in i:
                        cls.__instance.standard_answers[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "standard_answers_aliyev":
                    for phrase in i:
                        cls.__instance.standard_answers_aliyev[phrase.find("case").text.strip()] = phrase.find(
                            "text").text.strip()
                elif i.tag == "explanations":
                    for phrase in i:
                        cls.__instance.explanations[phrase.find("case").text.strip()] = phrase.find("text").text.strip()
                elif i.tag == "dialog_answers":
                    for phrase in i:
                        new_answer = {
                                      "answer": phrase.find("answer").text.strip(),
                                      "markers": [marker.text.strip().lower() for marker in phrase.find("markers")
                                                  if phrase.find("markers")]
                                    }
                        if phrase.find("answer_aliyev") is not None:
                            if phrase.find("answer_aliyev").text is not None:
                                new_answer["answer_aliyev"] = phrase.find("answer_aliyev").text
                        cls.__instance.dialog_answers[phrase.find("type").text.strip()] = new_answer
                elif i.tag == "goodbye_phrases":
                    for phrase in i:
                        cls.__instance.goodbye_phrases.append(phrase.text.strip().lower())
                elif i.tag == "db_clean_time":
                    cls.__instance.db_clean_time = float(i.text.strip())
        return cls.__instance


chatbot_config = ChatbotConstants().get_instance(config_file="chatbot_config.xml")

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
            print("Instance already created:", self.getInstance())

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


# chatbot_config = ChatbotConstants().get_instance(config_file="chatbot_config.xml")
# mongo_config = DBConstants().get_instance(config_file="mongo_client_config.xml")
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

j_text = open('links_dict.json', encoding='utf-8').read()
links_dict = json.loads(j_text, strict=False)

j_text_2 = open('links_dict_ep.json', encoding='utf-8').read()
links_dict_ep = json.loads(j_text_2, strict=False)

j_text_3 = open('links_dict_aliyev.json', encoding='utf-8').read()
links_dict_aliyev = json.loads(j_text_3, strict=False)


def start_form(request):
    convresation_id = request.session.get("convresation_id")
    if convresation_id is not None:
        return redirect('../process_question/')
    return redirect("../")



class GetDialogHistory(View):

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            # current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None:
            context = self.__get_diaog_history__(conversation_id=convresation_id)
        else:
            context = []
        return HttpResponse(json.dumps(context), content_type="application/json")

    def post(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        print("convresation_id", convresation_id)
        if convresation_id is not None:
            context = self.__get_diaog_history__(conversation_id=convresation_id)
        else:
            context = []
        return HttpResponse(json.dumps(context), content_type="application/json")




class StartConversation(View):

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            context = {"convresation_id": convresation_id}
            return render(request, template_name="index.html", context=context)
            # return HttpResponse(json.dumps({'convresation_id': convresation_id,
            #                                 "status": True}), content_type="application/json")
        else:
            context = {"convresation_id": None}
            return render(request, template_name="index.html", context=context)



    def post(self, request, *args, **kwargs):
        convresation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
        request.session["convresation_id"] = convresation_id
        try:
            post_body = json.loads(request.body.decode())
            if "is_webhook" not in post_body:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif post_body.get("is_webhook") is not None and not post_body.get("is_webhook"):
                request.session.set_expiry(chatbot_config.conversation_limitation)
        except Exception as e:
            request.session.set_expiry(chatbot_config.conversation_limitation)
            print(e)

        sparql_converter_message = {
            "performative": "subscribe",
            "password": chatbot_config.sparql_converter_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.sparql_converter_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c", content=convresation_id,
                                        receivers=json.dumps([chatbot_config.sparql_converter_name],
                                                             ensure_ascii=False),
                                        query_sqrvice_id=None, ontology_sqrvice_id=None).save()

        ontology_agent_message = {
            "performative": "subscribe",
            "password": chatbot_config.ontology_agent_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.ontology_agent_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id,
                                        receivers=json.dumps([chatbot_config.ontology_agent_name], ensure_ascii=False),
                                        type="r_c", content=convresation_id, query_sqrvice_id=None,
                                        ontology_sqrvice_id=None).save()
        try:
            print(chatbot_config.sparql_converter_url)
            sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_url,
                                                      json=sparql_converter_message)
            print(sparql_converter_response.text)
            sparql_converter_result = sparql_converter_response.json().get("content")
            ontolgy_agent_response = requests.post(url=chatbot_config.ontology_agent_url, json=ontology_agent_message)
            ontolgy_agent_result = ontolgy_agent_response.json().get("content")

            if sparql_converter_result == "registed" and ontolgy_agent_result == "registed":
                print("Agents registed!")
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                content=ontolgy_agent_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()
                context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question"),
                           'convresation_id': convresation_id,
                           "status": True
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=sparql_converter_response.json().get("content"),
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=ontolgy_agent_response.json().get("content"),
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                context = {"explanation": chatbot_config.explanations["refuse"],
                           'convresation_id': convresation_id,
                           "status": False
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            context = {"explanation": chatbot_config.explanations["error"],
                       'convresation_id': convresation_id,
                       "status": False
                       }

            return HttpResponse(json.dumps(context), content_type="application/json")


class StartConversationEP(View):

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            context = {"convresation_id": convresation_id}
            return render(request, template_name="index_2.html", context=context)
            # return HttpResponse(json.dumps({'convresation_id': convresation_id,
            #                                 "status": True}), content_type="application/json")
        else:
            context = {"convresation_id": None}
            return render(request, template_name="index_2.html", context=context)



    def post(self, request, *args, **kwargs):
        convresation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
        request.session["convresation_id"] = convresation_id
        try:
            post_body = json.loads(request.body.decode())
            if "is_webhook" not in post_body:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif post_body.get("is_webhook") is not None and not post_body.get("is_webhook"):
                request.session.set_expiry(chatbot_config.conversation_limitation)
        except Exception as e:
            request.session.set_expiry(chatbot_config.conversation_limitation)
            print(e)

        sparql_converter_message = {
            "performative": "subscribe",
            "password": chatbot_config.sparql_converter_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.sparql_converter_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c", content=convresation_id,
                                        receivers=json.dumps([chatbot_config.sparql_converter_name],
                                                             ensure_ascii=False),
                                        query_sqrvice_id=None, ontology_sqrvice_id=None).save()

        ontology_agent_message = {
            "performative": "subscribe",
            "password": chatbot_config.ontology_agent_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.ontology_agent_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id,
                                        receivers=json.dumps([chatbot_config.ontology_agent_name], ensure_ascii=False),
                                        type="r_c", content=convresation_id, query_sqrvice_id=None,
                                        ontology_sqrvice_id=None).save()
        try:
            print(chatbot_config.sparql_converter_ep_url)
            sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_ep_url,
                                                      json=sparql_converter_message)
            print(sparql_converter_response.text)
            sparql_converter_result = sparql_converter_response.json().get("content")
            ontolgy_agent_response = requests.post(url=chatbot_config.ontology_agent_url, json=ontology_agent_message)
            ontolgy_agent_result = ontolgy_agent_response.json().get("content")

            if sparql_converter_result == "registed" and ontolgy_agent_result == "registed":
                print("Agents registed!")
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                content=ontolgy_agent_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()
                context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question"),
                           'convresation_id': convresation_id,
                           "status": True
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=sparql_converter_response.json().get("content"),
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=ontolgy_agent_response.json().get("content"),
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                context = {"explanation": chatbot_config.explanations["refuse"],
                           'convresation_id': convresation_id,
                           "status": False
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            context = {"explanation": chatbot_config.explanations["error"],
                       'convresation_id': convresation_id,
                       "status": False
                       }

            return HttpResponse(json.dumps(context), content_type="application/json")



class StartConversationAliyev(View):

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            context = {"convresation_id": convresation_id}
            return render(request, template_name="index_3.html", context=context)
            # return HttpResponse(json.dumps({'convresation_id': convresation_id,
            #                                 "status": True}), content_type="application/json")
        else:
            context = {"convresation_id": None}
            return render(request, template_name="index_3.html", context=context)



    def post(self, request, *args, **kwargs):
        convresation_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=100))
        request.session["convresation_id"] = convresation_id
        try:
            post_body = json.loads(request.body.decode())
            if "is_webhook" not in post_body:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            elif post_body.get("is_webhook") is not None and not post_body.get("is_webhook"):
                request.session.set_expiry(chatbot_config.conversation_limitation)
        except Exception as e:
            request.session.set_expiry(chatbot_config.conversation_limitation)
            print(e)

        sparql_converter_message = {
            "performative": "subscribe",
            "password": chatbot_config.sparql_converter_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.sparql_converter_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c", content=convresation_id,
                                        receivers=json.dumps([chatbot_config.sparql_converter_name],
                                                             ensure_ascii=False),
                                        query_sqrvice_id=None, ontology_sqrvice_id=None).save()

        ontology_agent_message = {
            "performative": "subscribe",
            "password": chatbot_config.ontology_agent_password,
            "sender": chatbot_config.name,
            "receivers": [chatbot_config.ontology_agent_name],
            "reply-to": "",
            "content": convresation_id,
            "language": "text",
            "protocol": "fipa-request protocol",
            "reply-with": convresation_id,
            "conversationID": convresation_id,
            "enconding": "utf-8",
            "ontology": "",
            "in-reply-to": "",
            "reply-by": ""
        }
        CommunicationAct.objects.create(conversation_id=convresation_id,
                                        receivers=json.dumps([chatbot_config.ontology_agent_name], ensure_ascii=False),
                                        type="r_c", content=convresation_id, query_sqrvice_id=None,
                                        ontology_sqrvice_id=None).save()
        try:
            print(chatbot_config.sparql_converter_aliev_url)
            sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_aliev_url,
                                                      json=sparql_converter_message)
            print(sparql_converter_response.text)
            sparql_converter_result = sparql_converter_response.json().get("content")
            ontolgy_agent_response = requests.post(url=chatbot_config.ontology_agent_url, json=ontology_agent_message)
            ontolgy_agent_result = ontolgy_agent_response.json().get("content")

            if sparql_converter_result == "registed" and ontolgy_agent_result == "registed":
                print("Agents registed!")
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                content=ontolgy_agent_result, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()
                print(chatbot_config.greeting_phrases_aliyev.get("question"))
                context = {"greeting_phrase": chatbot_config.greeting_phrases_aliyev.get("question"),
                           'convresation_id': convresation_id,
                           "status": True
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
            else:
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=sparql_converter_response.json().get("content"),
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_c_a",
                                                content=ontolgy_agent_response.json().get("content"),
                                                receivers=ontolgy_agent_response.json().get("receivers"),
                                                query_sqrvice_id=None, ontology_sqrvice_id=None).save()
                context = {"explanation": chatbot_config.explanations["refuse"],
                           'convresation_id': convresation_id,
                           "status": False
                           }
                return HttpResponse(json.dumps(context), content_type="application/json")
        except Exception as e:
            print(e)
            print(traceback.format_exc())

            context = {"explanation": chatbot_config.explanations["error"],
                       'convresation_id': convresation_id,
                       "status": False
                       }

            return HttpResponse(json.dumps(context), content_type="application/json")


class GetFinalAnswer(View):

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            # current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context

    def __get_form_answer_context__(self, answer_obj, is_webhook, ontology):
        answers_keys = json.loads(answer_obj.content)
        print("answers_keys", answers_keys)

        answers_by_level = []
        for level in answers_keys:
            answers_by_sent = []
            for link_obj in level:
                answers = []
                for answer_link in link_obj:
                    images = list()
                    links = list()
                    answer_content = answer_link.get("content")
                    if answer_content is None:
                        answer_content = answer_link.get("key").replace("_comma_", ",").replace(
                            "_apostrof_", "`").replace("_squote_", "'").replace("_dquote_", '"').replace(
                            "_dot_", '.').replace("_lquote_", '«').replace("_rquote_", '»').replace(
                            "_colon_", ':').replace("_dash_", '–').replace("_lbraket_", '(').replace(
                            "_rbraket_", ')').replace("_slash_", '/').replace("_rslash_", '\\').replace("__", "-").replace("_", " ")
                    current_name = answer_link.get("name")
                    current_additional = answer_link.get("additional")
                    semantic_type = answer_link.get("semantic_type")
                    entities_for_query_tmp = answer_link.get("entities_for_query")
                    print(111111)
                    is_self_defined = False
                    if current_name.strip().lower() == answer_content.strip().lower():
                        is_self_defined = True
                    print(2222)
                    entities_for_query = dict()
                    for i_en in entities_for_query_tmp:
                        entities_for_query[i_en] = entities_for_query_tmp[i_en].replace(
                            "_comma_", ",").replace("_apostrof_", "`").replace("_squote_", "'").replace(
                            "_dquote_", '"').replace("_dot_", '.').replace("_lquote_", '«').replace(
                            "_rquote_", '»').replace("_colon_", ':').replace("_dash_", '–').replace(
                            "_lbraket_", '(').replace("_rbraket_", ')').replace("_slash_", '/').replace("_rslash_", '\\').replace("__", "-").replace("_", " ")
                        if (entities_for_query_tmp[i_en].replace("_comma_", ",").replace("_apostrof_", "`").replace(
                                "_squote_", "'").replace("_dquote_", '"').replace("_dot_", '.').replace(
                            "_lquote_", '«').replace("_rquote_", '»').replace("_colon_", ':').replace("_dash_", '–').replace(
                            "_lbraket_", '(').replace("_rbraket_", ')').replace("_slash_", '/').replace("_rslash_", '\\').replace("__", "-").replace(
                            "_", " ").strip().lower() == answer_content.strip().lower()):
                            is_self_defined = True
                    if is_self_defined:
                        continue
                    print(33333)
                    used_keyword = list()
                    work_keywords = list()
                    
                    if ontology is None:
                        current_links_dict = links_dict
                    else:
                        current_links_dict = links_dict_ep
                    
                                       
                    normalized_text = " ".join([porter.stem(word)
                                                for word in answer_content.strip().lower().split()])
                    for keyword in current_links_dict:
                        # Строка со словами в начальной форме. Для случаев, если ключ в тексте находится не в начальной форме
                        to_select = False
                        if ((keyword.strip().lower() in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("а") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("б") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("в") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("a") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("b") in answer_content.strip().lower())
                                or (keyword.strip().lower().rstrip("c") in answer_content.strip().lower())
                                or (keyword.strip().lower() in current_name.strip().lower())):
                            to_select = True
                        else:
                            if ((keyword.strip().lower() in normalized_text)
                            or (keyword.strip().lower().rstrip("а") in normalized_text)
                            or (keyword.strip().lower().rstrip("б") in normalized_text)
                            or (keyword.strip().lower().rstrip("в") in normalized_text)
                            or (keyword.strip().lower().rstrip("a") in normalized_text)
                            or (keyword.strip().lower().rstrip("b") in normalized_text)
                            or (keyword.strip().lower().rstrip("c") in normalized_text)):
                                to_select = True
                        if to_select:
                            # Отсеивание частичных совпадений
                            key_found = True
                            for keyword_2 in current_links_dict:
                                if (keyword in keyword_2 and (len(keyword) < len(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                        "В").rstrip("A").rstrip("B").rstrip("C"))) and
                                        ((answer_content.strip().lower().count(keyword) ==
                                         answer_content.strip().lower().count(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                        "В").rstrip("A").rstrip("B").rstrip("C"))) or
                                         (normalized_text.count(keyword) ==
                                          normalized_text.count(keyword_2.rstrip("А").rstrip("Б").rstrip(
                                              "В").rstrip("A").rstrip("B").rstrip("C"))))):
                                    # print(keyword, keyword_2)
                                    key_found = False
                                    break
                            if key_found:
                                work_keywords.append(keyword)

                    for keyword in work_keywords:
                        print(len(current_links_dict[keyword]))
                        if len(current_links_dict[keyword]) == 1:  # Если ключ однозначный (проверка вхождения в класс не требуется)
                            current_content = current_links_dict[keyword][0]
                            # print("current_content", current_content)
                            # print(len(current_content) > 1 and current_content[1].strip().lower() not in used_keyword)
                            # print(used_keyword)
                            if len(current_content) > 1 and current_content[1].strip().lower() not in used_keyword:
                                used_keyword.append(keyword.strip().lower())
                                alter_conternt = current_links_dict.get(current_content[1])
                                # print("current_content[1]", current_content[1])
                                if alter_conternt is None:
                                    used_keyword.append(keyword.strip().lower())
                                    if is_webhook:
                                        link_exists = False
                                        for link in links:
                                            if link["link"].strip() == current_content[0].strip():
                                                link_exists = True
                                                break
                                        if not link_exists:
                                            links.append({
                                                    "title": current_content[1],
                                                    "link": current_content[0]
                                                })
                                    else:
                                        answer_content += "<br /><br /><a target='_blank' href='" + current_content[
                                            0] + "' >"
                                        answer_content += current_content[1] + "</a>"
                                else:
                                    # print("alter_conternt", alter_conternt)
                                    if len(alter_conternt) == 1:
                                        if is_webhook:
                                            if (current_content[0].split('.')[-1] == "jpg" or
                                                    current_content[0].split('.')[-1] == "png" or
                                                    current_content[0].split('.')[-1] == "bmp"):
                                                image_exists = False
                                                for img in images:
                                                    if img["link"] == current_content[0]:
                                                        image_exists = True
                                                        break
                                                if not image_exists:
                                                    images.append({
                                                        "title": current_content[1],
                                                        "link": current_content[0]
                                                    })
                                            else:
                                                link_exists = False
                                                for link in links:
                                                    if link["link"].strip() == current_content[0].strip():
                                                        link_exists = True
                                                        break
                                                if not link_exists:
                                                    links.append({
                                                        "title": alter_conternt[0][1],
                                                        "link": current_content[0]
                                                    })

                                        else:
                                            answer_content += "<br /><br />" + current_content[1] + " - " + alter_conternt[0][1] + ":<br />"
                                            answer_content += "<a target='_blank' href='" + current_content[0] + "' >"
                                            if current_content[0].split('.')[-1] == "jpg" or current_content[0].split('.')[-1] == "png" or current_content[0].split('.')[-1] == "bmp":
                                                answer_content += "<img src='" + current_content[0] + "' title='" + current_content[1] + "' /></a>"
                                            else:
                                                answer_content += current_content[1] + "</a>"
                            elif len(current_links_dict[keyword]) == 1 and keyword not in used_keyword:
                                used_keyword.append(keyword.strip().lower())
                                if is_webhook:
                                    link_exists = False
                                    for link in links:
                                        if link["link"].strip() == current_content[0].strip():
                                            link_exists = True
                                            break
                                    if not link_exists:
                                        links.append({
                                            "title": "Details: ",
                                            "link": current_content[0]
                                        })
                                else:
                                    answer_content += "<br /><br /><a target='_blank' href='" + current_content[0] + "' >"
                                    answer_content += "Details</a>"
                        elif len(current_links_dict[keyword]) > 1:  # Имеется несколько значений для ключа
                            current_content = []
                            for option in current_links_dict[keyword]:
                                print(option)
                                option_fit = False
                                if len(option) > 2:
                                    for entity in entities_for_query_tmp:
                                        print("entity", entities_for_query_tmp[entity].lower().strip())
                                        if entities_for_query_tmp[entity].lower().strip() == option[2].lower().strip():
                                            current_content = option
                                            option_fit = True
                                            break
                                print("current_content 2", current_content)
                                if option_fit and len(current_content) > 1 and current_content[1].strip().lower() not in used_keyword:
                                    used_keyword.append(keyword.strip().lower())
                                    alter_conternt = current_links_dict.get(current_content[1])
                                    # print("current_content[1]", current_content[1])
                                    if alter_conternt is None:
                                        used_keyword.append(keyword.strip().lower())
                                        if is_webhook:
                                            link_exists = False
                                            for link in links:
                                                if link["link"].strip() == current_content[0].strip():
                                                    link_exists = True
                                                    break
                                            if not link_exists:
                                                links.append({
                                                    "title": current_content[1],
                                                    "link": current_content[0]
                                                })
                                        else:
                                            answer_content += "<br /><br /><a target='_blank' href='" + current_content[
                                                0] + "' >"
                                            answer_content += current_content[1] + "</a>"
                                    else:
                                        # print("alter_conternt", alter_conternt)
                                        if len(alter_conternt) == 1:
                                            if is_webhook:
                                                if current_content[0].split('.')[-1] == "jpg" or \
                                                        current_content[0].split('.')[-1] == "png" or \
                                                        current_content[0].split('.')[-1] == "bmp":
                                                    image_exists = False
                                                    for img in images:
                                                        if img["link"] == current_content[0]:
                                                            image_exists = True
                                                            break
                                                    if not image_exists:
                                                        images.append({
                                                            "title": current_content[1],
                                                            "link": current_content[0]
                                                        })
                                                else:
                                                    link_exists = False
                                                    for link in links:
                                                        if link["link"].strip() == current_content[0].strip():
                                                            link_exists = True
                                                            break
                                                    if not link_exists:
                                                        links.append({
                                                            "title": alter_conternt[0][1],
                                                            "link": current_content[0]
                                                        })

                                            else:
                                                answer_content += "<br /><br />" + current_content[1] + " - " + \
                                                                  alter_conternt[0][1] + ":<br />"
                                                answer_content += "<a target='_blank' href='" + current_content[0] + "' >"
                                                if current_content[0].split('.')[-1] == "jpg" or \
                                                        current_content[0].split('.')[-1] == "png" or \
                                                        current_content[0].split('.')[-1] == "bmp":
                                                    answer_content += "<img src='" + current_content[0] + "' title='" + \
                                                                      current_content[1] + "' /></a>"
                                                else:
                                                    answer_content += current_content[1] + "</a>"
                                        elif len(alter_conternt) > 1:
                                            alter_conternt_work = []
                                            for alter_option in alter_conternt:
                                                alter_option_fit = False
                                                if len(alter_option) > 2:
                                                    for entity in entities_for_query_tmp:
                                                        print("entity", entities_for_query_tmp[entity].lower().strip())
                                                        if entities_for_query_tmp[entity].lower().strip() == alter_option[
                                                            2].lower().strip():
                                                            alter_conternt_work = option
                                                            alter_option_fit = True
                                                            break
                                                if alter_option_fit and len(alter_conternt_work) > 1:
                                                    if is_webhook:
                                                        if current_content[0].split('.')[-1] == "jpg" or \
                                                                current_content[0].split('.')[-1] == "png" or \
                                                                current_content[0].split('.')[-1] == "bmp":
                                                            image_exists = False
                                                            for img in images:
                                                                if img["link"] == current_content[0]:
                                                                    image_exists = True
                                                                    break
                                                            if not image_exists:
                                                                images.append({
                                                                    "title": current_content[1],
                                                                    "link": current_content[0]
                                                                })
                                                        else:
                                                            link_exists = False
                                                            for link in links:
                                                                if link["link"].strip() == current_content[0].strip():
                                                                    link_exists = True
                                                                    break
                                                            if not link_exists:
                                                                links.append({
                                                                    "title": alter_conternt_work[1],
                                                                    "link": current_content[0]
                                                                })

                                                    else:
                                                        answer_content += "<br /><br />" + current_content[1] + " - " + \
                                                                          alter_conternt_work[1] + ":<br />"
                                                        answer_content += "<a target='_blank' href='" + current_content[
                                                            0] + "' >"
                                                        if current_content[0].split('.')[-1] == "jpg" or \
                                                                current_content[0].split('.')[-1] == "png" or \
                                                                current_content[0].split('.')[-1] == "bmp":
                                                            answer_content += "<img src='" + current_content[
                                                                0] + "' title='" + \
                                                                              current_content[1] + "' /></a>"
                                                        else:
                                                            answer_content += current_content[1] + "</a>"
                    if isinstance(current_name, str):
                        name_for_response = current_name.replace(
                            "_comma_", ",").replace("_apostrof_", "`").replace("_squote_", "'").replace(
                            "_dquote_", '"').replace("_dot_", '.').replace("_lquote_", '«').replace(
                            "_rquote_", '»').replace("_colon_", ':').replace("_dash_", '–').replace(
                            "_lbraket_", '(').replace("_rbraket_", ')').replace("_slash_", '/').replace("_rslash_", '\\').replace(
                            "__", "-").replace("_", " ")
                    else:
                        name_for_response = ""
                    if is_webhook:
                        answer = {"name": name_for_response, "content": answer_content, "semantic_type": semantic_type,
                                  "entities_for_query": entities_for_query, "additional": current_additional,
                                  "links": links, "images": images}
                    else:
                        answer = {"name": name_for_response, "content": answer_content, "semantic_type": semantic_type,
                                  "entities_for_query": entities_for_query, "additional": current_additional}
                    answers.append(answer)
                    print(444444)

                print("answers", answers)
                answers_by_sent.append(answers)
            answers_by_level.append(answers_by_sent)

        primary_answers = []
        additional_answers = []

        '''
        for level_num, level in enumerate(answers_by_level):
            if level_num == 0:
                for st in level:
                    for j in st:
                        primary_answers.append(j)
            else:
                for i in level:
                    additional_answers.append(i)
        '''
        for level_num, level in enumerate(answers_by_level):
            if level_num == 0:
                primary_answers, additional_answers = self.form_answers_set(level=level,
                                                                            comment_level="sure_answer")
            elif level_num < 3:
                if len(primary_answers) < 1:
                    primary_answers, additional_answers = self.form_answers_set(level=level,

                                                                                comment_level="unsure")
                else:
                    new_additional_answers_1, new_additional_answers_2 = \
                        self.form_answers_set(level=level, comment_level="unsure")
                    additional_answers += new_additional_answers_1 + new_additional_answers_2
            elif level_num < 5:
                if len(primary_answers) < 1:
                    primary_answers, additional_answers = self.form_answers_set(level=level,

                                                                                comment_level="probably")
                else:
                    new_additional_answers_1, new_additional_answers_2 =\
                        self.form_answers_set(level=level,  comment_level="probably")
                    additional_answers += new_additional_answers_1 + new_additional_answers_2
            else:
                if len(primary_answers) < 1:
                    primary_answers, additional_answers = self.form_answers_set(level=level,

                                                                                comment_level="related_info")
                else:
                    new_additional_answers_1, new_additional_answers_2 =\
                        self.form_answers_set(level=level, comment_level="related_info")
                    additional_answers += new_additional_answers_1 + new_additional_answers_2

        context = dict()
        context["primary_answers"] = primary_answers
        for ans in additional_answers:
            if "metrica" not in ans:
                ans["metrica"] = 0.0
        if len(additional_answers) > 10:
            sorted_additional = sorted(additional_answers, key=lambda answ: answ.get("metrica"), reverse=True)
            context["additional_answers"] = sorted_additional[:5]
            context["additional_answers"] += random.sample(sorted_additional[5:], 5)
        else:
            context["additional_answers"] = additional_answers
        context["additional_info_message"] = chatbot_config.answer_comments["additional_info"]
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
        print(context)
        return context, True


    def form_answers_set(self, level=None, comment_level="sure_answer"):
        main_answers_set = []
        additional_answers_set = []
        print("level ", level)
        if level is not None and len(level) > 0:
            for sent_answer in level:
                if len(sent_answer) == 1:
                    comment = chatbot_config.answer_comments.get(comment_level)
                    if comment is not None:
                        sent_answer[0]["comment"] = chatbot_config.answer_comments.get(comment_level)
                    else:
                        sent_answer[0]["comment"] = ""
                    main_answers_set.append(sent_answer[0])
                else:
                    comment = chatbot_config.answer_comments.get(comment_level)
                    for answer in sent_answer:
                        answer["comment"] = comment
                        main_answers_set.append(answer)

                    '''
                    comment = chatbot_config.answer_comments.get("broad_question")
                    if len(level) < 2:
                        try:
                            if len(sent_answer) > 0:
                                min_len_answer = min(len(item.get("name").split()) for item in sent_answer
                                                     if "name" in item)
                            else:
                                min_len_answer = 0
                        except Exception as e:
                            print(e)
                            print(traceback.format_exc())
                            min_len_answer = 0

                        for answer in sent_answer:

                            metrica = 0.0
                            answer["metrica"] = metrica
                            print(metrica)

                        if len(sent_answer) > 0:
                            max_metrica = max(answer.get("metrica") for answer in sent_answer if "metrica" in answer)
                        else:
                            max_metrica = 0.0

                        for answer in sent_answer:
                            if answer.get("metrica") >= (max_metrica - (abs(max_metrica) / 1000.0)):
                                answer["comment"] = comment
                                main_answers_set.append(answer)
                            else:
                                answer["comment"] = comment
                                additional_answers_set.append(answer)

                        if len(main_answers_set) > 1:
                            main_answers_set_tmp = []
                            for answer in main_answers_set:
                                if len(answer.get("name").split()) <= min_len_answer:
                                    answer["comment"] = comment
                                    main_answers_set_tmp.append(answer)
                                else:
                                    answer["comment"] = comment
                                    additional_answers_set.append(answer)
                            if len(main_answers_set_tmp) > 0:
                                main_answers_set = main_answers_set_tmp
                        if len(main_answers_set) > 1:
                            main_ansver = random.choice(main_answers_set)
                            tmp_answers = [answer for answer in main_answers_set if answer != main_ansver]
                            main_answers_set = [main_ansver]
                            additional_answers_set += tmp_answers
                    else:
                        if len(sent_answer) > 0:
                            try:
                                max_len_ansver = max(len(item.get("name").split()) for item in sent_answer
                                                     if "name" in item)
                            except Exception as e:
                                print(e)
                                print(traceback.format_exc())
                                max_len_ansver = 0
                            for answer in sent_answer:
                                if len(answer.get("name").split()) >= max_len_ansver:
                                    answer["comment"] = comment
                                    sent_answer[0]["metrica"] = float(len(answer.get("name").split()))/10.0
                                    main_answers_set.append(answer)
                                else:
                                    answer["comment"] = comment
                                    sent_answer[0]["metrica"] = float(len(answer.get("name").split())) / 100.0
                                    additional_answers_set.append(answer)
                    '''
        for ans in additional_answers_set:
            if "metrica" not in ans:
                ans["metrica"] = 0.0
        return main_answers_set, additional_answers_set



    def post(self, request, *args, **kwargs):
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None and request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)

        form = Form(request.POST or None)
        if not form.is_valid():
            form = Form(json.loads(request.body.decode()) or None)
        # print(form.is_valid())
        if form.is_valid():
            try:
                sparql_converter_result = form.data.get("sparql_converter_result")
                is_too_long = form.data.get("is_too_long")
                # print("is_too_long", is_too_long)
                if isinstance(is_too_long, str):
                    if is_too_long.lower().strip() == "false":
                        is_too_long = False
                    else:
                        is_too_long = True

                ontology = form.data.get("ontology")

                answer_obj = CommunicationAct.objects.filter(conversation_id=convresation_id,
                                type = "q_r",
                                query_sqrvice_id = sparql_converter_result).order_by('date_time').last()

                if answer_obj is None:
                    context = dict()
                    context["tech_response"] = "in_process"
                    context["status"] = True
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)

                if form.data.get("is_webhook") is not None and form.data.get("is_webhook"):
                    is_webhook = True
                else:
                    is_webhook = False
                context, status = self.__get_form_answer_context__(answer_obj, is_webhook, ontology=ontology)

                if (context is not None and len(context) > 0 and "primary_answers" in context
                        and len(context.get("primary_answers")) > 0):
                    if is_too_long:
                        if context.get("primary_answers") is not None and len(context.get("primary_answers")) > 0:
                            if "comment" in context.get("primary_answers")[0]:
                                context["primary_answers"][0][
                                    "comment"] += " Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit. "
                            else:
                                context["primary_answers"][0][
                                    "comment"] = " Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit. "

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # Получение и обработка истории диалога
                    '''
                    all_dialog = UserDialogPosition.objects.filter(conversation_id=convresation_id).order_by('date_time')
                    print("is_too_long", is_too_long)
                    full_context = []
                    for position in all_dialog:
                        if position.type == "answer":
                            current_context = json.loads(position.content)
                            current_context["type"] = "answer"
                        elif position.type == "question":
                            current_context = {"question": position.content, "type": "question"}
                        elif position.type == "additional_answer":
                            current_context = json.loads(position.content)
                            current_context["type"] = "additional_answer"
                        elif position.type == "additional_answer":
                            current_context = json.loads(position.content)
                            current_context["type"] = "additional_answer"
                        else:
                            current_context = {}
                        # current_context['date_time'] = position.date_time
                        full_context.append(current_context)

                    if len(full_context) > 0:
                        full_context[-1]["local_link"] = "last_message"
                    '''

                    print("is_too_long", is_too_long)
                    if status and len(context) > 0 and "primary_answers" in context and len(context.get(
                            "primary_answers")) > 0:
                        # context = dict()
                        # context["history"] = full_context - исключили истрию диалогоа из ответа API в данном случае
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
                        print("is_too_long", is_too_long)
                        if is_too_long:
                            if "primary_answers" in context:
                                if len(context.get("primary_answers")) > 0 and "comment" in context.get("primary_answers")[0]:
                                    context["primary_answers"][0][
                                        "comment"] += " Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit.  "
                                else:
                                    context["primary_answers"][0][
                                        "comment"] = " Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit.  "
                            elif context.get("primary_answers") is not None and len(context.get("primary_answers")) > 0:
                                context["primary_answers"] = [{
                                                                  "comment": "Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit. "}]
                        if request.COOKIES.get("is_webhook") is None:
                            request.session.set_expiry(chatbot_config.conversation_limitation)
                        context["status"] = True
                        return HttpResponse(json.dumps(context), content_type="application/json")
                    else:
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                        context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                                       "content": "", "comment": ""}]

                        if is_too_long:
                            if "comment" in context.get("primary_answers")[0]:
                                context["primary_answers"][0][
                                    "comment"] = " Your question is too long. The system is designed to answer simple, clear questions. The question should not exceed 120 characters. Your text has been reduced to the specified limit. "

                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                        # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                        if request.COOKIES.get("is_webhook") is None:
                            request.session.set_expiry(chatbot_config.conversation_limitation)
                        context["status"] = True
                        return HttpResponse(json.dumps(context), content_type="application/json")
                else:
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                                   "content": "", "comment": ""}]
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
                context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                               "content": "", "comment": ""}]
                # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context["status"] = True
                return HttpResponse(json.dumps(context), content_type="application/json")
        else:
            context = dict()
            context["greeting_phrase"] = chatbot_config.greeting_phrases.get("no_answer")
            context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("no_answer"),
                                           "content": "", "comment": ""}]
            # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")

class ProcessQuestion(View):

    def __get_form_answer_context_letters__(self, answer_obj, question_data):
        try:
            answers_keys = json.loads(answer_obj.content)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
            db_url_answers += mongo_config.password + '@' + mongo_config.db_url

            new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                        io_loop=loop)
            db_answers = eval('new_client_answers.' + mongo_config.db_name)
            new_collection_answers = eval('db_answers.' + mongo_config.collection_name_letters)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            context = dict()
            context["explanation"] = chatbot_config.explanations.get("error")
            return context, False
        print("new_collection_answers", new_collection_answers)
        primary_answers = []
        answers_by_level = []
        answer_phrase = []
        for level in answers_keys:
            answers_by_sent = []
            for link_obj in level:
                answers = []
                for answer_link in link_obj:
                    current_key = answer_link.get("key")
                    current_name = answer_link.get("name")

                    current_additional = answer_link.get("additional")
                    if current_additional is None:
                        current_additional = []
                    try:
                        print(answer_link)
                        if answer_link.get("is_link") or answer_link.get("is_link") is None:
                            data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": current_key},
                                                                            mongo_data_base=new_collection_answers))
                            answer_content = data.get("content").replace("\n", "<br />")
                            answer_content_list = data.get("content").split("\n")
                            if len(answer_content_list) > 0:
                                current_name = answer_content_list[0]
                                if len(answer_content_list) > 1:
                                    current_name += "<br />" + answer_content_list[1]
                            answer = {"name": current_name, "content": answer_content, "key": current_key,
                                      "additional": current_additional, "metrica": 100}
                            primary_answers.append(answer)
                        else:
                            answer_content = current_key
                            if current_name is None or current_name.strip() == "":
                                answer_phrase.append(answer_content)
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())
                        continue

        additional_answers = []

        if len(answer_phrase) > 0:
            answer_phrase = sorted(answer_phrase, key=lambda x: x.split()[-1] if len(x) > 0 else x)
            answer_phrase = ", <br />".join(answer_phrase).strip(", <br />") + ".<br />"
            answer = {"name": answer_phrase, "content": " ", "key": answer_phrase,
                      "additional": [], "metrica": 100}
            primary_answers.append(answer)

        context = dict()
        context["additional_answers"] = additional_answers
        context["primary_answers"] = primary_answers
        context["additional_info_message"] = ""
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
        context["additional_info_message"] = self.clean_question_from_introductory_words(question_data).strip("?").strip("!")
        print(context)
        return context, True

    def __clean_text__(self, question_data):
        question_data_cleaned = question_data.strip().strip(".").strip("!").strip("?").strip("-").strip("_").strip("*")
        question_data_cleaned = question_data_cleaned.strip("(").strip(")").strip("[").strip("]").strip(",").strip("#")
        question_data_cleaned = question_data_cleaned.strip("$").strip("%").strip(":").strip(";").strip("\"").strip("'")
        question_data_cleaned = question_data_cleaned.strip("~").strip("`").strip("+").strip("=").strip("\\").strip("/")
        question_data_cleaned = question_data_cleaned.strip(">").strip("<").strip("^").strip("&").strip("@")
        question_data_cleaned = question_data_cleaned.lower()
        return question_data_cleaned

    def __check_standard_answers__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for case in chatbot_config.dialog_answers:
            for item in chatbot_config.dialog_answers.get(case).get("markers"):
                if item == question_data_cleaned:
                    return chatbot_config.dialog_answers.get(case).get("answer")
        return None

    def __check_goodbye__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for item in chatbot_config.goodbye_phrases:
            if item == question_data_cleaned:
                return True
        return False

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context


    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            answer_obj = CommunicationAct.objects.filter(conversation_id=convresation_id,
                                                         type="q_r").order_by('date_time').last()
            if answer_obj is not None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
                context = dict()
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                context['convresation_id'] = convresation_id
                context["status"] = True
                return HttpResponse(json.dumps(context), content_type="application/json")

            else:
                context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question")}
                context['convresation_id'] = convresation_id,
                context["status"] = True
                request.session.set_expiry(chatbot_config.conversation_limitation)
                return HttpResponse(json.dumps(context), content_type="application/json")

        return redirect("../")

    def post(self, request, *args, **kwargs):
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        print(convresation_id)
        if convresation_id is not None:
            print("is_webhook", request.COOKIES.get("is_webhook"))
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
        else:
            print("convresation_id", convresation_id)
            context = {"convresation_id": convresation_id}
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")

        form = Form(request.POST or None)
        if not form.is_valid():
            form = Form(json.loads(request.body.decode()) or None)
        print(form.is_valid())
        if form.is_valid():
            try:
                if form.data.get("is_additional") is not None and form.data.get("is_additional") == "True":
                    context = self.__render_additional__(form=form, convresation_id=convresation_id)
                    context["status"] = True
                    context['convresation_id'] = convresation_id
                    return HttpResponse(json.dumps(context), content_type="application/json")

                question_data = form.data.get("question")

                question_data_work = question_data
                if question_data is None or not isinstance(question_data, str) or len(question_data.strip()) == 0:
                    context = dict()
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("wrong_input"),
                                                   "content": "", "comment": ""}]
                    context["additional_answers"] = []
                    context["additional_info_message"] = ""
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["status"] = True
                    print("context", context)
                    return HttpResponse(json.dumps(context), content_type="application/json")
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="question",
                                                  content=question_data, additional_info=None).save()
                standard_answer = self.__check_standard_answers__(question_data)
                if standard_answer is None:
                    standard_answer = self.__check_standard_answers__(question_data_work)

                if standard_answer is not None:
                    context = dict()
                    context["primary_answers"] = [
                        {"name": "", "content":standard_answer, "comment": ""}]
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["tech_response"] = "is_standard"
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if self.__check_goodbye__(question_data):
                    return redirect("../ask_unsubscribe/")

                is_too_long = False
                if len(question_data) > 120:
                    is_too_long = True
                    question_data_tmp = question_data.split()
                    new_question_data = ""
                    counter = 0
                    while len(new_question_data) < 120:
                        if counter < len(question_data_tmp):
                            new_question_data += question_data_tmp[counter]
                        else:
                            break

                sparql_converter_messege = {
                    "performative": "inform",
                    "password": chatbot_config.sparql_converter_password,
                    "sender": chatbot_config.name,
                    "receivers": [chatbot_config.sparql_converter_name],
                    "reply-to": "",
                    "content": question_data,
                    "language": "Norw",
                    "protocol": "fipa-request protocol",
                    "reply-with": question_data_work,
                    "conversationID": convresation_id,
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
                }

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q",
                                                receivers=json.dumps([chatbot_config.sparql_converter_name], ensure_ascii=False),
                                                content=question_data, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_url,
                                                          json=sparql_converter_messege)
                sparql_converter_result = sparql_converter_response.json().get("content")
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result,
                                                query_sqrvice_id=sparql_converter_result,
                                                ontology_sqrvice_id=None).save()
                if sparql_converter_result is None or len(sparql_converter_result) < 1:
                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("not_understand")
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("not_understand"),
                                                   "content": "", "comment": ""}]

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("not_understand")
                    context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["status"] = True
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    return HttpResponse(json.dumps(context), content_type="application/json")

                context = dict()
                context["tech_response"] = "set_into_processing"
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context["status"] = True
                context["sparql_converter_result"] = sparql_converter_result
                context["is_too_long"] = is_too_long
                return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context = {"explanation": chatbot_config.explanations.get("error")}
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()
                return render(request, template_name="failure_form.html", context=context)


        context = {"explanation": chatbot_config.explanations.get("validation_failure")}
        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                          content=json.dumps(context, ensure_ascii=False),
                                          additional_info=json.dumps([])).save()
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        return render(request, template_name="failure_form.html", context=context)

    def __render_additional__(self, form=None, convresation_id=""):
        if form.is_valid():
            try:
                question_key = form.data["question"]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
                db_url_answers += mongo_config.password + '@' + mongo_config.db_url

                new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                            io_loop=loop)
                db_answers = eval('new_client_answers.' + mongo_config.db_name)
                new_collection_answers = eval('db_answers.' + mongo_config.collection_name)
                data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": question_key},
                                                                mongo_data_base=new_collection_answers))

                context = dict()
                context["primary_answers"] = [{"name": data.get("name"), "content": data.get("content"),
                                               "key": question_key}]
                context["greeting_phrase"] = "Hello! What are you interested in? "

                UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()

                formated_time_string = form.data.get("time").replace(",", "").replace(
                    " p.m.", "PM").replace(" a.m.", "AM").replace(" р.", "").strip()

                # .replace("вересня", "September").replace(
                #                     "жовтня", "October").replace("листопада", "November").replace("грудня", "December")
                print(formated_time_string)
                print(datetime.now().__format__('%d %B %Y %H:%M'))
                datetime_object = datetime.strptime(formated_time_string, '%d %B %Y %H:%M')

                datetime_object = datetime_object + timedelta(milliseconds=1000)

                t_object = UserDialogPosition.objects.filter(conversation_id=convresation_id, type="additional_answer",
                                                             content=json.dumps(context, ensure_ascii=False))
                if t_object is None:
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([]),
                                                      date_time=datetime_object).save()
                    '''
                    e_object = UserDialogPosition.objects.filter(conversation_id=convresation_id,
                                                                 type="additional_answer",
                                                                 content=json.dumps(context)).order_by('date_time').last()
                    e_object.date_time=datetime_object
                    e_object.save(update_fields=['date_time'])                    
                else:
                    for obj in t_object:
                        obj.date_time=datetime_object
                        obj.save(update_fields=['date_time'])
                '''

                all_dialog = UserDialogPosition.objects.filter(conversation_id=convresation_id)

                for position in all_dialog:
                    if position.type == "answer":
                        current_context = json.loads(position.content)
                        if "additional_answers" in current_context:
                            new_additional_answers = []
                            for a_answ in current_context["additional_answers"]:
                                if "key" in a_answ and a_answ.get("key") != question_key:
                                    new_additional_answers.append(a_answ)
                            current_context["additional_answers"] = new_additional_answers
                        position.content = json.dumps(current_context, ensure_ascii=False)
                        position.save(update_fields=['content'])

                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                return context

            except Exception as e:
                print(e)
                print(traceback.format_exc())

        context = dict()
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("question")
        context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
        return context


class ProcessQuestionEP(View):

    def __get_form_answer_context_letters__(self, answer_obj, question_data):
        try:
            answers_keys = json.loads(answer_obj.content)
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
            db_url_answers += mongo_config.password + '@' + mongo_config.db_url

            new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                        io_loop=loop)
            db_answers = eval('new_client_answers.' + mongo_config.db_name)
            new_collection_answers = eval('db_answers.' + mongo_config.collection_name_letters)
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            context = dict()
            context["explanation"] = chatbot_config.explanations.get("error")
            return context, False
        print("new_collection_answers", new_collection_answers)
        primary_answers = []
        answers_by_level = []
        answer_phrase = []
        for level in answers_keys:
            answers_by_sent = []
            for link_obj in level:
                answers = []
                for answer_link in link_obj:
                    current_key = answer_link.get("key")
                    current_name = answer_link.get("name")

                    current_additional = answer_link.get("additional")
                    if current_additional is None:
                        current_additional = []
                    try:
                        print(answer_link)
                        if answer_link.get("is_link") or answer_link.get("is_link") is None:
                            data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": current_key},
                                                                            mongo_data_base=new_collection_answers))
                            answer_content = data.get("content").replace("\n", "<br />")
                            answer_content_list = data.get("content").split("\n")
                            if len(answer_content_list) > 0:
                                current_name = answer_content_list[0]
                                if len(answer_content_list) > 1:
                                    current_name += "<br />" + answer_content_list[1]
                            answer = {"name": current_name, "content": answer_content, "key": current_key,
                                      "additional": current_additional, "metrica": 100}
                            primary_answers.append(answer)
                        else:
                            answer_content = current_key
                            if current_name is None or current_name.strip() == "":
                                answer_phrase.append(answer_content)
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())
                        continue

        additional_answers = []

        if len(answer_phrase) > 0:
            answer_phrase = sorted(answer_phrase, key=lambda x: x.split()[-1] if len(x) > 0 else x)
            answer_phrase = ", <br />".join(answer_phrase).strip(", <br />") + ".<br />"
            answer = {"name": answer_phrase, "content": " ", "key": answer_phrase,
                      "additional": [], "metrica": 100}
            primary_answers.append(answer)

        context = dict()
        context["additional_answers"] = additional_answers
        context["primary_answers"] = primary_answers
        context["additional_info_message"] = ""
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
        context["additional_info_message"] = self.clean_question_from_introductory_words(question_data).strip("?").strip("!")
        print(context)
        return context, True

    def __clean_text__(self, question_data):
        question_data_cleaned = question_data.strip().strip(".").strip("!").strip("?").strip("-").strip("_").strip("*")
        question_data_cleaned = question_data_cleaned.strip("(").strip(")").strip("[").strip("]").strip(",").strip("#")
        question_data_cleaned = question_data_cleaned.strip("$").strip("%").strip(":").strip(";").strip("\"").strip("'")
        question_data_cleaned = question_data_cleaned.strip("~").strip("`").strip("+").strip("=").strip("\\").strip("/")
        question_data_cleaned = question_data_cleaned.strip(">").strip("<").strip("^").strip("&").strip("@")
        question_data_cleaned = question_data_cleaned.lower()
        return question_data_cleaned

    def __check_standard_answers__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for case in chatbot_config.dialog_answers:
            for item in chatbot_config.dialog_answers.get(case).get("markers"):
                if item == question_data_cleaned:
                    return chatbot_config.dialog_answers.get(case).get("answer")
        return None

    def __check_goodbye__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for item in chatbot_config.goodbye_phrases:
            if item == question_data_cleaned:
                return True
        return False

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context


    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            answer_obj = CommunicationAct.objects.filter(conversation_id=convresation_id,
                                                         type="q_r").order_by('date_time').last()
            if answer_obj is not None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
                context = dict()
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                context['convresation_id'] = convresation_id
                context["status"] = True
                return HttpResponse(json.dumps(context), content_type="application/json")

            else:
                context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question")}
                context['convresation_id'] = convresation_id,
                context["status"] = True
                request.session.set_expiry(chatbot_config.conversation_limitation)
                return HttpResponse(json.dumps(context), content_type="application/json")

        return redirect("../")

    def post(self, request, *args, **kwargs):
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        print(convresation_id)
        if convresation_id is not None:
            print("is_webhook", request.COOKIES.get("is_webhook"))
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
        else:
            print("convresation_id", convresation_id)
            context = {"convresation_id": convresation_id}
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")

        form = Form(request.POST or None)
        if not form.is_valid():
            form = Form(json.loads(request.body.decode()) or None)
        print(form.is_valid())
        if form.is_valid():
            try:
                if form.data.get("is_additional") is not None and form.data.get("is_additional") == "True":
                    context = self.__render_additional__(form=form, convresation_id=convresation_id)
                    context["status"] = True
                    context['convresation_id'] = convresation_id
                    return HttpResponse(json.dumps(context), content_type="application/json")

                question_data = form.data.get("question")

                question_data_work = question_data
                if question_data is None or not isinstance(question_data, str) or len(question_data.strip()) == 0:
                    context = dict()
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("wrong_input"),
                                                   "content": "", "comment": ""}]
                    context["additional_answers"] = []
                    context["additional_info_message"] = ""
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("wrong_input")
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["status"] = True
                    print("context", context)
                    return HttpResponse(json.dumps(context), content_type="application/json")
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="question",
                                                  content=question_data, additional_info=None).save()
                standard_answer = self.__check_standard_answers__(question_data)
                if standard_answer is None:
                    standard_answer = self.__check_standard_answers__(question_data_work)

                if standard_answer is not None:
                    context = dict()
                    context["primary_answers"] = [
                        {"name": "", "content":standard_answer, "comment": ""}]
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["tech_response"] = "is_standard"
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if self.__check_goodbye__(question_data):
                    return redirect("../ask_unsubscribe/")

                is_too_long = False
                if len(question_data) > 120:
                    is_too_long = True
                    question_data_tmp = question_data.split()
                    new_question_data = ""
                    counter = 0
                    while len(new_question_data) < 120:
                        if counter < len(question_data_tmp):
                            new_question_data += question_data_tmp[counter]
                        else:
                            break

                sparql_converter_messege = {
                    "performative": "inform",
                    "password": chatbot_config.sparql_converter_password,
                    "sender": chatbot_config.name,
                    "receivers": [chatbot_config.sparql_converter_name],
                    "reply-to": "",
                    "content": question_data,
                    "language": "Norw",
                    "protocol": "fipa-request protocol",
                    "reply-with": question_data_work,
                    "conversationID": convresation_id,
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
                }

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q",
                                                receivers=json.dumps([chatbot_config.sparql_converter_name], ensure_ascii=False),
                                                content=question_data, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_ep_url,
                                                          json=sparql_converter_messege)
                sparql_converter_result = sparql_converter_response.json().get("content")

                print("sparql_converter_result 111 ", sparql_converter_result)

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result,
                                                query_sqrvice_id=sparql_converter_result,
                                                ontology_sqrvice_id=None).save()
                if sparql_converter_result is None or len(sparql_converter_result) < 1:
                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("not_understand")
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("not_understand"),
                                                   "content": "", "comment": ""}]

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases.get("not_understand")
                    context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["status"] = True
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    return HttpResponse(json.dumps(context), content_type="application/json")

                context = dict()
                context["tech_response"] = "set_into_processing"
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context["status"] = True
                context["sparql_converter_result"] = sparql_converter_result
                context["is_too_long"] = is_too_long
                return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context = {"explanation": chatbot_config.explanations.get("error")}
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()
                return render(request, template_name="failure_form.html", context=context)


        context = {"explanation": chatbot_config.explanations.get("validation_failure")}
        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                          content=json.dumps(context, ensure_ascii=False),
                                          additional_info=json.dumps([])).save()
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        return render(request, template_name="failure_form.html", context=context)

    def __render_additional__(self, form=None, convresation_id=""):
        if form.is_valid():
            try:
                question_key = form.data["question"]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
                db_url_answers += mongo_config.password + '@' + mongo_config.db_url

                new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                            io_loop=loop)
                db_answers = eval('new_client_answers.' + mongo_config.db_name)
                new_collection_answers = eval('db_answers.' + mongo_config.collection_name)
                data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": question_key},
                                                                mongo_data_base=new_collection_answers))

                context = dict()
                context["primary_answers"] = [{"name": data.get("name"), "content": data.get("content"),
                                               "key": question_key}]
                context["greeting_phrase"] = "Hello! What are you interested in? "

                UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()

                formated_time_string = form.data.get("time").replace(",", "").replace(
                    " p.m.", "PM").replace(" a.m.", "AM").replace(" р.", "").strip()

                # .replace("вересня", "September").replace(
                #                     "жовтня", "October").replace("листопада", "November").replace("грудня", "December")
                print(formated_time_string)
                print(datetime.now().__format__('%d %B %Y %H:%M'))
                datetime_object = datetime.strptime(formated_time_string, '%d %B %Y %H:%M')

                datetime_object = datetime_object + timedelta(milliseconds=1000)

                t_object = UserDialogPosition.objects.filter(conversation_id=convresation_id, type="additional_answer",
                                                             content=json.dumps(context, ensure_ascii=False))
                if t_object is None:
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([]),
                                                      date_time=datetime_object).save()
                    '''
                    e_object = UserDialogPosition.objects.filter(conversation_id=convresation_id,
                                                                 type="additional_answer",
                                                                 content=json.dumps(context)).order_by('date_time').last()
                    e_object.date_time=datetime_object
                    e_object.save(update_fields=['date_time'])                    
                else:
                    for obj in t_object:
                        obj.date_time=datetime_object
                        obj.save(update_fields=['date_time'])
                '''

                all_dialog = UserDialogPosition.objects.filter(conversation_id=convresation_id)

                for position in all_dialog:
                    if position.type == "answer":
                        current_context = json.loads(position.content)
                        if "additional_answers" in current_context:
                            new_additional_answers = []
                            for a_answ in current_context["additional_answers"]:
                                if "key" in a_answ and a_answ.get("key") != question_key:
                                    new_additional_answers.append(a_answ)
                            current_context["additional_answers"] = new_additional_answers
                        position.content = json.dumps(current_context, ensure_ascii=False)
                        position.save(update_fields=['content'])

                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases.get("success")
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                return context

            except Exception as e:
                print(e)
                print(traceback.format_exc())

        context = dict()
        context["greeting_phrase"] = chatbot_config.greeting_phrases.get("question")
        context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
        return context


class ProcessQuestionAliyev(View):

    def __clean_text__(self, question_data):
        question_data_cleaned = question_data.strip().strip(".").strip("!").strip("?").strip("-").strip("_").strip("*")
        question_data_cleaned = question_data_cleaned.strip("(").strip(")").strip("[").strip("]").strip(",").strip("#")
        question_data_cleaned = question_data_cleaned.strip("$").strip("%").strip(":").strip(";").strip("\"").strip("'")
        question_data_cleaned = question_data_cleaned.strip("~").strip("`").strip("+").strip("=").strip("\\").strip("/")
        question_data_cleaned = question_data_cleaned.strip(">").strip("<").strip("^").strip("&").strip("@")
        question_data_cleaned = question_data_cleaned.lower()
        return question_data_cleaned

    def __check_standard_answers__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for case in chatbot_config.dialog_answers:
            for item in chatbot_config.dialog_answers.get(case).get("markers"):
                if item == question_data_cleaned:
                    answer = chatbot_config.dialog_answers.get(case).get("answer_aliyev")
                    if isinstance(answer, str) and answer.strip() != "":
                        return answer
                    return chatbot_config.dialog_answers.get(case).get("answer")
        return None

    def __check_goodbye__(self, question_data):
        question_data_cleaned = self.__clean_text__(question_data)
        for item in chatbot_config.goodbye_phrases:
            if item == question_data_cleaned:
                return True
        return False

    def __get_diaog_history__(self, conversation_id=""):
        all_dialog = UserDialogPosition.objects.filter(conversation_id=conversation_id).order_by('date_time')
        full_context = []
        for position in all_dialog:
            current_context = {}
            if position.type == "answer":
                current_context = json.loads(position.content)
                current_context["type"] = "answer"
            elif position.type == "question":
                current_context = {"question": position.content, "type": "question"}
            elif position.type == "additional_answer":
                current_context = json.loads(position.content)
                current_context["type"] = "additional_answer"
            current_context['date_time'] = position.date_time
            full_context.append(current_context)
        if len(full_context) > 0:
            full_context[-1]["local_link"] = "last_message"
        return full_context


    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")

        if convresation_id is not None:
            answer_obj = CommunicationAct.objects.filter(conversation_id=convresation_id,
                                                         type="q_r").order_by('date_time').last()
            if answer_obj is not None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
                context = dict()
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                context['convresation_id'] = convresation_id
                context["status"] = True
                return HttpResponse(json.dumps(context), content_type="application/json")

            else:
                context = {"greeting_phrase": chatbot_config.greeting_phrases.get("question")}
                context['convresation_id'] = convresation_id,
                context["status"] = True
                request.session.set_expiry(chatbot_config.conversation_limitation)
                return HttpResponse(json.dumps(context), content_type="application/json")

        return redirect("../")

    def post(self, request, *args, **kwargs):
        request.session["quertion_processing"] = True
        convresation_id = request.session.get("convresation_id")
        print(convresation_id)
        if convresation_id is not None:
            print("is_webhook", request.COOKIES.get("is_webhook"))
            if request.COOKIES.get("is_webhook") is None:
                request.session.set_expiry(chatbot_config.conversation_limitation)
        else:
            print("convresation_id", convresation_id)
            context = {"convresation_id": convresation_id}
            context["status"] = True
            return HttpResponse(json.dumps(context), content_type="application/json")

        form = Form(request.POST or None)
        if not form.is_valid():
            form = Form(json.loads(request.body.decode()) or None)
        print(form.is_valid())
        if form.is_valid():
            try:
                if form.data.get("is_additional") is not None and form.data.get("is_additional") == "True":
                    context = self.__render_additional__(form=form, convresation_id=convresation_id)
                    context["status"] = True
                    context['convresation_id'] = convresation_id
                    return HttpResponse(json.dumps(context), content_type="application/json")

                question_data = form.data.get("question")

                question_data_work = question_data
                if question_data is None or not isinstance(question_data, str) or len(question_data.strip()) == 0:
                    print("Empty enter!")
                    context = dict()
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers.get("wrong_input"),
                                                   "content": "", "comment": ""}]
                    context["additional_answers"] = []
                    context["additional_info_message"] = ""
                    context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("wrong_input")

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["status"] = True
                    context["tech_response"] = "is_standard"
                    print("context", context)
                    return HttpResponse(json.dumps(context), content_type="application/json")
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="question",
                                                  content=question_data, additional_info=None).save()
                standard_answer = self.__check_standard_answers__(question_data)
                if standard_answer is None:
                    standard_answer = self.__check_standard_answers__(question_data_work)

                if standard_answer is not None:
                    context = dict()
                    context["primary_answers"] = [
                        {"name": "", "content": standard_answer, "comment": ""}]
                    context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("success")

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    # context = dict()
                    # context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    context["tech_response"] = "is_standard"
                    context["status"] = True
                    return HttpResponse(json.dumps(context), content_type="application/json")

                if self.__check_goodbye__(question_data):
                    return redirect("../ask_unsubscribe/")

                is_too_long = False
                if len(question_data) > 120:
                    is_too_long = True
                    question_data_tmp = question_data.split()
                    new_question_data = ""
                    counter = 0
                    while len(new_question_data) < 120:
                        if counter < len(question_data_tmp):
                            new_question_data += question_data_tmp[counter]
                        else:
                            break

                sparql_converter_messege = {
                    "performative": "inform",
                    "password": chatbot_config.sparql_converter_password,
                    "sender": chatbot_config.name,
                    "receivers": [chatbot_config.sparql_converter_name],
                    "reply-to": "",
                    "content": question_data,
                    "language": "Norw",
                    "protocol": "fipa-request protocol",
                    "reply-with": question_data_work,
                    "conversationID": convresation_id,
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
                }

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q",
                                                receivers=json.dumps([chatbot_config.sparql_converter_name],
                                                ensure_ascii=False),
                                                content=question_data, query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()

                sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_aliev_url,
                                                          json=sparql_converter_messege)
                sparql_converter_result = sparql_converter_response.json().get("content")

                print("sparql_converter_result 111 ", sparql_converter_result)

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_m_q_a",
                                                receivers=sparql_converter_response.json().get("receivers"),
                                                content=sparql_converter_result,
                                                query_sqrvice_id=sparql_converter_result,
                                                ontology_sqrvice_id=None).save()
                if sparql_converter_result is None or len(sparql_converter_result) < 1:
                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("not_understand")
                    context["primary_answers"] = [{"name": chatbot_config.standard_answers_aliyev.get("not_understand"),
                                                   "content": "", "comment": ""}]

                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([])).save()

                    context = dict()
                    context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("not_understand")
                    context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                    context["status"] = True
                    if request.COOKIES.get("is_webhook") is None:
                        request.session.set_expiry(chatbot_config.conversation_limitation)
                    return HttpResponse(json.dumps(context), content_type="application/json")

                context = dict()
                context["tech_response"] = "set_into_processing"
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context["status"] = True
                context["sparql_converter_result"] = sparql_converter_result
                context["is_too_long"] = is_too_long
                return HttpResponse(json.dumps(context), content_type="application/json")
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                if request.COOKIES.get("is_webhook") is None:
                    request.session.set_expiry(chatbot_config.conversation_limitation)
                context = {"explanation": chatbot_config.explanations.get("error")}
                UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()
                return render(request, template_name="failure_form.html", context=context)


        context = {"explanation": chatbot_config.explanations.get("validation_failure")}
        UserDialogPosition.objects.create(conversation_id=convresation_id, type="answer",
                                          content=json.dumps(context, ensure_ascii=False),
                                          additional_info=json.dumps([])).save()
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        return render(request, template_name="failure_form.html", context=context)

    def __render_additional__(self, form=None, convresation_id=""):
        if form.is_valid():
            try:
                question_key = form.data["question"]
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                db_url_answers = mongo_config.url_base + '://' + mongo_config.admin + ':'
                db_url_answers += mongo_config.password + '@' + mongo_config.db_url

                new_client_answers = motor.motor_asyncio.AsyncIOMotorClient(db_url_answers,
                                                                            io_loop=loop)
                db_answers = eval('new_client_answers.' + mongo_config.db_name)
                new_collection_answers = eval('db_answers.' + mongo_config.collection_name)
                data = loop.run_until_complete(get_data_from_db(dict_item={"onto_link": question_key},
                                                                mongo_data_base=new_collection_answers))

                context = dict()
                context["primary_answers"] = [{"name": data.get("name"), "content": data.get("content"),
                                               "key": question_key}]
                context["greeting_phrase"] = "Hello! What are you interested in? "

                UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                  content=json.dumps(context, ensure_ascii=False),
                                                  additional_info=json.dumps([])).save()

                formated_time_string = form.data.get("time").replace(",", "").replace(
                    " p.m.", "PM").replace(" a.m.", "AM").replace(" р.", "").strip()

                # .replace("вересня", "September").replace(
                #                     "жовтня", "October").replace("листопада", "November").replace("грудня", "December")
                print(formated_time_string)
                print(datetime.now().__format__('%d %B %Y %H:%M'))
                datetime_object = datetime.strptime(formated_time_string, '%d %B %Y %H:%M')

                datetime_object = datetime_object + timedelta(milliseconds=1000)

                t_object = UserDialogPosition.objects.filter(conversation_id=convresation_id, type="additional_answer",
                                                             content=json.dumps(context, ensure_ascii=False))
                if t_object is None:
                    UserDialogPosition.objects.create(conversation_id=convresation_id, type="additional_answer",
                                                      content=json.dumps(context, ensure_ascii=False),
                                                      additional_info=json.dumps([]),
                                                      date_time=datetime_object).save()
                    '''
                    e_object = UserDialogPosition.objects.filter(conversation_id=convresation_id,
                                                                 type="additional_answer",
                                                                 content=json.dumps(context)).order_by('date_time').last()
                    e_object.date_time=datetime_object
                    e_object.save(update_fields=['date_time'])                    
                else:
                    for obj in t_object:
                        obj.date_time=datetime_object
                        obj.save(update_fields=['date_time'])
                '''

                all_dialog = UserDialogPosition.objects.filter(conversation_id=convresation_id)

                for position in all_dialog:
                    if position.type == "answer":
                        current_context = json.loads(position.content)
                        if "additional_answers" in current_context:
                            new_additional_answers = []
                            for a_answ in current_context["additional_answers"]:
                                if "key" in a_answ and a_answ.get("key") != question_key:
                                    new_additional_answers.append(a_answ)
                            current_context["additional_answers"] = new_additional_answers
                        position.content = json.dumps(current_context, ensure_ascii=False)
                        position.save(update_fields=['content'])

                context = dict()
                context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("success")
                context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
                return context

            except Exception as e:
                print(e)
                print(traceback.format_exc())

        context = dict()
        context["greeting_phrase"] = chatbot_config.greeting_phrases_aliyev.get("question")
        context["history"] = self.__get_diaog_history__(conversation_id=convresation_id)
        return context


class ProcessRequests(View):

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None:
            return redirect('/')
        return redirect("../chatbot/")

    def post(self, request, *args, **kwargs):
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        request.session["quertion_processing"] = True
        request.session["queries_processing"] = True

        try:
            received_json_data = json.loads(request.body.decode("utf-8"))
            query_sqrvice_id = received_json_data['content']
        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return HttpResponse(status=status.HTTP_404_NOT_FOUN)

        current_obj = CommunicationAct.objects.filter(query_sqrvice_id=query_sqrvice_id).order_by('date_time').last()
        counter = 0
        while current_obj is None and counter < 20:
            current_obj = CommunicationAct.objects.filter(query_sqrvice_id=query_sqrvice_id).order_by(
                'date_time').last()
            if current_obj is None:
                time.sleep(0.1)
            else:
                break
            counter += 1

        if current_obj is not None:
            conversation_id = current_obj.conversation_id
            CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r_i",
                                            receivers=json.dumps(received_json_data.get("receivers"),
                                                                 ensure_ascii=False),
                                            content=received_json_data['content'],
                                            query_sqrvice_id=received_json_data['content'],
                                            ontology_sqrvice_id=None).save()
            get_results_message = {
                "performative": "request",
                "password": chatbot_config.sparql_converter_password,
                "sender": chatbot_config.name,
                "receivers": [chatbot_config.sparql_converter_name],
                "reply-to": received_json_data['content'],
                "content": received_json_data['content'],
                "language": "Norw",
                "protocol": "fipa-request protocol",
                "reply-with": received_json_data['content'],
                "conversationID": conversation_id,
                "enconding": "utf-8",
                "ontology": "",
                "in-reply-to": "",
                "reply-by": ""
            }
            CommunicationAct.objects.create(conversation_id=conversation_id, type="r_r_q",
                                            receivers=json.dumps([chatbot_config.sparql_converter_name],
                                                                 ensure_ascii=False),
                                            content=received_json_data['content'],
                                            query_sqrvice_id=received_json_data['content'],
                                            ontology_sqrvice_id=None).save()
            try:
                sparql_converter_response = requests.post(url=chatbot_config.sparql_converter_url,
                                                          json=get_results_message)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                receivers=json.dumps(json.dumps([chatbot_config.name]),
                                                                     ensure_ascii=False),
                                                content=json.dumps([]),
                                                query_sqrvice_id=current_obj.query_sqrvice_id,
                                                ontology_sqrvice_id="0").save()
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)

            try:
                if sparql_converter_response.json().get("performative") == "inform":
                    sparql_converter_result = sparql_converter_response.json().get("content")
                    print("sparql_converter_result", sparql_converter_result)
                    CommunicationAct.objects.create(conversation_id=conversation_id, type="q_s",
                                                    receivers=json.dumps(sparql_converter_response.json().get(
                                                        "receivers"), ensure_ascii=False),
                                                    content=sparql_converter_result,
                                                    query_sqrvice_id=query_sqrvice_id,
                                                    ontology_sqrvice_id=None).save()

                    ontology_agent_message = {
                        "performative": "inform",
                        "password": chatbot_config.ontology_agent_password,
                        "sender": chatbot_config.name,
                        "receivers": [chatbot_config.ontology_agent_name],
                        "reply-to": "",
                        "content": sparql_converter_result,
                        "language": "sparql",
                        "protocol": "fipa-request protocol",
                        "reply-with": sparql_converter_result,
                        "conversationID": conversation_id,
                        "enconding": "utf-8",
                        "ontology": "",
                        "in-reply-to": "",
                        "reply-by": ""
                    }
                    CommunicationAct.objects.create(conversation_id=conversation_id, type="r_q_e",
                                                    receivers=json.dumps([chatbot_config.ontology_agent_name],
                                                                         ensure_ascii=False),
                                                    content=sparql_converter_result,
                                                    query_sqrvice_id=query_sqrvice_id,
                                                    ontology_sqrvice_id=None).save()

                    ontology_agent_response = requests.post(url=chatbot_config.ontology_agent_url,
                                                            json=ontology_agent_message)
                    print("ontology_agent_response", ontology_agent_response.text)
                    if ontology_agent_response.json().get("performative") == "confirm":
                        ontology_sqrvice_id = ontology_agent_response.json().get("content")
                        CommunicationAct.objects.create(conversation_id=conversation_id, type="r_q_e_a",
                                                        receivers=json.dumps(
                                                            ontology_agent_response.json().get("receivers"),
                                                            ensure_ascii=False),
                                                        content=ontology_sqrvice_id,
                                                        query_sqrvice_id=query_sqrvice_id,
                                                        ontology_sqrvice_id=ontology_sqrvice_id).save()

                        return HttpResponse(status=status.HTTP_200_OK)
                    else:
                        return HttpResponse(status=status.HTTP_200_OK)
                else:
                    return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                print("No results")
                CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                receivers=json.dumps(json.dumps([chatbot_config.name]),
                                                                     ensure_ascii=False),
                                                content=json.dumps([]),
                                                query_sqrvice_id=current_obj.query_sqrvice_id,
                                                ontology_sqrvice_id=None).save()
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        else:
            try:
                conversation_id = request.session.get("convresation_id")
                CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                receivers=json.dumps(json.dumps([chatbot_config.name]),
                                                                     ensure_ascii=False),
                                                content=json.dumps([]),
                                                query_sqrvice_id=current_obj.query_sqrvice_id,
                                                ontology_sqrvice_id=None).save()
            except Exception as e:
                print(e)
                print(traceback.format_exc())
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)


class OntainOntologyAnswers(View):

    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is not None:
            return redirect('/')
        return redirect("../chatbot/")

    def post(self, request, *args, **kwargs):
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(chatbot_config.conversation_limitation)
        request.session["quertion_processing"] = True
        request.session["queries_processing"] = True
        try:
            received_json_data = json.loads(request.body.decode("utf-8"))
            ontology_sqrvice_id = received_json_data['content']

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        current_obj = CommunicationAct.objects.filter(ontology_sqrvice_id=ontology_sqrvice_id).order_by(
            'date_time').last()
        if current_obj is None:
            counter = 0
            while current_obj is None and counter < 20:
                current_obj = CommunicationAct.objects.filter(ontology_sqrvice_id=ontology_sqrvice_id).order_by(
                    'date_time').last()
                if current_obj is None:
                    time.sleep(0.1)
                else:
                    break
                counter += 1

        if current_obj is not None:
            conversation_id = current_obj.conversation_id
            CommunicationAct.objects.create(conversation_id=conversation_id, type="q_e_i",
                                            receivers=json.dumps(received_json_data.get("receivers"),
                                                                 ensure_ascii=False),
                                            content=received_json_data['content'],
                                            query_sqrvice_id=current_obj.query_sqrvice_id,
                                            ontology_sqrvice_id=received_json_data['content']).save()
            get_results_message = {
                "performative": "request",
                "password": chatbot_config.ontology_agent_password,
                "sender": chatbot_config.name,
                "receivers": [chatbot_config.ontology_agent_name],
                "reply-to": received_json_data['content'],
                "content": received_json_data['content'],
                "language": "text",
                "protocol": "fipa-request protocol",
                "reply-with": received_json_data['content'],
                "conversationID": conversation_id,
                "enconding": "utf-8",
                "ontology": "",
                "in-reply-to": "",
                "reply-by": ""
            }

            CommunicationAct.objects.create(conversation_id=conversation_id, type="r_q_r",
                                            receivers=json.dumps([chatbot_config.ontology_agent_name],
                                                                 ensure_ascii=False),
                                            content=received_json_data['content'],
                                            query_sqrvice_id=current_obj.query_sqrvice_id,
                                            ontology_sqrvice_id=ontology_sqrvice_id).save()
            try:
                ontology_agent_response = requests.post(url=chatbot_config.ontology_agent_url,
                                                        json=get_results_message)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                receivers=json.dumps([chatbot_config.name],
                                                                     ensure_ascii=False),
                                                content=json.dumps([]),
                                                query_sqrvice_id=current_obj.query_sqrvice_id,
                                                ontology_sqrvice_id=ontology_sqrvice_id).save()
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)

            try:
                if ontology_agent_response.json().get("performative") == "inform":
                    ontology_agent_result = ontology_agent_response.json().get("content")

                    CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                    receivers=json.dumps(
                                                        ontology_agent_response.json().get("receivers"),
                                                        ensure_ascii=False),
                                                    content=ontology_agent_result,
                                                    query_sqrvice_id=current_obj.query_sqrvice_id,
                                                    ontology_sqrvice_id=ontology_sqrvice_id).save()
                else:
                    CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                    receivers=json.dumps(
                                                        ontology_agent_response.json().get("receivers"),
                                                        ensure_ascii=False),
                                                    content=json.dumps([]),
                                                    query_sqrvice_id=current_obj.query_sqrvice_id,
                                                    ontology_sqrvice_id=ontology_sqrvice_id).save()
                    return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                print("No results")
                CommunicationAct.objects.create(conversation_id=conversation_id, type="q_r",
                                                receivers=json.dumps(json.dumps([chatbot_config.name]),
                                                                     ensure_ascii=False),
                                                content=json.dumps([]),
                                                query_sqrvice_id=current_obj.query_sqrvice_id,
                                                ontology_sqrvice_id=ontology_sqrvice_id).save()
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
        else:
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)

        return HttpResponse(status=status.HTTP_200_OK)


class Unsubsrcibe(View):
    def get(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is None:
            return redirect('/')
        return render(request, template_name="unsubscribe_form.html")

    def post(self, request, *args, **kwargs):
        convresation_id = request.session.get("convresation_id")
        if convresation_id is None:
            return redirect('/')
        if request.COOKIES.get("is_webhook") is None:
            request.session.set_expiry(2)
        form = Form(request.POST or None)
        if form.is_valid():
            result = form.data.get("result")
            if result is not None:
                try:
                    if result == "False":
                        context = dict()
                        context["primary_answers"] = [{"name": "result evaluation",
                                                       "content": "negative", "comment": ""}]
                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="result_evaluation",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                    else:
                        context = dict()
                        context["primary_answers"] = [{"name": "result evaluation",
                                                       "content": "positive", "comment": ""}]
                        UserDialogPosition.objects.create(conversation_id=convresation_id, type="result_evaluation",
                                                          content=json.dumps(context, ensure_ascii=False),
                                                          additional_info=json.dumps([])).save()
                except Exception as e:
                    print(e)
                    print(traceback.format_exc())

            ontology_agent_unsubscribe_message = {
                    "performative": "unsubscribe",
                    "password": chatbot_config.ontology_agent_password,
                    "sender": chatbot_config.name,
                    "receivers": [chatbot_config.ontology_agent_name],
                    "reply-to": "",
                    "content": convresation_id,
                    "language": "text",
                    "protocol": "fipa-request protocol",
                    "reply-with": convresation_id,
                    "conversationID": convresation_id,
                    "enconding": "utf-8",
                    "ontology": "",
                    "in-reply-to": "",
                    "reply-by": ""
            }
            CommunicationAct.objects.create(conversation_id=convresation_id, type="r_u",
                                            receivers=json.dumps([chatbot_config.ontology_agent_name],
                                                                 ensure_ascii=False),
                                            content=convresation_id,
                                            query_sqrvice_id=None,
                                            ontology_sqrvice_id=None).save()
            try:
                ontology_agent_response = requests.post(url=chatbot_config.ontology_agent_url,
                                                        json=ontology_agent_unsubscribe_message)

                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_u_a",
                                                receivers=json.dumps(
                                                    ontology_agent_response.json().get("receivers"), ensure_ascii=False),
                                                content=ontology_agent_response.json().get("content"),
                                                query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                ontology_agent_response = None

            converter_agent_unsubscribe_message = {
                "performative": "unsubscribe",
                "password": chatbot_config.sparql_converter_password,
                "sender": chatbot_config.name,
                "receivers": [chatbot_config.sparql_converter_name],
                "reply-to": "",
                "content": convresation_id,
                "language": "text",
                "protocol": "fipa-request protocol",
                "reply-with": convresation_id,
                "conversationID": convresation_id,
                "enconding": "utf-8",
                "ontology": "",
                "in-reply-to": "",
                "reply-by": ""
            }

            try:
                converter_agent_response = requests.post(url=chatbot_config.sparql_converter_url,
                                                         json=converter_agent_unsubscribe_message)
                CommunicationAct.objects.create(conversation_id=convresation_id, type="r_u_a",
                                                receivers=json.dumps(
                                                    converter_agent_response.json().get("receivers"),
                                                    ensure_ascii=False),
                                                content=converter_agent_response.json().get("content"),
                                                query_sqrvice_id=None,
                                                ontology_sqrvice_id=None).save()
            except Exception as e:
                print(e)
                print(traceback.format_exc())
                converter_agent_response = None

            if ontology_agent_response is not None and converter_agent_response is not None:
                if "convresation_id" in request.session:
                    try:
                        del request.session["convresation_id"]
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())
        context = {"status": True}
        return HttpResponse(json.dumps(context), content_type="application/json")


salt = b'^\x17\x9d\xe6\xb0?\xe9\xad\xe4\x04\xe4\x010p\xa4\xcd\xe6`(\x8e\\g\xa7\x19\xd9~\xe8;\xddu\x12\xa0'
key = b'\x02\x8a\xeb\x96\xfe$r\xdaG\xc9Q\x1e(+\x8e\x0e\x8a\xcfr\xe1\xb5G\x8d\x12\xc0\xa6Qe\x90\xcc\xf5\xdb'


class DialogLogs(View):
    def __form_out_json__(self, massages_range):
        sorted_by_conversation = dict()
        for message in massages_range:
            current_id = message.conversation_id
            if current_id not in sorted_by_conversation:
                sorted_by_conversation[current_id] = []
            current_type = message.type.strip()
            if current_type == "question":
                current_content = message.content
            else:
                current_content = json.loads(message.content)
            current_date = message.date_time.strftime('%B %d %Y %H:%M:%S')
            sorted_by_conversation[current_id].append({"type": current_type,
                                                       "content": current_content,
                                                       "date": current_date})
        out = []
        for item_id in sorted_by_conversation:
            out.append(sorted_by_conversation[item_id])
        out = sorted(out, key=lambda n: n[0].get("date"))
        return out

    def __form_file_response__(self, selection):
        filename = "dialogs_log.json"
        content = json.dumps(selection)
        response = HttpResponse(content.encode("utf-8").decode("utf-8"), content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename={0}'.format(filename)
        return response

    def get(self, request):
        return HttpResponse(status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        try:
            received_json_data = json.loads(request.body.decode("utf-8"))
            password = received_json_data.get("password")
            if password is None:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            new_key = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
            if new_key != key:
                return HttpResponse(status=status.HTTP_404_NOT_FOUND)
            period = received_json_data.get("period")
            beginning = None
            end = None
            if period is not None:
                beginning = period.get("beginning")
                if beginning is not None and isinstance(beginning, str):
                    try:
                        beginning = datetime.strptime(beginning.replace(
                            ",", "").replace(" p.m.", "PM").replace(" a.m.", "AM").strip(), '%B %d %Y %I:%M%p')
                        print("beginning", beginning)
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())
                        beginning = None
                else:
                    beginning = None
                end = period.get("end")
                if end is not None and isinstance(end, str):
                    try:
                        end = datetime.strptime(end.replace(
                            ",", "").replace(" p.m.", "PM").replace(" a.m.", "AM").strip(), '%B %d %Y %I:%M%p')
                        print("end", end)
                    except Exception as e:
                        print(e)
                        print(traceback.format_exc())
                        end = None
                else:
                    end = None

            if period is None or (beginning is None and end is None):
                all_dialogs = UserDialogPosition.objects.all().order_by('date_time')
            elif beginning is None and end is not None:
                all_dialogs = UserDialogPosition.objects.filter(date_time__lte=end).order_by('date_time')
            elif beginning is not None and end is None:
                all_dialogs = UserDialogPosition.objects.filter(date_time__gte=beginning).order_by('date_time')
            else:
                all_dialogs = UserDialogPosition.objects.filter(date_time__range=(beginning, end)).order_by('date_time')

            sorted_by_conversation = self.__form_out_json__(all_dialogs)
            response = self.__form_file_response__(sorted_by_conversation)
            return response

        except Exception as e:
            print(e)
            print(traceback.format_exc())
            return HttpResponse(status=status.HTTP_404_NOT_FOUND)


def db_clean():
    while True:
        current_objects = CommunicationAct.objects.all()

        for obj in current_objects:
            d_time = datetime.now(timezone.utc) - obj.date_time
            # print(d_time.total_seconds(), chatbot_config.db_clean_time)
            if d_time.total_seconds() > chatbot_config.db_clean_time:
                obj.delete()
        time.sleep(chatbot_config.garbage_deleting)


t = Thread(target=db_clean, kwargs={}, daemon=True)
t.start()













