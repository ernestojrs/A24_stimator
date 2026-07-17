from django import forms
from django.contrib.auth.models import User

from .models import AssignmentMember, TechnicianAssigment, UserProfile


class TechnicianAssigmentForm(forms.ModelForm):
    workers = forms.ModelMultipleChoiceField(
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

        if not workers or not start_date or not end_date:
            return cleaned_data
        
        if end_date < start_date:
            raise forms.ValidationError("End date cannot be earlier than start date.")
        
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

            has_overlap = overlaps.exists()

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