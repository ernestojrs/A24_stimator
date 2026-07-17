from django.contrib import admin
from .models import UserProfile, TechnicianAssigment, AssignmentMember
from django.contrib.auth.models import User

# Register your models here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'company', 'age', 'created_at')
    search_fields = ('user__username','user__first_name', 'user__last_name', 'company', 'abilities')
    list_filter = ('role', 'company')
    ordering = ('user',)
    readonly_fields = ('created_at',)

class AssignmentMemberInline(admin.TabularInline):
    model = AssignmentMember
    extra = 1
    autocomplete_fields = ("worker",)

@admin.register(TechnicianAssigment)
class TechnicianAssigmentAdmin(admin.ModelAdmin):
    list_display = ('workers_list', 'assigned_by', 'location', 'start_date', 'end_date', 'status', 'created_at')
    search_fields = ('workers__username','workers__first_name', 'workers__last_name', 'location', 'work_description', 
                     'assigned_by__username', 'assigned_by__first_name', 'assigned_by__last_name')
    list_filter = ('status', 'start_date', 'end_date')
    ordering = ('-created_at',)
    readonly_fields = ('created_at',)

    inlines = [AssignmentMemberInline]

    def workers_list(self, obj):
        return ", ".join([worker.get_full_name() or worker.username for worker in obj.workers.all()])
    
    workers_list.short_description = 'Workers'



@admin.register(AssignmentMember)
class AssignmentMemberAdmin(admin.ModelAdmin):
    list_display = ('assignment', 'worker')
    search_fields = ('worker__username', 'worker__first_name', 'worker__last_name', 'assignment__location')

    '''def formfield_for_foreignkey(self,db_field,request,**kwargs):
        if db_field.name == "technician":
            allowed_user_ids = UserProfile.objects.filter(
                role__in=[UserProfile.ROLE_SUPERVISOR, UserProfile.ROLE_TECHNICIAN]
            ).values_list('user_id', flat=True)
            kwargs["queryset"] = User.objects.filter(id__in=allowed_user_ids)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)'''
    

