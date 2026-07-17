from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    ROLE_MANAGEMENT = 'management'
    ROLE_SUPERVISOR = 'supervisor'
    ROLE_TECHNICIAN = 'technician'

    ROLE_CHOICES = [
        (ROLE_MANAGEMENT, 'Management'),
        (ROLE_SUPERVISOR, 'Supervisor'),
        (ROLE_TECHNICIAN, 'Technician'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_TECHNICIAN)

    age = models.PositiveIntegerField(null=True, blank=True)
    company = models.CharField(max_length=150, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    abilities = models.TextField(null=True, blank=True)

    created_by = models.ForeignKey(User, on_delete=models.PROTECT, null=True, blank=True, 
                                   related_name='created_worker_profiles')
    
    created_at = models.DateTimeField(auto_now_add=True)

    def is_management(self):
        return self.role == self.ROLE_MANAGEMENT
    def is_supervisor(self):
        return self.role == self.ROLE_SUPERVISOR
    def is_technician(self):
        return self.role == self.ROLE_TECHNICIAN

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} - {self.get_role_display()}"

class TechnicianAssigment(models.Model):
    STATUS_ACTIVE = 'active'
    STATUS_CANCELLED = 'cancelled'
    STATUS_COMPLETED = 'completed'

    STATUS_CHOICES = [
        (STATUS_ACTIVE, 'Active'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_COMPLETED, 'Completed'),  
    ]



    workers = models.ManyToManyField(User, through='AssignmentMember', related_name='work_assignments')
    assigned_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_technician_assigments')
    location = models.CharField(max_length=255)
    work_description = models.TextField(blank=True, null=True)
    start_date = models.DateField()
    end_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        '''if self.end_date < self.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        if not hasattr(self.technician, 'profile'):
            raise ValidationError("The selected technician does not have a profile.")
        if self.technician.profile.role == UserProfile.ROLE_MANAGEMENT:
            raise ValidationError("management users cannot be scheduled")
        
        overlapping_assignments = TechnicianAssigment.objects.filter(
            technician=self.technician,
            status=self.STATUS_ACTIVE,
            start_date__lte=self.end_date,
            end_date__gte=self.start_date
        )

        if self.pk:
            overlapping_assignments = overlapping_assignments.exclude(pk=self.pk)

        if overlapping_assignments.exists():
            raise ValidationError("This worker has overlapping assignments during the specified period.")'''
        
    def save(self, *args, **kwargs):
        self.full_clean()  # This will call the clean method
        super().save(*args, **kwargs)   

    def __str__(self):
        return f"{self.location} - {self.start_date} to {self.end_date}"
        

class AssignmentMember(models.Model):
    assignment = models.ForeignKey(TechnicianAssigment, on_delete=models.CASCADE, related_name='assignment_members')
    worker = models.ForeignKey(User, on_delete=models.PROTECT, related_name='assignment_memberships')

    class Meta:
        unique_together = ('assignment', 'worker')

    def clean(self):
        from django.core.exceptions import ValidationError

        if not hasattr(self.worker, 'profile'):
            raise ValidationError("The selected worker does not have a profile.")
        
        if self.worker.profile.role == UserProfile.ROLE_MANAGEMENT:
            raise ValidationError("Management users cannot be assigned to assignments.")
        
        if self.assignment.end_date < self.assignment.start_date:
            raise ValidationError("End date cannot be earlier than start date.")
        
        overlapping_assignments = AssignmentMember.objects.filter(
            worker=self.worker,
            assignment__status=TechnicianAssigment.STATUS_ACTIVE,
            assignment__start_date__lte=self.assignment.end_date,
            assignment__end_date__gte=self.assignment.start_date
        )

        if self.pk:
            overlapping_assignments = overlapping_assignments.exclude(pk=self.pk)

        if self.assignment_id:
            overlapping_assignments = overlapping_assignments.exclude(assignment_id=self.assignment_id)

        if overlapping_assignments.exists():
            raise ValidationError("This worker has overlapping assignments during the specified period.")
        
    def save(self, *args, **kwargs):
        self.full_clean()  # This will call the clean method
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.worker.get_full_name() or self.worker.username} assigned to {self.assignment}"
        
