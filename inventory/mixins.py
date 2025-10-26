from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.http import Http404

from .services import get_user_offices


class RoleRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    required_role = None

    def test_func(self):
        if self.required_role is None:
            return True
        return self.request.user.role == self.required_role


class AdminRequiredMixin(RoleRequiredMixin):
    required_role = "admin"


class OfficeScopedMixin(LoginRequiredMixin):
    office_kwarg = "office_id"

    def get_office(self):
        office_id = self.kwargs.get(self.office_kwarg) or self.request.GET.get("office_id")
        offices = get_user_offices(self.request.user)
        if office_id:
            try:
                office = offices.get(pk=office_id)
            except offices.model.DoesNotExist as exc:  # type: ignore[attr-defined]
                raise Http404 from exc
            return office
        if self.request.user.role == self.request.user.Role.ADMIN:
            return offices.first()
        raise Http404("Office not found")
