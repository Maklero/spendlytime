from datetime import timedelta, datetime

from django.utils import timezone
from django.http import Http404
from django.contrib.auth.models import User

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import APIException

from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer

from spendlytime.models import Trace
from spendlytime.api import serializers


class TraceListAPIView(APIView):
    """
    The trace view, return all traces from current session user
    and afford a create new trace
    """
    permission_classes = [IsAuthenticated]

    def get_object(self, pk):
        try:
            return Trace.objects.get(id=pk)
        except Trace.DoesNotExist:
            raise Http404

    def get(self, request, pk=None):
        current_user = request.user
        if not pk:
            traces = Trace.objects.filter(user_id=current_user.id).all()
        else:
            traces = Trace.objects.filter(
                id=pk, user_id=current_user.id)
            if not traces:
                raise Http404

        serializer = serializers.TraceSerializer(traces, many=True)

        return Response(serializer.data)

    def post(self, request):
        serializer = serializers.TraceSerializer(
            context={"request": request}, data=request.data)
        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data, status.HTTP_201_CREATED)
        else:
            errors = serializer.errors

            return Response(errors, status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk=None):
        trace = self.get_object(pk)
        trace.delete()

        return Response(status=status.HTTP_200_OK)


class MeAPIView(APIView):
    """
    This view is returing current user.
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        current_user = request.user
        user = User.objects.filter(id=current_user.id)
        serializer = serializers.UserSerializer(user, many=True)

        return Response(serializer.data)


class TokenAPIView(APIView):
    """
    The api token view class, generating a auth token
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # Get current user session
        current_user = request.user
        # Create token if not exist of current user but exist return token
        token = Token.objects.get_or_create(user=current_user)
        return Response({"api-token": str(token[0])})


class TimerAPIView(APIView):
    """
    The main class for timer endpoint
    """
    # permission_classes = [IsAuthenticated]

    def get_object(self, id: int):
        try:
            return Trace.objects.get(id=id)
        except Trace.DoesNotExist:
            raise Http404

    def post(self, request, pk):
        serializer = serializers.TimerSerializer(data=request.data)
        if serializer.is_valid():
            trace = self.get_object(pk)

            # Convert new time to timedelta
            new_time = serializer.data["time"]
            new_time = datetime.strptime(new_time, "%H:%M:%S")
            new_time = timedelta(hours=new_time.hour, minutes=new_time.minute, seconds=new_time.second)

            # Convert last trace time to timedelta and add new time to last track time
            last_time = trace.trace_time
            last_time = timedelta(hours=last_time.hour, minutes=last_time.minute, seconds=last_time.second)
            time = last_time + new_time

            # str(time) is required because django models is convert str to TimeField
            trace.trace_time = str(time)
            trace.save()

            # Response current time value
            return Response({"trace_time": str(time)}, status.HTTP_200_OK)
        else:
            errors = serializer.errors
            return Response(errors, HTTP_400_BAD_REQUEST)