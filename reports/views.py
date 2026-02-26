from datetime import date, datetime, timedelta
from collections import defaultdict
from django.db.models import Sum
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from expenses.models import Expense
from invoices.models import Invoice


@login_required
def reports(request):

    user = request.user
    company = user.company

    # ==============================
    # DATE RANGE
    # ==============================

    start = request.GET.get("start")
    end = request.GET.get("end")

    if start:
        start_date = datetime.strptime(start, "%Y-%m-%d").date()
    else:
        start_date = date.today().replace(day=1)

    if end:
        end_date = datetime.strptime(end, "%Y-%m-%d").date()
    else:
        end_date = date.today()

    # ==============================
    # ROLE-BASED QUERYSETS
    # ==============================

    if user.role in ["admin", "superadmin"]:
        expenses_qs = Expense.objects.filter(
            company=company,
            created_at__date__range=(start_date, end_date)
        )
        invoices_qs = Invoice.objects.filter(
            company=company,
            date__range=(start_date, end_date)
        )

    elif user.role == "accountant":
        expenses_qs = Expense.objects.filter(
            company=company,
            created_at__date__range=(start_date, end_date)
        )
        invoices_qs = Invoice.objects.filter(
            company=company,
            status__in=["approved", "paid"],
            date__range=(start_date, end_date)
        )

    else:  # employee
        expenses_qs = Expense.objects.filter(
            company=company,
            user=user,
            created_at__date__range=(start_date, end_date)
        )
        invoices_qs = Invoice.objects.filter(
            company=company,
            user=user,
            date__range=(start_date, end_date)
        )

    # ==============================
    # TOTALS
    # ==============================

    total_expenses = float(expenses_qs.aggregate(
        total=Sum("amount")
    )["total"] or 0)

    total_invoices = float(invoices_qs.aggregate(
        total=Sum("total_amount")
    )["total"] or 0)

    net_balance = total_invoices - total_expenses

    # ==============================
    # DAILY DATA
    # ==============================

    day_range = (end_date - start_date).days + 1
    labels = []
    invoice_data = []
    expense_data = []

    invoices_by_day = defaultdict(float)
    expenses_by_day = defaultdict(float)

    for inv in invoices_qs:
        invoices_by_day[inv.date] += float(inv.total_amount)

    for e in expenses_qs:
        expenses_by_day[e.created_at.date()] += float(e.amount)

    for i in range(day_range):
        day = start_date + timedelta(days=i)
        labels.append(day.strftime("%Y-%m-%d"))
        invoice_data.append(invoices_by_day.get(day, 0.0))
        expense_data.append(expenses_by_day.get(day, 0.0))

    # ==============================
    # MONTHLY DATA
    # ==============================

    monthly_invoice = defaultdict(float)
    monthly_expense = defaultdict(float)

    for inv in invoices_qs:
        key = date(inv.date.year, inv.date.month, 1)
        monthly_invoice[key] += float(inv.total_amount)

    for e in expenses_qs:
        key = date(e.created_at.year, e.created_at.month, 1)
        monthly_expense[key] += float(e.amount)

    months_sorted = sorted(set(list(monthly_invoice.keys()) + list(monthly_expense.keys())))
    month_labels = [m.strftime("%b %Y") for m in months_sorted]
    month_invoice_data = [monthly_invoice.get(m, 0.0) for m in months_sorted]
    month_expense_data = [monthly_expense.get(m, 0.0) for m in months_sorted]

    # ==============================
    # CATEGORY TOTALS
    # ==============================

    business_total = 0
    personal_total = 0
    others_total = 0

    for e in expenses_qs:
        cat = (e.category or "").strip().lower()
        if cat == "business":
            business_total += float(e.amount)
        elif cat == "personal":
            personal_total += float(e.amount)
        else:
            others_total += float(e.amount)

    category_labels = ["Business", "Personal", "Others"]
    category_values = [business_total, personal_total, others_total]

    # ==============================
    # OTHER METRICS
    # ==============================

    avg_invoice_per_day = (total_invoices / day_range) if day_range else 0
    avg_expense_per_day = (total_expenses / day_range) if day_range else 0

    cat_totals = expenses_qs.values("category").annotate(
        total=Sum("amount")
    ).order_by("-total")

    biggest_expense_category = cat_totals[0]["category"] if cat_totals else None

    best_date = None
    if invoices_by_day:
        best_date = max(invoices_by_day.items(), key=lambda x: x[1])[0].strftime("%Y-%m-%d")

    # ==============================
    # COMBINED TABLE
    # ==============================

    combined = []

    for e in expenses_qs:
        combined.append({
            "date": e.created_at.date(),
            "type": "Expense",
            "title": e.title,
            "category_or_vendor": e.category,
            "payment_method": e.payment_method,
            "status": e.status,
            "amount": float(e.amount),
        })

    for inv in invoices_qs:
        combined.append({
            "date": inv.date,
            "type": "Invoice",
            "title": inv.invoice_number,
            "category_or_vendor": inv.vendor.name if inv.vendor else "-",
            "payment_method": inv.payment_method,
            "status": inv.status,
            "amount": float(inv.total_amount),
            "tax": float(inv.tax_amount or 0),
        })

    combined = sorted(combined, key=lambda x: x["date"], reverse=True)

    # ==============================
    # CONTEXT
    # ==============================

    context = {
        "start": start,
        "end": end,
        "total_expenses": total_expenses,
        "total_invoices": total_invoices,
        "net_balance": net_balance,
        "labels": labels,
        "invoice_data": invoice_data,
        "expense_data": expense_data,
        "month_labels": month_labels,
        "month_invoice_data": month_invoice_data,
        "month_expense_data": month_expense_data,
        "category_labels": category_labels,
        "category_values": category_values,
        "combined": combined,
        "avg_invoice_per_day": round(avg_invoice_per_day, 2),
        "avg_expense_per_day": round(avg_expense_per_day, 2),
        "biggest_expense_category": biggest_expense_category,
        "best_date": best_date,
    }

    return render(request, "reports/reports.html", context)