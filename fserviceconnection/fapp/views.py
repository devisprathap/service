from rest_framework.views import APIView
from .serializers import RegisterSerializer,OTPVerificationSerializer,ProfileSerializer, ServicesSerializer, SubservicesSerializer, ServiceRegistrySerializer, ServiceRequestSerializer, BookingListSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from .manager import create_otp_for_user
from .email import send_otp_via_email
from django.contrib.auth.hashers import check_password
from .models import Register,Profile,Services, Subservices, ServiceRegistry, ServiceRequest,BookingList
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.generics import ListAPIView
from rest_framework.decorators import api_view
from .pagination import CustomPagination
    
class RegisterAPIView(APIView):
    permission_classes=[AllowAny]
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "User registered successfully", "user": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST) 

class LoginAPIView(APIView):
    permission_classes=[IsAuthenticated] 
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({"error": "Email and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = Register.objects.get(email=email)
            if check_password(password, user.password):
                otp_code = create_otp_for_user(user)

                send_otp_via_email(email, otp_code)   
        
                return Response({"message": "Login successful check your mail", "user": {"id": user.id, "name": user.name, "email": user.email}}, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)
        except Register.DoesNotExist:
            return Response({"error": "Invalid email or password."}, status=status.HTTP_401_UNAUTHORIZED)  

class OTPVerificationAPIView(APIView):
    def post(self, request):
        serializer = OTPVerificationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()  # Delete OTP after successful verification
            return Response({"message": "OTP verified successfully."}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class ProfileCreateView(APIView):
    permission_classes = [IsAuthenticated]  

    def get(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            serializer = ProfileSerializer(profile)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request):
        user = request.user
        
        if Profile.objects.filter(user=user).exists():
            return Response({"message": "Profile already exists."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = ProfileSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=user)
            return Response({"message": "Profile created successfully.", "profile": serializer.data}, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile updated successfully.", "profile": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Profile partially updated successfully.", "profile": serializer.data}, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        user = request.user
        try:
            profile = Profile.objects.get(user=user)
            profile.delete()
            return Response({"message": "Profile deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
        except Profile.DoesNotExist:
            return Response({"message": "Profile not found."}, status=status.HTTP_404_NOT_FOUND)
    

    

class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if not refresh_token:
                return Response({"error": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)
            
            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            return Response({"message": "Successfully logged out."}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)             
        
        
        
        
class ServicesAPIView(APIView):
    def get(self, request):
        """Retrieve all services with their associated subservices."""
        services = Services.objects.all()
        data = []

        for service in services:
            subservices = service.subservices.all() 
            subservices_serializer = SubservicesSerializer(subservices, many=True)
            service_data = {
                "id": service.id,
                "title": service.title,
                "image": service.image.url if service.image else None,
                "description": service.description,
                "status": service.status,
                "subservices": subservices_serializer.data,
            }
            data.append(service_data)

        return Response(data, status=status.HTTP_200_OK)
    
    
    
    
    
    
class ServiceRegistryView(APIView):
    
    def get(self, request):
        """Retrieve all ServiceRegistry records."""
        service_registries = ServiceRegistry.objects.all()
        serializer = ServiceRegistrySerializer(service_registries, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    
    
    
    
    
    
    
class ServiceRequestAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure the user is authenticated

    def get(self, request, pk=None):
        """
        Retrieve a list of all service requests or a specific one by ID.
        """
        if pk:
            try:
                service_request = ServiceRequest.objects.get(pk=pk)
                serializer = ServiceRequestSerializer(service_request)
                return Response(serializer.data, status=status.HTTP_200_OK)
            except ServiceRequest.DoesNotExist:
                return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        # If no `pk` is provided, return all service requests
        service_requests = ServiceRequest.objects.all()
        serializer = ServiceRequestSerializer(service_requests, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new service request.
        """
        # Make a mutable copy of the request data and add the currently authenticated user to 'register'
        data = request.data.copy()  # Mutable copy
        data['register'] = request.user.id  # Set the 'register' field to the current user's ID
        
        # Serialize the data
        serializer = ServiceRequestSerializer(data=data)
        
        if serializer.is_valid():
            serializer.save()  # Save the new service request
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk):
        """
        Update an existing service request.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceRequestSerializer(service_request, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        """
        Partially update an existing service request.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ServiceRequestSerializer(service_request, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete an existing service request.
        """
        try:
            service_request = ServiceRequest.objects.get(pk=pk)
        except ServiceRequest.DoesNotExist:
            return Response({"error": "ServiceRequest not found."}, status=status.HTTP_404_NOT_FOUND)

        service_request.delete()
        return Response({"message": "ServiceRequest deleted successfully."}, status=status.HTTP_204_NO_CONTENT)
    
    
    
class BookingListView(APIView):
    def get(self, request):
        bookings = BookingList.objects.select_related('register', 'service_request').all()
        paginator = CustomPagination()
        paginated_queryset = paginator.paginate_queryset(bookings, request, view=self)
        serializer = BookingListSerializer(paginated_queryset, many=True)
        return paginator.get_paginated_response(serializer.data)


