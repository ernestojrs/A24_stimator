from zoneinfo import ZoneInfo,ZoneInfoNotFoundError
from django.utils import timezone

class UserTimezoneMiddleware:
    def __init__(self,get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and hasattr(request.user,"profile"):
            user_timezone = request.user.profile.timezone

            try:
                timezone.activate(ZoneInfo(user_timezone))
            except ZoneInfoNotFoundError:
                timezone.deactivate()

        else:
            timezone.deactivate()

        response = self.get_response(request) 

        return response