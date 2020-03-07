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
from pyfcm import FCMNotification

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
    Messaging,
    Notifications
)

from .serializers import(
    EvaluatorSerializer,
    MessagingSerializer,
    NotificationSerilizer
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
            push_service = FCMNotification(api_key="AIzaSyD8v3e4a3v-rcasU3Mh0KKkPaflm1dW1J4")
            if serializer.is_valid():
                serializer.save()
                if not serializer.data['message_conf']:
                    devices = Notifications.objects.all().exclude(user=request.user)
                    registration_ids=[]
                    for i in devices:
                        registration_ids.append(i.device_id)
                    result = push_service.notify_multiple_devices(registration_ids=registration_ids, message_title=serializer.data['message_heading'], message_body=serializer.data['message_body'])
                    print(result)
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)
        else:
            request.data['user']=request.user
            serializer = MessagingSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=201)
            return Response(serializer.errors, status=400)

class NotificationView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self,request):
        serializer=NotificationSerilizer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=200)
        else:
            return Response(serializer.errors, status=400)



