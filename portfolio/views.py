from django.shortcuts import render

# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from .models import *
from .forms import *
from django.db.models import Sum
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomerSerializer
from django.http import HttpResponse
from django.template.loader import render_to_string, get_template
import pdfkit
from decimal import Decimal


now = timezone.now()


# home page / landing page view
def home(request):
    return render(request, 'portfolio/home.html',
                  {'portfolio': home})


# lists the customers and their details
@login_required
def customer_list(request):
    customer = Customer.objects.filter(created_date__lte=timezone.now())
    return render(request, 'portfolio/customer_list.html',
                  {'customers': customer})


# adds the customer
@login_required
def customer_new(request):
    if request.method == "POST":
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.created_date = timezone.now()
            customer.save()
            customers = Customer.objects.filter(created_date__lte=timezone.now())
            return render(request, 'portfolio/customer_list.html',
                          {'customers': customers})
    else:
        form = CustomerForm()
        # print("Else")
    return render(request, 'portfolio/customer_new.html', {'form': form})


# edit the customer
@login_required
def customer_edit(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    if request.method == "POST":
        # update
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save(commit=False)
            customer.updated_date = timezone.now()
            customer.save()
            customer = Customer.objects.filter(created_date__lte=timezone.now())
            return render(request, 'portfolio/customer_list.html',
                          {'customers': customer})
    else:
        # edit
        form = CustomerForm(instance=customer)
    return render(request, 'portfolio/customer_edit.html', {'form': form})


# deletes the customer
@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customer.delete()
    return redirect('portfolio:customer_list')


# lists the stocks
@login_required
def stock_list(request):
    stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
    return render(request, 'portfolio/stock_list.html', {'stocks': stocks})


# adds the stocks
@login_required
def stock_new(request):
    if request.method == "POST":
        form = StockForm(request.POST)
        if form.is_valid():
            stock = form.save(commit=False)
            stock.created_date = timezone.now()
            stock.save()
            stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
            return render(request, 'portfolio/stock_list.html',
                          {'stocks': stocks})
    else:
        form = StockForm()
        # print("Else")
    return render(request, 'portfolio/stock_new.html', {'form': form})


# edit the stocks
@login_required
def stock_edit(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    if request.method == "POST":
        form = StockForm(request.POST, instance=stock)
        if form.is_valid():
            stock = form.save()
            # stock.customer = stock.id
            stock.updated_date = timezone.now()
            stock.save()
            stocks = Stock.objects.filter(purchase_date__lte=timezone.now())
            return render(request, 'portfolio/stock_list.html', {'stocks': stocks})
    else:
        # print("else")
        form = StockForm(instance=stock)
    return render(request, 'portfolio/stock_edit.html', {'form': form})


# deletes the stocks
@login_required
def stock_delete(request, pk):
    stock = get_object_or_404(Stock, pk=pk)
    stock.delete()
    return redirect('portfolio:stock_list')


# investments

# list the investments
@login_required
def investment_list(request):
    investments = Investment.objects.filter(acquired_date__lte=timezone.now())
    return render(request, 'portfolio/investment_list.html', {'investments': investments})


#  adds the investments
@login_required
def investment_new(request):
    if request.method == "POST":
        form = InvestmentForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.acquired_date = timezone.now()
            investment.save()
            investments = Investment.objects.filter(acquired_date__lte=timezone.now())
            return render(request, 'portfolio/investment_list.html',
                          {'investments': investments})
    else:
        form = InvestmentForm()
        # print("Else")
    return render(request, 'portfolio/investment_new.html', {'form': form})


# edit the investments
@login_required
def investment_edit(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    if request.method == "POST":
        form = InvestmentForm(request.POST, instance=investment)
        if form.is_valid():
            investment = form.save()
            # investment.customer = investment.id
            investment.updated_date = timezone.now()
            investment.save()
            investments = Investment.objects.filter(acquired_date__lte=timezone.now())
            return render(request, 'portfolio/investment_list.html', {'investments': investments})
    else:
        # print("else")
        form = InvestmentForm(instance=investment)
    return render(request, 'portfolio/investment_edit.html', {'form': form})


# deletes the investments
@login_required
def investment_delete(request, pk):
    investment = get_object_or_404(Investment, pk=pk)
    investment.delete()
    return redirect('portfolio:investment_list')


@login_required
def portfolio(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    customers = Customer.objects.filter(created_date__lte=timezone.now())
    investments = Investment.objects.filter(customer=pk)
    funds = Fund.objects.filter(customer=pk)
    stocks = Stock.objects.filter(customer=pk)
    sum_recent_value = Investment.objects.filter(customer=pk).aggregate(Sum('recent_value'))
    sum_acquired_value = Investment.objects.filter(customer=pk).aggregate(Sum('acquired_value'))
    # overall_investment_results = sum_recent_value-sum_acquired_value
    # Initialize the value of the stocks
    sum_current_stocks_value = 0
    sum_of_initial_stock_value = 0
    sum_current_funds_value = 0
    sum_of_initial_funds_value = 0

    # Loop through each stock and add the value to the total
    for stock in stocks:
        sum_current_stocks_value += stock.current_stock_value()
        sum_of_initial_stock_value += stock.initial_stock_value()
    for fund in funds:
        sum_current_funds_value += fund.current_fund_value()
        sum_of_initial_funds_value += fund.initial_fund_value()

    labels = ['stocks', 'funds', 'investments']
    totalinv = Decimal(sum_current_stocks_value)+Decimal(sum_current_funds_value)+sum_recent_value['recent_value__sum']
    data = [int(Decimal(sum_current_stocks_value)*100/totalinv),
            int(Decimal(sum_current_funds_value)*100/totalinv),
                int(Decimal(sum_recent_value['recent_value__sum'])*100/totalinv)]

    # data = [60,10,30]
    return render(request, 'portfolio/portfolio.html', {'customer': customer,
                                                        'investments': investments,
                                                        'funds': funds,
                                                        'stocks': stocks,
                                                        'labels': labels,
                                                        'data': data,
                                                        'sum_acquired_value': sum_acquired_value,
                                                        'sum_recent_value': sum_recent_value,
                                                        'sum_current_stocks_value': sum_current_stocks_value,
                                                        'sum_of_initial_stock_value': sum_of_initial_stock_value,
                                                        'sum_current_funds_value': sum_current_funds_value,
                                                        'sum_of_initial_funds_value': sum_of_initial_funds_value, })


# Lists all customers
class CustomerList(APIView):
    def get(self, request):
        customers_json = Customer.objects.all()
        serializer = CustomerSerializer(customers_json, many=True)
        return Response(serializer.data)


# Funds


# lists the funds
@login_required
def fund_list(request):
    funds = Fund.objects.filter(purchase_date__lte=timezone.now())
    return render(request, 'portfolio/fund_list.html', {'funds': funds})


# adds the funds
@login_required
def fund_new(request):
    if request.method == "POST":
        form = FundForm(request.POST)
        if form.is_valid():
            fund = form.save(commit=False)
            fund.created_date = timezone.now()
            fund.save()
            funds = Fund.objects.filter(purchase_date__lte=timezone.now())
            return render(request, 'portfolio/fund_list.html',
                          {'funds': funds})
    else:
        form = FundForm()
        # print("Else")
    return render(request, 'portfolio/fund_new.html', {'form': form})


# edit the funds
@login_required
def fund_edit(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    if request.method == "POST":
        form = FundForm(request.POST, instance=fund)
        if form.is_valid():
            fund = form.save()
            # fund.customer = fund.id
            fund.updated_date = timezone.now()
            fund.save()
            funds = Fund.objects.filter(purchase_date__lte=timezone.now())
            return render(request, 'portfolio/fund_list.html', {'funds': funds})
    else:
        # print("else")
        form = FundForm(instance=fund)
    return render(request, 'portfolio/fund_edit.html', {'form': form})


# deletes the funds
@login_required
def fund_delete(request, pk):
    fund = get_object_or_404(Fund, pk=pk)
    fund.delete()
    return redirect('portfolio:fund_list')


@login_required
def portfolio_pdf(request, pk):
    customer = get_object_or_404(Customer, pk=pk)
    investments = Investment.objects.filter(customer=pk)
    funds = Fund.objects.filter(customer=pk)
    stocks = Stock.objects.filter(customer=pk)
    sum_recent_value = Investment.objects.filter(customer=pk).aggregate(Sum('recent_value'))
    sum_acquired_value = Investment.objects.filter(customer=pk).aggregate(Sum('acquired_value'))
    # overall_investment_results = sum_recent_value-sum_acquired_value
    # Initialize the value of the stocks
    sum_current_stocks_value = 0
    sum_of_initial_stock_value = 0
    sum_current_funds_value = 0
    sum_of_initial_funds_value = 0

    # Loop through each stock and add the value to the total
    for stock in stocks:
        sum_current_stocks_value += stock.current_stock_value()
        sum_of_initial_stock_value += stock.initial_stock_value()
    for fund in funds:
        sum_current_funds_value += fund.current_fund_value()
        sum_of_initial_funds_value += fund.initial_fund_value()
    labels = ['stocks', 'funds', 'investments']
    totalinv = Decimal(sum_current_stocks_value)+Decimal(sum_current_funds_value)+sum_recent_value['recent_value__sum']
    data = [int(Decimal(sum_current_stocks_value)*100/totalinv),
            int(Decimal(sum_current_funds_value)*100/totalinv),
                int(Decimal(sum_recent_value['recent_value__sum'])*100/totalinv)]

    template = get_template('portfolio/portfolio_pdf.html')
    html = template.render({'customer': customer,
                            'investments': investments,
                            'stocks': stocks,
                            'funds': funds,
                            'labels': labels,
                            'data': data,
                            'sum_acquired_value': sum_acquired_value,
                            'sum_recent_value': sum_recent_value,
                            'sum_current_stocks_value': sum_current_stocks_value,
                            'sum_of_initial_stock_value': sum_of_initial_stock_value,
                            'sum_current_funds_value': sum_current_funds_value,
                            'sum_of_initial_funds_value': sum_of_initial_funds_value, })
    path_wkhtmltopdf = r'.\bin\wkhtmltopdf.exe'
    config = pdfkit.configuration(wkhtmltopdf=path_wkhtmltopdf)
    options = {
        'page-size': 'Letter',
        'encoding': "UTF-8",
    }
    pdf = pdfkit.from_string(html, False, options, configuration=config)
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename=portfolio-' + str(customer.cust_number) + '.pdf'
    return response
