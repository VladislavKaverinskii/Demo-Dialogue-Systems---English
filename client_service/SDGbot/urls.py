# -*- coding: utf-8 -*-

from django.urls import path
from . import views
from django.views.decorators.csrf import csrf_exempt

urlpatterns = [
    path('', csrf_exempt(views.StartConversation.as_view()), name="index"),
    path('process_question/', csrf_exempt(views.ProcessQuestion.as_view()), name="process_question"),
    path('process_requests/', csrf_exempt(views.ProcessRequests.as_view()), name="process_requests"),
    path('process_answers/', csrf_exempt(views.OntainOntologyAnswers.as_view()), name="process_answers"),
    # path('process_question/see_related/', csrf_exempt(views.ShowRelated.as_view()), name="see_related"),
    path('process_question/ask_unsubscribe/', csrf_exempt(views.Unsubsrcibe.as_view()), name="ask_unsubsrcibe"),
    path('ask_unsubscribe/', csrf_exempt(views.Unsubsrcibe.as_view()), name="ask_unsubsrcibe"),
    path('get_answer/', csrf_exempt(views.GetFinalAnswer.as_view()), name="get_answer"),
    path('get_history/', csrf_exempt(views.GetDialogHistory.as_view()), name="get_history"),

    path('european_parlament/', csrf_exempt(views.StartConversationEP.as_view()), name="index_2"),
    path('european_parlament/get_history/', csrf_exempt(views.GetDialogHistory.as_view()), name="get_history"),
    path('european_parlament/process_question/', csrf_exempt(views.ProcessQuestionEP.as_view()), name="process_question"),

    path('aliyev/', csrf_exempt(views.StartConversationAliyev.as_view()), name="index_3"),
    path('aliyev/get_history/', csrf_exempt(views.GetDialogHistory.as_view()), name="get_history"),
    path('aliyev/process_question/', csrf_exempt(views.ProcessQuestionAliyev.as_view()), name="process_question_aliyev"),
]

