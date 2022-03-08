# -*- coding: utf-8 -*-

import xml.etree.ElementTree as Et
import traceback
import pymorphy2
import json
import time
# morph = pymorphy2.MorphAnalyzer(lang='uk')

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


class QualifierConfig:
    __instance = None

    def __init__(self):
        if not QualifierConfig.__instance:
            self.tree = []
            self.specific_words_beginning = []
            self.specific_words_everywhere = []
        else:
            print("Instance already created:", self.get_instance())

    @classmethod
    def get_instance(cls, config_file="tree.xml"):
        if not cls.__instance:
            cls.__instance = QualifierConfig()
            cls.__instance.config_file = config_file
            with open(config_file, 'r', encoding='utf-8') as xml_file:
                xml_file_data = xml_file.read()
                tree = Et.ElementTree(Et.fromstring(xml_file_data.encode('utf-8').decode('utf-8')))

            root = tree.getroot()

            for i in root:
                if i.tag == "tree":
                    for level in i:
                        if level.tag == "condition_level":
                            new_level = {"id": level.attrib.get("id"),
                                         "positions": dict()}
                            for position in level:
                                if position.tag == "position":
                                    new_position = {"id": position.attrib.get("id"),
                                                    "conditions": dict()}
                                    for condition in position:
                                        if condition.tag == "condition" or "default":
                                            if condition.tag == "condition":
                                                new_condition_id = condition.attrib.get("id")
                                                new_condition = {"id": new_condition_id}
                                            else:
                                                new_condition_id = position.attrib.get("id") + "_default"
                                                new_condition = {"id": new_condition_id}
                                            for tag in condition:
                                                if tag.tag == "words_list":
                                                    new_words_list = []
                                                    for wd in tag:
                                                        if wd is not None and wd.text is not None:
                                                            new_words_list.append(wd.text.strip())
                                                    new_condition["words_list"] = new_words_list
                                                if tag.tag == "next_position" and tag.text is not None:
                                                    new_condition["next_position"] = tag.text
                                                if tag.tag == "result":
                                                    new_result = dict()
                                                    for res in tag:
                                                        if res.tag == "query_type":
                                                            if res.text is not None:
                                                                if new_result.get("query_type") is None:
                                                                    new_result["query_type"] = [res.text.strip()]
                                                                else:
                                                                    new_result["query_type"].append(res.text.strip())
                                                        if res.tag == "input_entity":
                                                            if "input_entity" not in new_result:
                                                                if res.text is not None:
                                                                    new_result["input_entity"] = [res.text.strip()]
                                                            else:
                                                                if res.text is not None:
                                                                    new_result["input_entity"].append(res.text.strip())
                                                    if tag.text is not None:
                                                        new_result["value"] = tag.text.strip()
                                                    new_condition["result"] = new_result
                                            new_position["conditions"][new_condition_id] = new_condition
                                    new_level["positions"][position.attrib.get("id")] = new_position
                            cls.__instance.tree.append(new_level)
                if i.tag == "specific_words":
                    for j in i:
                        if j.tag == "beginning":
                            for item in j:
                                cls.__instance.specific_words_beginning.append(item.text)
                        if j.tag == "everywhere":
                            for item in j:
                                cls.__instance.specific_words_everywhere.append(item.text)
        # print(cls.__instance.tree)
        return cls.__instance


def find_ontology_entity(word_list, chapters="all", current_keywords=[]):
    if isinstance(chapters, str):
        if chapters.lower().strip == "all":
            chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
        elif chapters.lower().strip in ["class_names_dict", "individual_names_dict", "pradicates"]:
            chapters = [chapters]
        else:
            chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
    elif isinstance(chapters, list) or isinstance(chapters, set):
        chapters = chapters
    else:
        chapters = ["class_names_dict", "individual_names_dict", "pradicates"]
    max_metric = 0.0
    output = " ".join(word_list)
    firts_time = True

    # print("current_keywords ", current_keywords)

    for chapter in chapters:
        if chapter in current_keywords:
            for entity in current_keywords[chapter]:
                nouns_match = 0
                adj_match = 0
                verb_match = 0
                other_match = 0
                nouns_extra = 0
                adj_extra = 0
                verb_extra = 0
                other_extra = 0
                not_found_words = set()
                nouns_not_found = 0
                adj_not_found = 0
                verb_not_found = 0
                other_not_found = 0

                total_words = len(word_list)
                total_entity_words = len(current_keywords[chapter][entity]["words"])

                if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                    print("entity ", entity)
                    print("total_words ", total_words)

                p_total = nltk.pos_tag(word_list)
                for cnt, word in enumerate(word_list):
                    input_word_found = False
                    # p = morph.parse(word)
                    p = nltk.pos_tag([word])
                    # word_2 = "."
                    for word_2 in current_keywords[chapter][entity]["words"]:
                        entity_word_found = False
                        entity_word_found_factor = 1.0
                        for word_3 in p_total: # Встречается ли слово из базы во фразе пользователя
                            # Перебираем слова из фразы пользователя
                            # p_2 = morph.parse(word_3)
                            p_2 = [word_3]
                            if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                                print("p_2 ", p_2, "p ", p)
                            for form_2 in p_2:
                                if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                                    print(word_3[-1], word_2["POS"])
                                    print(porter.stem(word_3[0]), word_2["text"])
                                if porter.stem(word_3[0]) in not_found_words:
                                    # Если слово уже вошло в список ненайденых, то его точно нет
                                    entity_word_found = False
                                    if porter.stem(word_3[0]) == word_2["text"]:
                                        entity_word_found_factor = 2.0
                                    break
                                if (porter.stem(word_3[0]) == word_2["text"]):
                                    # Если слово из фразы пользователя совпадает с одним из слов из базы
                                    # по форме и по тексту, то оно найдено
                                    if word_3[-1] != word_2["POS"]:
                                        entity_word_found_factor = 2.0
                                    else:
                                        entity_word_found_factor = 1.0
                                    entity_word_found = True
                                    break
                            if entity_word_found:
                                # Если установлено, что слово из базы есть во фразе мользователя, дальше
                                # перебирать слова из фразы пользователя нет смысла
                                break
                        if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                            print("entity_word_found ", entity_word_found)
                            print("not_found_words ", not_found_words)

                        if not entity_word_found and word_2["text"] not in not_found_words:
                            not_found_words.add(word_2["text"])
                            if word_2["POS"] == "NN" or word_2["POS"] == "NNS" or word_2["POS"] == None:
                                nouns_not_found += 1.0 / entity_word_found_factor
                            elif word_2["POS"] == "JJ" or word_2["POS"] == "RB":
                                adj_not_found += 1.0 / entity_word_found_factor
                            elif word_2["POS"] == "VB" or word_2["POS"] == "VBD" or word_2["POS"] == "VBG" or word_2["POS"] == "VBN":
                                verb_not_found += 1.0 / entity_word_found_factor
                            else:
                                other_not_found += 1.0 / entity_word_found_factor

                        if entity_word_found and porter.stem(word) == word_2["text"]:
                            input_word_found = True
                            if p_total[cnt][-1] == word_2["POS"]:
                                if word_2["POS"] == "NN" or word_2["POS"] == "NNS" or word_2["POS"] == None:
                                    nouns_match += 1.0
                                elif word_2["POS"] == "JJ" or word_2["POS"] == "RB":
                                    adj_match += 1.0
                                elif word_2["POS"] == "VB" or word_2["POS"] == "VBD" or word_2["POS"] == "VBG" or word_2["POS"] == "VBN":
                                    verb_match += 1.0
                                else:
                                    other_match += 1.0
                            else:
                                if word_2["POS"] == "NN" or word_2["POS"] == "NNS" or word_2["POS"] == None:
                                    nouns_match += 0.5
                                elif word_2["POS"] == "JJ" or word_2["POS"] == "RB":
                                    adj_match += 0.5
                                elif word_2["POS"] == "VB" or word_2["POS"] == "VBD" or word_2["POS"] == "VBG" or word_2["POS"] == "VBN":
                                    verb_match += 0.5
                                else:
                                    other_match += 0.5
                            break
                    if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                        print("input_word_found ", input_word_found)
                    if not input_word_found:
                        current_pos = p[-1][-1]
                        if current_pos == "NN" or current_pos == "NNS" or word_2["POS"] is None:
                            nouns_extra += 1
                        elif current_pos == "JJ" or current_pos == "RB":
                            adj_extra += 1
                        elif current_pos == "VB" or current_pos == "VBD" or current_pos == "VBG" or current_pos == "VBN":
                            verb_extra += 1
                        else:
                            other_extra += 1
                        # break
                    if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                        print("word ", word)
                        print("nouns_extra ", nouns_extra, "adj_extra ", adj_extra, "verb_extra ", verb_extra, "other_extra ", other_extra)
                        print(
                        "nouns_not_found ", nouns_not_found, "adj_not_found ", adj_not_found, "verb_not_found ", verb_not_found, "other_not_found ",
                        other_not_found)

                #print(nouns_not_found, adj_not_found, verb_not_found, other_not_found)
                current_metric = (2.0*float((5*nouns_match + 3*adj_match + 2*verb_match + 1.5*other_match) / (total_words + total_entity_words)) +
                                  2.0*float((-2*nouns_extra - adj_extra - verb_extra - 0.5*other_extra) / (total_words + total_entity_words)) +
                                  2.0*float((-2*nouns_not_found - adj_not_found + 0.5*verb_not_found - 0.5*other_not_found) / (total_words + total_entity_words)))
                if entity == "Revenue_and_slash_or__lbraket_net_rbraket__value_added":
                    print(current_metric)
                if firts_time or current_metric > max_metric:
                    max_metric = current_metric
                    output = entity
                    firts_time = False
                    if (nouns_extra + adj_extra + verb_extra + other_extra == 0 and
                        nouns_not_found + adj_not_found + verb_not_found + other_not_found == 0 and
                        nouns_match + adj_match + verb_match + other_match > 0 and
                        total_entity_words == total_words):
                        return output
                    if nouns_match + adj_match + verb_match + other_match == total_words:
                        return output

        print("max_metric", max_metric, output)
    return output



def clean_phrase(input_str="", qualifier_config=None):
    work_str = input_str.replace(".", "").replace(",", "").replace(";", "").replace("!", "").replace("?", "").replace(
        "/", "").replace("\\", "").replace("@", "").replace("#", "").replace("№", "").replace("$", "").replace(
        "%", "").replace("^", "").replace("&", "").replace("*", "").replace("(", "").replace(")", "").replace(
        "_", "").replace("+", "").replace("=", "").replace("'", "").replace('"', "").replace(":", "").replace(
        "<", "").replace(">", "").replace("`", "").replace("~", "")
    for word in qualifier_config.specific_words_beginning:
        if work_str[:len(word + " ")].lower().strip() + " " == word.strip() + " ":
            # print(work_str[:len(word + " ")].lower().strip() + " ")
            work_str = work_str[len(word):].strip()
    for word in qualifier_config.specific_words_everywhere:
        work_str = work_str.lower().replace(" " + word + " ", " ")
        if work_str[:len(word + " ")] == word + " ":
            work_str = work_str[len(word):]
        if work_str[len(work_str) - len(word + " "):] == " " + word:
            work_str = work_str[:len(work_str) - len(word + " ")]
    return work_str.strip()

def choise_query_template(input_str="", qualifier_config=None):
    result = dict()
    work_str_list = clean_phrase(input_str=input_str, qualifier_config=qualifier_config).split()
    # print("work_str_list", work_str_list)
    extracted_entities = dict()
    sutable_condition = {"max_length": 0, "next_position": "unknown", "next_start": 0}
    # print(qualifier_config.tree)
    for counter, level in enumerate(qualifier_config.tree):
        if counter == 0:
            for position in level["positions"]:
                if "conditions" in level["positions"][position]:
                    for condition in level["positions"][position]["conditions"]:
                        # print(condition)
                        if "words_list" in level["positions"][position]["conditions"][condition]:
                            name_list = []
                            for wd in level["positions"][position]["conditions"][condition]["words_list"]:
                                current_wd_list = wd.strip().split()
                                current_wd_length = len(current_wd_list)
                                is_sutable = True
                                # print(44444444, not (wd.lower().strip() == "any_words" and extracted_entities.get(position) is None))
                                if wd.lower().strip() == "any_words" and extracted_entities.get(position) is None:
                                    # print(work_str_list)
                                    for w_2 in work_str_list:
                                        # p = morph.parse(w_2.strip())
                                        p = nltk.pos_tag([w_2.strip()])
                                        name_list.append(porter.stem(w_2.strip()))
                                    is_sutable = True
                                elif wd.lower().strip() == "any_noun" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        p = nltk.pos_tag([w.strip()])
                                        # p = morph.parse(w.strip())
                                        for form in p:
                                            if form[-1] == "NN" or form[-1] == "NNS" or form[-1] == "JJ":
                                                is_sutable = True
                                                break
                                        if is_sutable:
                                            for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                                # p = morph.parse(w_2.strip())
                                                p = nltk.pos_tag([w_2.strip()])
                                                more_nouns = False
                                                for form in p:
                                                    # print(form.tag.POS, w_2.strip(), form.normal_form)
                                                    if form[-1] == "NN" or form[-1] == "NNS" or form.tag.POS == "JJ":
                                                        name_list.append(porter.stem(w_2.strip()))
                                                        more_nouns = True
                                                        break
                                                if not more_nouns:
                                                    break
                                else:
                                    # print(current_wd_length, len(work_str_list))
                                    if current_wd_length > len(work_str_list):
                                        is_sutable = False
                                        continue
                                    if extracted_entities.get(position) is not None:
                                        # print(current_wd_length, extracted_entities.get(position))
                                        if current_wd_length <= len(extracted_entities.get(position).split()):
                                            is_sutable = False
                                            continue
                                    for c, w in enumerate(current_wd_list):
                                        # print(c, w, work_str_list[c])
                                        compare_1 = w.lower().strip()
                                        compare_2 = work_str_list[c].lower().strip()
                                        if compare_1 != compare_2:
                                            # p_1 = morph.parse(compare_1)
                                            # p_2 = morph.parse(compare_2)

                                            p_1 = nltk.pos_tag([compare_1])
                                            p_2 = nltk.pos_tag([compare_2])

                                            lemma_match = False
                                            for variant_1 in p_1:
                                                for variant_2 in p_2:
                                                    if porter.stem(variant_1[0]) == porter.stem(variant_2[0]):
                                                        lemma_match = True
                                                        break
                                                if lemma_match:
                                                    break
                                            if not lemma_match:
                                                is_sutable = False
                                                break

                                # print("is_sutable", is_sutable)
                                if not is_sutable:
                                    continue
                                elif (is_sutable and sutable_condition["max_length"] < current_wd_length and
                                            "result" not in level["positions"][position]["conditions"][condition]):
                                        # print(11111111111111)
                                        sutable_condition["max_length"] = current_wd_length
                                        if level["positions"][position]["conditions"][
                                            condition].get("next_position"):
                                            sutable_condition["next_position"] = level["positions"][position]["conditions"][
                                                condition]["next_position"]
                                        else:
                                            continue
                                        sutable_condition["next_start"] = current_wd_length
                                        extracted_entities[position] = wd.strip()
                                elif (is_sutable and sutable_condition["max_length"] < current_wd_length and
                                            "result" in level["positions"][position]["conditions"][condition]):
                                    # print(3333333333)
                                    if len(name_list) > 0:
                                        position_n = sutable_condition["next_position"]
                                        extracted_entities[position] = name_list
                                        sutable_condition["max_length"] = len(name_list)
                                    else:
                                        extracted_entities[position] = wd.strip()
                                    # print("extracted_entities", extracted_entities)
                                    sutable_condition["next_position"] == "final"

                                    result["query_type"] = level["positions"][position]["conditions"][condition]["result"].get(
                                        "query_type")
                                    input_entity_n = level["positions"][position]["conditions"][condition]["result"].get(
                                        "input_entity")

                                    if input_entity_n is not None:
                                        result["input_entity"] = [extracted_entities.get(ent) for ent in input_entity_n]
                                    else:
                                        result["input_entity"] = None
                                    break


                        # print("result", result)
            # print("next_position 11111", sutable_condition["next_position"])
            if sutable_condition["next_position"] == "final":
                break
            # print(sutable_condition)
            # print(extracted_entities)

        else:
            position_n = sutable_condition["next_position"]
            sutable_condition["max_length"] = 0
            sutable_condition["next_position"] = "unknown"
            # print("position_n", position_n)
            if position_n != "unknown" and position_n != "final":
                next_position = level["positions"].get(position_n)
                # print("next_position 22222", next_position)
                if next_position is not None and "conditions" in next_position:
                    for condition in next_position["conditions"]:
                        if "words_list" in next_position["conditions"][condition]:
                            name_list = []
                            for wd in next_position["conditions"][condition]["words_list"]:
                                is_sutable = True
                                if wd.lower().strip() == "any_words" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    # print(sutable_condition["next_start"], len(work_str_list))
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        is_sutable = True
                                    if is_sutable:
                                        for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                            # p = morph.parse(w_2.strip())[0]
                                            p = nltk.pos_tag([w_2.strip()])[-1]
                                            name_list.append(porter.stem(p[0]))
                                        # print("name_list 1", name_list)
                                elif wd.lower().strip() == "any_undefined" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    # print(sutable_condition["next_start"], len(work_str_list))
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        is_sutable = True
                                    # if is_sutable:
                                        w = work_str_list[sutable_condition["next_start"]]
                                        # p = morph.parse(w.strip())[0]
                                        p = nltk.pos_tag([w.strip()])[-1]
                                        name_list.append(porter.stem(p[0]))
                                        # print("name_list 1", name_list)

                                elif wd.lower().strip() == "any_noun" and sutable_condition["max_length"] == 0:
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        # p = morph.parse(w.strip())
                                        p = nltk.pos_tag([w.strip()])
                                        for form in p:

                                            if form[-1] == "NN" or form[-1] == "NNS" or form[-1] == "JJ":
                                                is_sutable = True
                                                break
                                        if is_sutable:
                                            for w_2 in work_str_list[sutable_condition["next_start"]:]:
                                                # p = morph.parse(w_2.strip())
                                                p = nltk.pos_tag([w_2.strip()])
                                                more_nouns = False
                                                for form in p:
                                                    # print(form.tag.POS, w_2.strip(), form.normal_form)
                                                    if form[-1] == "NN" or form[-1] == "NNS":
                                                        name_list.append(porter.stem(form[0]))
                                                        more_nouns = True
                                                        break
                                                    elif form[-1] == "JJ":
                                                        if (len(form.normal_form) > 4 and
                                                            form[0][len(form[0]) - 1:] == "y"):
                                                            name_list.append(porter.stem(form[0]))
                                                            more_nouns = True
                                                            break
                                                        elif (len(form.normal_form) > 3 and
                                                              form[0][len(form[0]) - 2:] == "ie"):
                                                            name_list.append(porter.stem(form[0]))
                                                            more_nouns = True

                                                if not more_nouns:
                                                    break

                                elif wd.lower().strip() == "year_str":
                                    is_sutable = False
                                    if sutable_condition["next_start"] < len(work_str_list):
                                        w = work_str_list[sutable_condition["next_start"]]
                                        if len(w) == 4 and w.isdigit():
                                            is_sutable = True
                                    else:
                                        is_sutable = False
                                elif wd.lower().strip() == "not_noun" and sutable_condition["max_length"] == 0:
                                    # print("not_noun")
                                    # print(sutable_condition["next_start"] + 1 >= len(work_str_list))
                                    if sutable_condition["next_start"] + 1 >= len(work_str_list):
                                        is_sutable = True
                                    else:
                                        w = work_str_list[sutable_condition["next_start"]]
                                        # p = morph.parse(w.strip())
                                        p = nltk.pos_tag([w.strip()])
                                        for form in p:
                                            if form[-1] == "NN" or form[-1] == "NNS" or form[-1] == "JJ":
                                                is_sutable = False
                                                break
                                else:
                                    is_sutable = False
                                # print(is_sutable, work_str_list[sutable_condition["next_start"]])
                                if not is_sutable:
                                    # print("qwerty")
                                    is_sutable = True
                                    current_wd_list = wd.strip().split()
                                    current_wd_length = len(current_wd_list)

                                    if current_wd_length > (len(work_str_list) - sutable_condition["next_start"]):
                                        is_sutable = False
                                        continue
                                    for c, w in enumerate(current_wd_list):
                                        # print(work_str_list[c + sutable_condition["next_start"]], w)
                                        if w != work_str_list[c + sutable_condition["next_start"]]:
                                            is_sutable = False
                                            break
                                    if not is_sutable:
                                        continue
                                    else:
                                        if is_sutable and sutable_condition["max_length"] < current_wd_length:
                                            sutable_condition["max_length"] = current_wd_length
                                            sutable_condition["next_position"] = next_position["conditions"][
                                                condition].get("next_position")
                                            extracted_entities[position_n] = wd.strip()
                                            # print("extracted_entities[position_n]", extracted_entities[position_n])
                                else:
                                    if len(name_list) > 0:
                                        sutable_condition["max_length"] = len(name_list)
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = name_list
                                        # print("name_list", name_list)
                                    elif wd.lower().strip() == "year_str":
                                        sutable_condition["max_length"] = 1
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = "Year_" + work_str_list[sutable_condition["next_start"]]
                                    elif wd.lower().strip() == "any_undefined":
                                        sutable_condition["max_length"] = 0
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        extracted_entities[position_n] = work_str_list[sutable_condition["next_start"]]
                                    elif wd.lower().strip() == "not_noun":
                                        sutable_condition["max_length"] = 0
                                        sutable_condition["next_position"] = next_position["conditions"][
                                            condition].get("next_position")
                                        if sutable_condition["next_start"] + 1 >= len(work_str_list):
                                            extracted_entities[position_n] = ""
                                        else:
                                            extracted_entities[position_n] = work_str_list[
                                                sutable_condition["next_start"]]


                        if (sutable_condition["next_position"] is None and "result" in next_position[
                                "conditions"][condition]):
                            print(extracted_entities)
                            print(next_position["conditions"][condition]["result"])
                            result["query_type"] = next_position["conditions"][condition]["result"].get("query_type")
                            input_entity_n = next_position["conditions"][condition]["result"].get("input_entity")
                            if input_entity_n is not None:
                                result["input_entity"] = [extracted_entities.get(ent) for ent in input_entity_n]
                            else:
                                result["input_entity"] = None
                            break

                if len(result) > 0:
                    break

                sutable_condition["next_start"] += sutable_condition["max_length"]
                # print(sutable_condition)
            elif position_n == "unknown" and result.get("query_type") is None:
                result["query_type"] = 'unknown'
                break
            else:
                break

    # print(extracted_entities)

    return result


def fit_input_entities(raw_result, current_keywords):
    if isinstance(raw_result, dict) and 'input_entity' in raw_result and\
            (isinstance(raw_result.get('input_entity'), list) or isinstance(raw_result.get('input_entity'), set)):
        raw_result['input_entity'] = [find_ontology_entity(ent, current_keywords=current_keywords) if isinstance(ent, list) else
                                      find_ontology_entity(ent.split(), current_keywords=current_keywords) for ent in raw_result.get('input_entity')]

    return raw_result












if __name__ == "__main__":
    config = QualifierConfig.get_instance()
    t_0 = time.time()
    cleaned_phrase = choise_query_template(input_str="таблиця іа з розділу 2",
                                  qualifier_config=config)
    d_t = time.time() - t_0
    print(d_t)
    print(cleaned_phrase)
    result = fit_input_entities(cleaned_phrase)
    print(result)

# "Що відомо тобі про те, які листи отримував О. Гончар 1956 року?"