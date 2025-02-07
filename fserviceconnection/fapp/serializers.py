from rest_framework import serializers
from .models import Register,OTP,Profile,Services, Subservices, ServiceRegistry,ServiceRequest,BookingList
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = Register
        fields = ['id', 'name', 'email', 'password', 'phone_number', 'created_at']
        extra_kwargs = {
            'password': {'write_only': True}, 
            'created_at': {'read_only': True}, 
        }

    def create(self, validated_data):
        validated_data['password'] = make_password(validated_data['password'])
        return Register.objects.create(**validated_data)

    def validate_password(self, value):
        """
        Custom password validation logic, if needed.
        Example: You can add checks like minimum length or special characters.
        """
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        return value
       
class OTPVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = Register.objects.get(email=email)
        except Register.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")

        try:
            otp_entry = OTP.objects.filter(user=user).order_by('-created_at').first()
        except OTP.DoesNotExist:
            raise serializers.ValidationError("No OTP found for this user.")

        if otp_entry.otp_code != otp_code:
            raise serializers.ValidationError("Invalid OTP code.")

        if otp_entry.created_at < timezone.now() - timedelta(minutes=5):
            raise serializers.ValidationError("OTP has expired.")

        return attrs

    def save(self):
        email = self.validated_data['email']
        user = Register.objects.get(email=email)
        OTP.objects.filter(user=user).delete()
        return user
    
class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = [
            'full_name', 'address', 'email', 'phone_number', 'date_of_birth',
            'gender', 'house_name', 'landmark', 'pin_code', 'district', 'state'
        ]
    
    def validate_email(self, value):
        user = Register.objects.filter(email=value).first()
        if user and user.email != value:
            raise serializers.ValidationError("Email is already in use.")
        return value
    
    
    
    
class SubservicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subservices
        fields = ['id', 'title', 'description', 'image']

class ServicesSerializer(serializers.ModelSerializer):
    subservices = SubservicesSerializer(many=True, read_only=True) 

    class Meta:
        model = Services
        fields = ['id', 'title', 'description', 'image', 'status', 'subservices']
        
        
        
        
class ServiceRegistrySerializer(serializers.ModelSerializer):
    employee_name = serializers.CharField(source='employee.name', read_only=True)  
    service_title = serializers.CharField(source='service.title', read_only=True) 

    class Meta:
        model = ServiceRegistry
        fields = ['id', 'employee', 'employee_name', 'service', 'service_title', 'min_price', 'max_price', 'description']
        
        

class ServiceRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceRequest
        fields = '__all__'  # Or list specific fields if needed

class BookingListSerializer(serializers.ModelSerializer):
    register = RegisterSerializer()  # Nested serializer to show the user data
    service_request = ServiceRequestSerializer()  # Nested serializer to show service request data

    class Meta:
        model = BookingList
        fields = '__all__'