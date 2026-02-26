from django.shortcuts import redirect
from django.urls import reverse

class SubscriptionMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:

            company = request.user.company

            if company and company.is_expired():
                if request.path not in [
                    reverse("upgrade_plan"),
                    reverse("logout"),
                ]:
                    return redirect("upgrade_plan")

        return self.get_response(request)