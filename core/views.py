from django.shortcuts import render

# Create your views here.
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.utils.timezone import now
from rest_framework import generics, status, views, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import HttpResponse, JsonResponse
from rest_framework.decorators import api_view, permission_classes

from djoser import signals, utils
from djoser.compat import get_user_email
from djoser.conf import settings
User = get_user_model()
from rest_framework.views import APIView
from fcm_django.models import FCMDevice


from .models import (
    evaluator,
    TeamInfo,
    UserType,
    Messaging
)

from .serializers import(
    EvaluatorSerializer,
    MessagingSerializer
)

class TokenCreateView(utils.ActionViewMixin, generics.GenericAPIView):
    """
    Use this endpoint to obtain user authentication token.
    """

    serializer_class = settings.SERIALIZERS.token_create
    permission_classes = settings.PERMISSIONS.token_create

    def _action(self, serializer):
        token = utils.login_user(self.request, serializer.user)
        token_serializer_class = settings.SERIALIZERS.token
        try: 
            data = {
                'token':token_serializer_class(token).data,
                'user_type' : UserType.objects.filter(user=serializer.user)[0].type_of_user.category,
                'username': serializer.user.username,
                'name': serializer.user.first_name+' '+serializer.user.last_name
            }
        except:
            return HttpResponse(status=404)
        return Response(
            data=data, status=status.HTTP_200_OK
        )



class EvaluatorList(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        try:
            list_of_teams = evaluator.objects.filter(evaluator_object__user=request.user).filter(round_level=1)
        except evaluator.DoesNotExist:
            return HttpResponse(status=404)
        serializer = EvaluatorSerializer(list_of_teams, many=True)
        data = {
            'round':1,
            'data':serializer.data
        }
        return Response(data)


    
class Message(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        if not request.data._mutable:
            request.data._mutable = True
            request.data['user']=request.user.id
            request.data['team']=TeamInfo.objects.filter(team_number=request.data['team'])[0].id
            request.data._mutable = False
            serializer = MessagingSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                if not serializer.data['message_conf']:
                    devices = FCMDevice.objects.all()
                    devices.send_message(title=serializer.data['message_heading'], body=serializer.data['message_body'])
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            request.data['user']=request.user
            serializer = MessagingSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

class Test(APIView):
    permission_classes = [IsAuthenticated]
    def get(self,request):
        dicti = {
            'registration_id':request.GET['registration_id'],
            'user':request.user,
            'type':request.GET['type']
        }
        FCMDevice(**dicti).save()
        return Response('OK', status=200)


