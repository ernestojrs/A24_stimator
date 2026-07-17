from django.shortcuts import redirect, render
from django.contrib.auth.decorators import login_required
from .models import TechnicianAssigment, UserProfile
from .forms import TechnicianAssigmentForm
from django.contrib import messages
from django.shortcuts import get_object_or_404
import calendar
from datetime import date
from django.core.paginator import Paginator

# Create your views here.

@login_required(login_url='login')
def my_schedule_view(request):
    assignments = TechnicianAssigment.objects.filter(workers = request.user).prefetch_related("workers", "workers__profile",).select_related("assigned_by",).order_by("start_date", "end_date")
    return render(request, 'work_tracking/my_schedule.html', {'assignments': assignments})

@login_required(login_url='login')
def create_assignment_view(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, "You do not have a profile. Please contact the administrator.")
        return redirect('my_schedule')
    
    if request.user.profile.is_technician():
        messages.error(request, "Technicians cannot create assignments.")
        return redirect('my_schedule')
    
    if request.method == 'POST':
        form = TechnicianAssigmentForm(request.POST, current_user=request.user)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            form.save_members(assignment)  # Save the many-to-many relationship
            messages.success(request, "Assignment created successfully.")
            return redirect('assignment_list')
        
    else:
        form = TechnicianAssigmentForm(current_user=request.user)

    return render(request, 'work_tracking/assignment_form.html', {'form': form})

@login_required(login_url='login')
def assignment_list_view(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, "You do not have a profile. Please contact the administrator.")
        return redirect('my_schedule')
    
    if request.user.profile.is_technician():
        messages.error(request, "Technicians cannot view all assignments.")
        return redirect('my_schedule')
    
    assignments =  TechnicianAssigment.objects.prefetch_related("workers", "workers__profile").select_related("assigned_by").order_by("-start_date", "-created_at")

    summary_queryset = TechnicianAssigment.objects.all()

    summary ={
        "total": summary_queryset.count(),
        "active": summary_queryset.filter(status=TechnicianAssigment.STATUS_ACTIVE).count(),
        "completed": summary_queryset.filter(status=TechnicianAssigment.STATUS_COMPLETED).count(),
        "cancelled": summary_queryset.filter(status = TechnicianAssigment.STATUS_CANCELLED).count(),

    }

    status = request.GET.get("status","")
    worker_id=request.GET.get("worker","")
    start_date = request.GET.get("start_date","")
    end_date = request.GET.get("end_date","")

    if status:
        assignments = assignments.filter(status=status)

    if worker_id:
        assignments = assignments.filter(workers__id = worker_id)

    if start_date:
        assignments = assignments.filter(end_date__gte=start_date)

    if end_date:
        assignments = assignments.filter(start_date__lte=end_date)

    workers = UserProfile.objects.select_related("user").filter(
        role__in =[
            UserProfile.ROLE_SUPERVISOR,
            UserProfile.ROLE_TECHNICIAN
        ]
    ).order_by("user__first_name", "user__last_name", "user__username")

    paginator = Paginator(assignments,10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'work_tracking/assignment_list.html', 
                  {'assignments': page_obj,
                   'page_obj':page_obj,
                   "workers": workers,
                   "selected_status":status,
                   "selected_worker": worker_id,
                   "selected_start_date": start_date,
                   "selected_end_date": end_date,
                   "status_choices": TechnicianAssigment.STATUS_CHOICES,
                   "summary": summary,
                   })

@login_required(login_url='login')
def cancel_assignment_view(request, assignment_id):
    if not hasattr(request.user, 'profile'):
        messages.error(request, "You do not have a profile. Please contact the administrator.")
        return redirect('my_schedule')
    
    if request.user.profile.is_technician():
        messages.error(request, "Technicians cannot cancel assignments.")
        return redirect('my_schedule')
    
    assignment = get_object_or_404(TechnicianAssigment, id=assignment_id)

    if request.method == 'POST':
        assignment.status = TechnicianAssigment.STATUS_CANCELLED
        assignment.save()
        messages.success(request, "Assignment cancelled successfully.")
        return redirect('assignment_list')
    
    return render(request, 'work_tracking/cancel_assignment.html', {'assignment': assignment})

@login_required(login_url='login')
def assignment_calendar_view(request):
    if not hasattr(request.user, 'profile'):
        messages.error(request, "You do not have a profile. Please contact the administrator.")
        return redirect('my_schedule')
    

    today = date.today()
    year = int(request.GET.get('year', today.year))
    month = int(request.GET.get('month', today.month))

    status = request.GET.get("status", TechnicianAssigment.STATUS_ACTIVE)
    worker_id = request.GET.get("worker","")

    first_day = date(year, month, 1)
    last_day_number = calendar.monthrange(year, month)[1]
    last_day = date(year, month, last_day_number)

    if request.user.profile.is_technician():
        assignments = TechnicianAssigment.objects.filter(
            workers=request.user,
            start_date__lte = last_day,
            end_date__gte = first_day,
        ).prefetch_related("workers", "workers__profile")

        if status:
            assignments = assignments.filter(status=status)
    else:
       assignments = TechnicianAssigment.objects.filter(
           start_date__lte = last_day,
           end_date__gte = first_day,
       ).select_related("assigned_by",).prefetch_related("workers","workers__profile",)

       if status:
           assignments = assignments.filter(status=status)

       if worker_id:
           assignments = assignments.filter(workers__id = worker_id)
       ''' assignments = TechnicianAssigment.objects.filter(
            status=TechnicianAssigment.STATUS_ACTIVE,
            start_date__lte = last_day,
            end_date__gte = first_day,
        ).select_related('assigned_by',).prefetch_related("workers", "workers__profile")'''

    calendar_weeks = calendar.Calendar(firstweekday=6).monthdatescalendar(year, month)

    assignments_by_day = {}
    for week in calendar_weeks:
        for day in week:
            assignments_by_day[day] = []

    for assignment in assignments:
        for day in assignments_by_day:
            if assignment.start_date <= day <= assignment.end_date:
                assignments_by_day[day].append(assignment)

    previous_month = month - 1
    previous_year = year
    if previous_month == 0:
        previous_month = 12
        previous_year -= 1

    next_month = month + 1
    next_year = year

    if next_month == 13:
        next_month = 1
        next_year += 1

    workers = UserProfile.objects.select_related("user").filter(
        role__in=[
            UserProfile.ROLE_SUPERVISOR,
            UserProfile.ROLE_TECHNICIAN,
        ]
    ).order_by("user__first_name", "user__last_name", "user__username")

    return render(
        request,
        'work_tracking/assignment_calendar.html',
        {
            'calendar_weeks': calendar_weeks,
            'assignments_by_day': assignments_by_day,
            'month_name': first_day.strftime('%B'),
            'year': year,
            'month': month,
            'previous_month': previous_month,
            'previous_year': previous_year,
            'next_month': next_month,
            'next_year': next_year,
            'today': today,
            'workers': workers,
            "selected_status": status,
            "selected_worker":worker_id,
            "status_choices": TechnicianAssigment.STATUS_CHOICES,
        }
    )

@login_required(login_url='login')
def assignment_detail_view(request, assignment_id):
    assignment = get_object_or_404(
        TechnicianAssigment.objects.select_related('assigned_by',).prefetch_related("workers", "workers__profile"),
        id=assignment_id,
    )

    if not hasattr(request.user, 'profile'):
        messages.error(request, "You do not have a profile. Please contact the administrator.")
        return redirect('my_schedule')
    
    if request.user.profile.is_technician() and assignment.workers.filter(id=request.user.id).exists:
        messages.error(request, "You do not have permission to view this assignment.")
        return redirect('my_schedule')
    
    can_manage_assignment = (
        request.user.profile.is_management() or request.user.profile.is_admin()
    )
    
    return render(request, 'work_tracking/assignment_detail.html', 
                  {'assignment': assignment
                   , 'can_manage_assignment': can_manage_assignment,})

@login_required(login_url="login")
def worker_profile_detail_view(request, profile_id):
    profile = get_object_or_404(
        UserProfile.objects.select_related("user", "created_by"),
        id=profile_id
    )

    if not hasattr(request.user,"profile"):
        messages.error(request, "Your User does not have a worker profile")
        return redirect("my_schedule")

    is_own_profile = profile.user == request.user
    can_view_all_profiles = (
        request.user.profile.is_management()
        or request.user.profile.is_supervisor()
    )

    if not is_own_profile and not can_view_all_profiles:
        messages.error(request, "You do not have permission to view this profiles.")
        return redirect("my_schedule")
    assignments = TechnicianAssigment.objects.filter(
        workers = profile.user,
    ).select_related("assigned_by").prefetch_related("workers",).order_by("-start_date")

    return render(
        request,
        "work_tracking/worker_profile_detail.html",
        {
            "profile": profile,
            "assignments": assignments,
        },
    )

@login_required(login_url="login")
def worker_directory_view(request):
    if not hasattr(request.user, "profile"):
        messages.error(request, "Your user does not have a worker profile.")
        return redirect("my_schedule")
    
    if request.user.profile.is_technician():
        messages.error(request, "You do not have a permission to view the worker directory")
        return redirect("my_schedule")
    
    profiles = UserProfile.objects.select_related("user").filter(
        role__in=[
            UserProfile.ROLE_SUPERVISOR,
            UserProfile.ROLE_TECHNICIAN,
        ]
    ).order_by("role", "user__first_name", "user__last_name", "user__username")

    paginator = Paginator(profiles,9)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    return render(
        request, 
        "work_tracking/worker_directory.html",
        {
            "profiles": page_obj,
            "page_obj":page_obj,
        },
    )

@login_required(login_url='login')
def edit_assignment_view(request, assignment_id):
    if not hasattr(request.user,"profile"):
        messages.error(request,"Your user does not have a worker profile.")
        return redirect("my_schedule")
    
    if request.user.profile.is_technician():
        messages.error(request, "You do not have permission to edit assignments.")
        return redirect("my_schedule")
    
    assignment = get_object_or_404(TechnicianAssigment, id=assignment_id)

    if request.method == 'POST':
        form = TechnicianAssigmentForm(
            request.POST,
            instance = assignment,
            current_user = request.user,
        )

        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = assignment.assigned_by or request.user
            assignment.save()
            form.save_members(assignment)
            messages.success(request, "Assignment updated successfully.")
            return redirect("assignment_detail", assignment_id = assignment.id)
    else:
        form = TechnicianAssigmentForm(
            instance= assignment,
            current_user= request.user,
        )

    return render(
        request,
        "work_tracking/assignment_form.html",
        {
            "form":form,
            "is_edit":True,
            "assignment":assignment,
        },

    )


@login_required(login_url="login")
def work_tracking_dashboard_view(request):
    if not hasattr(request.user, "profile"):
        messages.error(request, "Your user does not have a worker profile")
        return redirect("my_schedule")
    
    if request.user.profile.is_technician():
        upcoming_assignments = TechnicianAssigment.objects.filter(
            workers = request.user,
            status = TechnicianAssigment.STATUS_ACTIVE,
        ).select_related("assigned_by").prefetch_related("workers",).order_by("start_date")[:5]

        summary = None

    else:

        upcoming_assignments = TechnicianAssigment.objects.filter(
            status = TechnicianAssigment.STATUS_ACTIVE
        ).select_related("assigned_by",).prefetch_related("workers",).order_by("start_date")[:5]

        summary_queryset = TechnicianAssigment.objects.all()
        summary = {
            "total" : summary_queryset.count(),
            "active" :summary_queryset.filter(status = TechnicianAssigment.STATUS_ACTIVE).count(),
            "completed" :summary_queryset.filter(status = TechnicianAssigment.STATUS_COMPLETED).count(),
            "cancelled" :summary_queryset.filter(status = TechnicianAssigment.STATUS_CANCELLED).count(),
        }

    return render(
        request,
        "work_tracking/dashboard.html",
        {
            "summary": summary,
            "upcoming_assignments": upcoming_assignments,
        }
    )

@login_required(login_url='login')
def complete_assignment_view(request, assignment_id):
    if not hasattr(request.user,"profile"):
        messages.error(request, "Your user does not have a worker profile")
        return redirect("my_schedule")
    
    if request.user.profile.is_technician():
        messages.error(request, "You do not have a permission to complete assignments.")
        return redirect("my_schedule")
    
    assignment = get_object_or_404(TechnicianAssigment, id=assignment_id)

    if request.method == "POST":
        assignment.status = TechnicianAssigment.STATUS_COMPLETED
        assignment.save()
        messages.success(request, "La asignacion fue completada")
        return redirect("assignment_list")
    
    return render(
        request,
        "work_tracking/complete_assignment.html",
        {
            "assignment": assignment,
        }
    )


   