import csv
from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import ListView, TemplateView, UpdateView, View

from .forms import (
    LotForm,
    MedicationForm,
    MembershipForm,
    OfficeForm,
    OfficeMedicationForm,
    UserForm,
)
from .mixins import AdminRequiredMixin
from .models import AuditLog, Lot, Medication, Office, OfficeMedication, OfficeMembership
from .services import (
    default_expiry_days,
    get_user_offices,
    inventory_summary,
    lots_expired,
    lots_expiring_within,
    next_expiring_lots,
)

User = get_user_model()


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = "dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        offices = get_user_offices(self.request.user)
        context["offices"] = offices
        context["expiring_sets"] = next_expiring_lots(offices=offices)
        context["expired_lots"] = lots_expired(offices)
        context["default_days"] = default_expiry_days()
        needs_attention = set()
        for days, qs in context["expiring_sets"].items():
            for lot in qs:
                needs_attention.add(lot.office_medication.office)
        context["attention_offices"] = needs_attention
        return context


class OfficeListView(LoginRequiredMixin, ListView):
    template_name = "offices/list.html"
    model = Office
    context_object_name = "offices"

    def get_queryset(self):
        user = self.request.user
        if user.role == user.Role.ADMIN:
            return Office.objects.filter(is_active=True)
        return get_user_offices(user)


class OfficeCreateView(AdminRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        form = OfficeForm(request.POST)
        if form.is_valid():
            office = form.save(commit=False)
            if office.is_active is False:
                office.is_active = True
            office.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, office)
            messages.success(request, "Office created")
        else:
            messages.error(request, "Unable to create office")
        return redirect("offices")


class OfficeUpdateView(AdminRequiredMixin, UpdateView):
    model = Office
    form_class = OfficeForm
    template_name = "offices/office_form.html"

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.log(self.request.user, AuditLog.Action.UPDATE, self.object)
        messages.success(self.request, "Office updated")
        return response

    def get_success_url(self):
        return reverse("office-detail", args=[self.object.pk])


class OfficeDetailView(LoginRequiredMixin, TemplateView):
    template_name = "offices/detail.html"

    def dispatch(self, request, *args, **kwargs):
        self.office = get_object_or_404(Office, pk=kwargs["pk"], is_active=True)
        if request.user.role != request.user.Role.ADMIN and not OfficeMembership.objects.filter(
            office=self.office, user=request.user, is_active=True
        ).exists():
            messages.error(request, "You do not have access to this office")
            return redirect("offices")
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        tab = self.request.GET.get("tab", "stock")
        context.update(
            {
                "office": self.office,
                "tab": tab,
                "stock_list": self.office.office_medications.filter(is_active=True).select_related("medication"),
                "lot_list": Lot.objects.filter(office_medication__office=self.office, is_active=True)
                .select_related("office_medication__medication")
                .order_by("exp_date"),
                "expiring_lots": lots_expiring_within(default_expiry_days(), office=self.office),
                "expired_lots": lots_expired(office=self.office),
                "default_days": default_expiry_days(),
                "office_med_form": self._office_med_form(),
                "lot_form": self._lot_form(),
            }
        )
        return context

    def _office_med_form(self):
        form = OfficeMedicationForm(initial={"office": self.office})
        form.fields["office"].queryset = Office.objects.filter(pk=self.office.pk)
        form.fields["medication"].queryset = Medication.objects.filter(is_active=True)
        return form

    def _lot_form(self):
        form = LotForm()
        form.fields["office_medication"].queryset = self.office.office_medications.filter(is_active=True)
        return form


class OfficeMedicationCreateView(AdminRequiredMixin, View):
    def post(self, request, pk):
        office = get_object_or_404(Office, pk=pk, is_active=True)
        form = OfficeMedicationForm(request.POST)
        form.fields["office"].queryset = Office.objects.filter(pk=office.pk)
        form.fields["medication"].queryset = Medication.objects.filter(is_active=True)
        if form.is_valid():
            office_med = form.save(commit=False)
            office_med.office = office
            office_med.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, office_med)
            messages.success(request, "Medication added to office")
        else:
            messages.error(request, "Could not add medication")
        return redirect(reverse("office-detail", args=[pk]) + "?tab=stock")


class OfficeMedicationUpdateView(AdminRequiredMixin, UpdateView):
    model = OfficeMedication
    form_class = OfficeMedicationForm
    template_name = "offices/office_medication_form.html"

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["office"].queryset = Office.objects.filter(pk=self.object.office_id)
        form.fields["medication"].queryset = Medication.objects.filter(is_active=True)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.log(self.request.user, AuditLog.Action.UPDATE, self.object)
        messages.success(self.request, "Office medication updated")
        return response

    def get_success_url(self):
        return reverse("office-detail", args=[self.object.office_id]) + "?tab=stock"


class LotCreateView(LoginRequiredMixin, View):
    def post(self, request, pk):
        office = get_object_or_404(Office, pk=pk, is_active=True)
        if request.user.role != request.user.Role.ADMIN and not OfficeMembership.objects.filter(
            office=office, user=request.user, is_active=True
        ).exists():
            messages.error(request, "You do not have access to this office")
            return redirect("offices")
        form = LotForm(request.POST)
        form.fields["office_medication"].queryset = office.office_medications.filter(is_active=True)
        if form.is_valid():
            lot = form.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, lot)
            messages.success(request, "Lot saved")
        else:
            messages.error(request, "Unable to save lot")
        return redirect(reverse("office-detail", args=[pk]) + "?tab=lots")


class LotUpdateView(LoginRequiredMixin, UpdateView):
    model = Lot
    form_class = LotForm
    template_name = "offices/lot_form.html"

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        office = self.object.office_medication.office
        if request.user.role != request.user.Role.ADMIN and not OfficeMembership.objects.filter(
            office=office, user=request.user, is_active=True
        ).exists():
            messages.error(request, "You do not have access to this lot")
            return redirect("offices")
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        office = self.object.office_medication.office
        form.fields["office_medication"].queryset = office.office_medications.filter(is_active=True)
        return form

    def form_valid(self, form):
        response = super().form_valid(form)
        AuditLog.log(self.request.user, AuditLog.Action.UPDATE, self.object)
        messages.success(self.request, "Lot updated")
        return response

    def get_success_url(self):
        return reverse("office-detail", args=[self.object.office_medication.office_id]) + "?tab=lots"


class OfficeExpirationsExportView(LoginRequiredMixin, View):
    def get(self, request, pk):
        office = get_object_or_404(Office, pk=pk, is_active=True)
        if request.user.role != request.user.Role.ADMIN and not OfficeMembership.objects.filter(
            office=office, user=request.user, is_active=True
        ).exists():
            return HttpResponse(status=403)
        days = int(request.GET.get("days", default_expiry_days()))
        lots = lots_expiring_within(days, office=office)
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(["Medication", "Lot", "Quantity", "Expiration Date"])
        for lot in lots:
            writer.writerow(
                [
                    lot.office_medication.medication.generic_name,
                    lot.lot_number,
                    lot.qty,
                    lot.exp_date,
                ]
            )
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = f"attachment; filename=expiring_{office.pk}.csv"
        AuditLog.log(request.user, AuditLog.Action.EXPORT, office, {"type": "expiring_csv"})
        return response


class MedicationListView(AdminRequiredMixin, ListView):
    template_name = "medications/list.html"
    model = Medication
    context_object_name = "medications"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = MedicationForm()
        return context


class MedicationCreateView(AdminRequiredMixin, View):
    def post(self, request):
        form = MedicationForm(request.POST)
        if form.is_valid():
            medication = form.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, medication)
            messages.success(request, "Medication added")
        else:
            messages.error(request, "Could not add medication")
        return redirect("medications")


class UserListView(AdminRequiredMixin, ListView):
    template_name = "users/list.html"
    model = User
    context_object_name = "users"

    def get_queryset(self):
        return User.objects.all().prefetch_related("memberships__office")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = UserForm()
        context["membership_form"] = MembershipForm()
        context["offices"] = Office.objects.filter(is_active=True)
        return context


class UserCreateView(AdminRequiredMixin, View):
    def post(self, request):
        form = UserForm(request.POST)
        password = request.POST.get("password") or User.objects.make_random_password()
        if form.is_valid():
            user = form.save(commit=False)
            if not user.username:
                user.username = user.email
            if user.role == User.Role.ADMIN:
                user.is_staff = True
                user.is_superuser = True
            user.is_active = True
            user.set_password(password)
            user.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, user)
            messages.success(request, "User created")
        else:
            messages.error(request, "Could not create user")
        return redirect("users")


class MembershipCreateView(AdminRequiredMixin, View):
    def post(self, request):
        form = MembershipForm(request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            if membership.is_active is False:
                membership.is_active = True
            membership.save()
            AuditLog.log(request.user, AuditLog.Action.CREATE, membership)
            messages.success(request, "Membership saved")
        else:
            messages.error(request, "Could not save membership")
        return redirect("users")


class ReportsView(LoginRequiredMixin, TemplateView):
    template_name = "reports/index.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        days = int(self.request.GET.get("days", default_expiry_days()))
        office_id = self.request.GET.get("office_id")
        office = None
        offices = get_user_offices(self.request.user)
        if office_id:
            office = get_object_or_404(Office, pk=office_id, is_active=True)
            if self.request.user.role != self.request.user.Role.ADMIN and not offices.filter(pk=office.pk).exists():
                office = None
        context.update(
            {
                "offices": offices,
                "days": days,
                "expiring": lots_expiring_within(days, office=office or offices),
                "expired": lots_expired(office=office or offices),
                "inventory": inventory_summary(offices),
            }
        )
        return context
