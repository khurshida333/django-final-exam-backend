from django.shortcuts import render
from rest_framework import viewsets
from . import models
from . import serializers
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from rest_framework.authtoken.models import Token
# for sending email
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.shortcuts import redirect
from rest_framework import status


# Create your views here.

class StudentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = models.Student.objects.all()
    serializer_class = serializers.StudentSerializer

class StudentRegistrationAPIView(APIView):
    serializer_class = serializers.StudentRegistrationSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            print(user)
            token = default_token_generator.make_token(user)
            print("token", token)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            print("uid", uid)
            print(user.email)
            confirm_link = f"http://127.0.0.1:8000/student/active/{uid}/{token}"
            email_subject = "Confirm Your Email"
            email_body = render_to_string('confirm_student_email.html', {'confirm_link' : confirm_link})
            email = EmailMultiAlternatives(email_subject,'',to=[user.email])
            email.attach_alternative(email_body, "text/html")
            email.send()
            return Response({"message": "Check your mail for confirmation"}, status=status.HTTP_201_CREATED)
        return Response({"errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

def student_activate(request, uid64, token):
    try:
        uid = urlsafe_base64_decode(uid64).decode()
        user = User._default_manager.get(pk=uid)
    except(User.DoesNotExist):
        user = None 
    
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        return redirect('http://127.0.0.1:5500/student_login.html')
    else:
        return redirect('http://127.0.0.1:5500/student_reg.html')

    

class StudentLoginApiView(APIView):
    def post(self, request):
        serializer = serializers.StudentLoginSerializer(data = self.request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']

            user = authenticate(username= username, password=password)
            
            if user:
                token, _ = Token.objects.get_or_create(user=user)
                print(token)
                print(_)
                login(request, user)
                return Response({'student_token' : token.key, 'student_id' : user.id})
            else:
                return Response({'error' : "Invalid Credential"})
        return Response(serializer.errors)


class StudentLogoutView(APIView):
    def get(self, request):
        try:
            
            if hasattr(request.user, 'auth_token'):
                request.user.auth_token.delete() 

          
            logout(request)

           
            return Response({"message": "Logout student successful"}, status=status.HTTP_200_OK)

        except Exception as e:
            
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


