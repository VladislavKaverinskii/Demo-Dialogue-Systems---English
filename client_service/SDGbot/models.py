# -*- coding: utf-8 -*-

from django.db import models

# Create your models here.


class CommunicationAct(models.Model):
    conversation_id = models.CharField(max_length=200, blank=False, verbose_name="Conversation ID",
                                       default="0")
    type = models.CharField(max_length=10, choices=(("r_c", "reqest conversation"),
                                                    ("r_c_a", "reqest conversation answer"),
                                                    ("r_m_q", "request make queries"),
                                                    ("r_m_q_a", "request make queries answer"),
                                                    ("r_r_q", "request ready queries"),
                                                    ("q_r_i", "queries ready info"),
                                                    ("q_s", "set of queries"),
                                                    ("r_q_e", "requesr queries execution"),
                                                    ("r_q_e_a", "requesr queries execution answer"),
                                                    ("q_e_i", "queries executed info"),
                                                    ("r_q_r", "requesr queries result"),
                                                    ("q_r", "queries result"),
                                                    ("r_u", "reqest unsubscribe"),
                                                    ("r_u_a", "reqest unsubscribe ansver"),),
                            verbose_name="Messege type", blank=False, default="r_m_q")
    content = models.TextField(blank=True, verbose_name="Messege content", null=True)
    query_sqrvice_id = models.CharField(max_length=200, blank=True, null=True,
                                        verbose_name="ID by query creation service")
    ontology_sqrvice_id = models.CharField(max_length=200, blank=True, null=True,
                                           verbose_name="ID by query ontology service")
    receivers = models.TextField(blank=False, verbose_name="Receivers", default="self")
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Time", blank=False)

    class Meta:
        db_table = 'CommunicationActs'
        verbose_name = 'Communication Acts'


class UserDialogPosition(models.Model):
    conversation_id = models.CharField(max_length=200, blank=False, verbose_name="Conversation ID",
                                       default="0")
    type = models.CharField(max_length=30, choices=(("question", "question"),
                                                    ("answer", "answer"),
                                                    ("additional_answer", "additional answer"),
                                                    ("result_evaluation", "result evaluation")),
                            verbose_name="Messege type", blank=False, default="question")
    content = models.TextField(blank=True, verbose_name="Messege content", null=True)
    additional_info =models.TextField(blank=True, verbose_name="Additional information", null=True)
    date_time = models.DateTimeField(auto_now_add=True, verbose_name="Time", blank=False)

    class Meta:
        db_table = 'DialogPositions'
        verbose_name = 'Dialog messages'













