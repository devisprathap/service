from django.contrib import admin
from .models import Register,OTP,Profile,Services,Subservices, EmployeeRegistration, ServiceRegistry,ServiceRequest,BookingList




admin.site.register(Register)
admin.site.register(OTP)
admin.site.register(Profile)

admin.site.register(Services)
admin.site.register(Subservices)
admin.site.register(ServiceRequest)




@admin.register(EmployeeRegistration)
class EmployeeRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'age', 'phone_number', 'created_at')
    search_fields = ('name', 'phone_number')
    list_filter = ('created_at',)


@admin.register(ServiceRegistry)
class ServiceRegistryAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'service', 'min_price', 'max_price', 'description')
    search_fields = ('employee__name', 'service__title')
    list_filter = ('service',)
    
    
    
    
@admin.register(BookingList)
class BookingListAdmin(admin.ModelAdmin):
    list_display = ('register_name', 'booking_date')

    def register_name(self, obj):
        return obj.register.name if obj.register else "No Register"
    register_name.short_description = "Register Name"
