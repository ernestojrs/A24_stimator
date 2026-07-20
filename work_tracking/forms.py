from django import forms
from django.contrib.auth.models import User

from .models import AssignmentMember, TechnicianAssigment, UserProfile

class UserFullNameMultipleChoiceField(forms.ModelMultipleChoiceField):
    def label_from_instance(self,user):
        full_name = user.get_full_name()
        if full_name:
            return full_name
        
        return user.username


class TechnicianAssigmentForm(forms.ModelForm):
    workers = UserFullNameMultipleChoiceField(
        queryset=User.objects.none(),
        widget=forms.SelectMultiple(attrs={"class": "form-select"}),
        label="Workers",
    )

    class Meta:
        model = TechnicianAssigment
        fields = [
            "workers",
            "location",
            "work_description",
            "start_date",
            "end_date",
            "start_time",
            "end_time",
            "status",
        ]
        widgets = {
            "location": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "ejemplo: APAP OP",
            }),
            "work_description": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4,
                "placeholder": "Describe the work to be done...",
            }),
            "start_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "end_date": forms.DateInput(attrs={
                "type": "date",
                "class": "form-control",
            }),
            "status": forms.Select(attrs={"class": "form-select"}),

            "start_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),

             "end_time": forms.TimeInput(attrs={
                "type": "time",
                "class": "form-control"
            }),
        }

    def __init__(self, *args, current_user=None, **kwargs):
        super().__init__(*args, **kwargs)

        allowed_profiles = UserProfile.objects.filter(
            role__in=[
                UserProfile.ROLE_SUPERVISOR,
                UserProfile.ROLE_TECHNICIAN,
            ]
        )

        if current_user and hasattr(current_user, "profile"):
            if current_user.profile.is_supervisor():
                allowed_profiles = UserProfile.objects.filter(
                    role=UserProfile.ROLE_TECHNICIAN
                ) | UserProfile.objects.filter(user=current_user)

        allowed_user_ids = allowed_profiles.values_list("user_id", flat=True)

        self.fields["workers"].queryset = User.objects.filter(
            id__in=allowed_user_ids
        ).order_by(
            "first_name",
            "last_name",
            "username",
        )

        if self.instance and self.instance.pk:
            self.fields["workers"].initial = self.instance.workers.all()

    

    def clean(self):
        cleaned_data = super().clean()

        workers = cleaned_data.get("workers")
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")
        status = cleaned_data.get("status")
        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if not workers or not start_date or not end_date:
            return cleaned_data
        
        if end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date.")
        
        if bool(start_time) != bool(end_time):
            raise forms.ValidationError("Tiempo de inicio y fin deben ser colocados")
        
        if start_time and end_time and start_date == end_date and end_time <start_time:
            raise forms.ValidationError("El tiempo de fin debe ser mayor al de inicio")
        
        if status != TechnicianAssigment.STATUS_ACTIVE:
            return cleaned_data
        
        unavailable_workers = []

        for worker in workers:

            overlaps = AssignmentMember.objects.filter(
                worker = worker,
                assignment__status = TechnicianAssigment.STATUS_ACTIVE,
                assignment__start_date__lte = end_date,
                assignment__end_date__gte = start_date,
            )

            if self.instance and self.instance.pk:
                overlaps = overlaps.exclude(assignment = self.instance)

            has_overlap = False

            for member in overlaps.select_related("assignment"):
                existing = member.assignment

                existing_has_time = existing.start_time and existing.end_time
                new_has_time = start_time and end_time

                if not existing_has_time or not new_has_time:
                    has_overlap = True
                    break

                same_day = (
                    existing.start_date == existing.end_date
                    and start_date == end_date
                    and existing.start_date == existing.end_date
                )

                if not same_day:
                    has_overlap = True
                    break

                times_overlap = existing.start_time <end_time and existing.end_time >start_time

                if times_overlap:
                    has_overlap = True
                    break

            if has_overlap:
                unavailable_workers.append(worker.get_full_name() or worker.username)

        if unavailable_workers:
            names = ", ".join(unavailable_workers)
            raise forms.ValidationError(
                f"The following workers have overlapping assignments during the specified period: {names}."
            )

        return cleaned_data

    def save_members(self, assignment):
        AssignmentMember.objects.filter(assignment=assignment).delete()

        for worker in self.cleaned_data["workers"]:
            AssignmentMember.objects.create(
                assignment=assignment,
                worker=worker,
            )