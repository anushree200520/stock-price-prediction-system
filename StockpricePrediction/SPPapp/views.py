import os
import csv
import joblib
import requests
from datetime import datetime
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import authenticate, login, logout as auth_logout
from .models import StockPrediction
from .forms import StockPredictionForm, UserRegistrationForm, UserLoginForm


# =========================
# HOME VIEW
# =========================
def home(request):
    return render(request, 'home.html')


# =========================
# CSV LOADER
# =========================
def get_stock_history(company_name):
    csv_file_path = os.path.join(settings.BASE_DIR, f'{company_name.upper()}.csv')

    dates, prices, volumes, high_prices, low_prices = [], [], [], [], []

    with open(csv_file_path, 'r', encoding='utf-8') as csvfile:

        company = company_name.lower()

        if company == 'facebook':
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    parsed_date = datetime.strptime(row['Date'], "%Y-%m-%d")
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
                    prices.append(float(row['Close']))
                    volumes.append(float(row['Volume']))
                    high_prices.append(float(row['High']))
                    low_prices.append(float(row['Low']))
                except:
                    continue

        elif company == 'google':
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    date_val = row['Date'].split()[0]
                    parsed_date = datetime.strptime(date_val, "%Y-%m-%d")
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
                    prices.append(float(row['Close']))
                    volumes.append(float(row['Volume']))
                    high_prices.append(float(row['High']))
                    low_prices.append(float(row['Low']))
                except:
                    continue

        elif company == 'microsoft':
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    date_val = row['Date'].split()[0]
                    parsed_date = datetime.strptime(date_val, "%m/%d/%Y")
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
                    prices.append(float(row['Close']))
                    volumes.append(float(row['Volume']))
                    high_prices.append(float(row['High']))
                    low_prices.append(float(row['Low']))
                except:
                    continue

        else:
            reader = csv.DictReader(csvfile)
            for row in reader:
                try:
                    parsed_date = datetime.strptime(row['Date'], "%Y-%m-%d")
                    dates.append(parsed_date.strftime("%Y-%m-%d"))
                    prices.append(float(row['Close']))
                    volumes.append(float(row['Volume']))
                    high_prices.append(float(row['High']))
                    low_prices.append(float(row['Low']))
                except:
                    continue

    return dates, prices, volumes, high_prices, low_prices


# =========================
# REAL-TIME STOCK API
# =========================
def get_live_stock_data(company_name):
    company_symbols = {
        'amazon': 'AMZN',
        'apple': 'AAPL',
        'facebook': 'META',
        'google': 'GOOGL',
        'microsoft': 'MSFT',
    }

    symbol = company_symbols.get(company_name.lower())

    if not symbol:
        return None

    # ✅ Add this in settings.py:
    # FINNHUB_API_KEY = "your_api_key_here"
    api_key = getattr(settings, 'FINNHUB_API_KEY', None)

    if not api_key:
        return {
            'symbol': symbol,
            'current_price': None,
            'open_price': None,
            'high_price': None,
            'low_price': None,
            'previous_close': None,
            'change': None,
            'change_percent': None,
            'error': 'API key not configured'
        }

    url = f"https://finnhub.io/api/v1/quote?symbol={symbol}&token={api_key}"

    try:
        response = requests.get(url, timeout=5)
        data = response.json()

        current_price = data.get('c')
        previous_close = data.get('pc')

        change = None
        change_percent = None

        if current_price and previous_close:
            change = current_price - previous_close
            change_percent = (change / previous_close) * 100

        return {
            'symbol': symbol,
            'current_price': current_price,
            'open_price': data.get('o'),
            'high_price': data.get('h'),
            'low_price': data.get('l'),
            'previous_close': previous_close,
            'change': change,
            'change_percent': change_percent,
            'error': None
        }

    except Exception:
        return {
            'symbol': symbol,
            'current_price': None,
            'open_price': None,
            'high_price': None,
            'low_price': None,
            'previous_close': None,
            'change': None,
            'change_percent': None,
            'error': 'Unable to fetch live stock data'
        }


# =========================
# API
# =========================
@login_required
def company_history(request, company_name):
    dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)

    return JsonResponse({
        'dates': dates,
        'prices': prices,
        'volumes': volumes,
        'high_prices': high_prices,
        'low_prices': low_prices,
    })


# =========================
# PREDICTION
# =========================
def get_prediction(form_data, company_name):
    model_path = os.path.join(settings.BASE_DIR, 'models', f'{company_name.lower()}.pkl')

    with open(model_path, 'rb') as model_file:
        model = joblib.load(model_file)

    input_data = [[
        form_data['open_price'],
        form_data['high_price'],
        form_data['low_price'],
        form_data['volume']
    ]]

    return model.predict(input_data)[0]


# =========================
# PREDICTION PAGE
# =========================
@login_required
def predict(request, company_name):
    prediction = None

    dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)

    dates = dates[-50:]
    prices = prices[-50:]
    volumes = volumes[-50:]
    high_prices = high_prices[-50:]
    low_prices = low_prices[-50:]

    live_data = get_live_stock_data(company_name)

    if request.method == 'POST':
        form = StockPredictionForm(request.POST)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.user = request.user
            obj.company = company_name
            obj.predicted_price = get_prediction(form.cleaned_data, company_name)
            obj.save()

            prediction = obj.predicted_price

            return render(request, 'result.html', {
                'company': company_name,
                'prediction': prediction,
                'dates': dates,
                'prices': prices,
                'volumes': volumes,
                'high_prices': high_prices,
                'low_prices': low_prices,
                'live_data': live_data,
            })

    else:
        form = StockPredictionForm()

    return render(request, f'{company_name.lower()}.html', {
        'form': form,
        'company': company_name,
        'prediction': prediction,
        'dates': dates,
        'prices': prices,
        'volumes': volumes,
        'high_prices': high_prices,
        'low_prices': low_prices,
        'live_data': live_data,
    })


# =========================
# HISTORY
# =========================
def history(request):
    company_names = ['amazon', 'apple', 'facebook', 'google', 'microsoft']

    selected_year = request.GET.get('year')
    selected_company = request.GET.get('company')

    all_company_data = {'companies': []}

    for company_name in company_names:

        if selected_company and company_name.upper() != selected_company.upper():
            continue

        try:
            dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)

            if not dates:
                continue

            years = [datetime.strptime(d, "%Y-%m-%d").year for d in dates]

            min_year = min(years)
            max_year = max(years)

            company_error = None

            if selected_year:
                try:
                    year_int = int(selected_year)
                except:
                    company_error = "Invalid year format"
                    year_int = None

                if year_int:
                    if year_int < min_year or year_int > max_year:
                        company_error = f"Data available only from {min_year} to {max_year}"
                        dates, prices, volumes, high_prices, low_prices = [], [], [], [], []
                    else:
                        filtered = [
                            (d, p, v, h, l)
                            for d, p, v, h, l in zip(dates, prices, volumes, high_prices, low_prices)
                            if datetime.strptime(d, "%Y-%m-%d").year == year_int
                        ]

                        if filtered:
                            dates, prices, volumes, high_prices, low_prices = zip(*filtered)
                            dates = list(dates)
                            prices = list(prices)
                            volumes = list(volumes)
                            high_prices = list(high_prices)
                            low_prices = list(low_prices)
                        else:
                            company_error = f"No data found for {selected_year}"
                            dates, prices, volumes, high_prices, low_prices = [], [], [], [], []

            MAX_POINTS = 150

            dates = dates[-MAX_POINTS:]
            prices = prices[-MAX_POINTS:]
            volumes = volumes[-MAX_POINTS:]
            high_prices = high_prices[-MAX_POINTS:]
            low_prices = low_prices[-MAX_POINTS:]

            all_company_data['companies'].append({
                'name': company_name,
                'dates': dates,
                'prices': prices,
                'volumes': volumes,
                'high_prices': high_prices,
                'low_prices': low_prices,
                'error': company_error,
                'min_year': min_year,
                'max_year': max_year
            })

        except FileNotFoundError:
            continue

    return render(request, 'history.html', {
        'company_data': all_company_data
    })


# =========================
# AUTH FUNCTIONSz
# =========================
@login_required
def old_predictions(request):
    predictions = StockPrediction.objects.filter(user=request.user).order_by('date')
    return render(request, 'old_predictions.html', {'old_predictions': predictions})


@login_required
def edit_prediction(request, pk):
    prediction = get_object_or_404(StockPrediction, pk=pk, user=request.user)

    if request.method == 'POST':
        form = StockPredictionForm(request.POST, instance=prediction)

        if form.is_valid():
            obj = form.save(commit=False)
            obj.predicted_price = get_prediction(form.cleaned_data, obj.company)
            obj.save()

            return redirect('old_predictions')

    else:
        form = StockPredictionForm(instance=prediction)

    return render(request, 'edit_prediction.html', {'form': form})


@login_required
def delete_prediction(request, pk):
    prediction = get_object_or_404(StockPrediction, pk=pk, user=request.user)

    if request.method == 'POST':
        prediction.delete()
        return redirect('old_predictions')

    return redirect('old_predictions')


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            form.save()

            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password1']
            )

            login(request, user)

            return redirect(home)

    else:
        form = UserRegistrationForm()

    return render(request, 'register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)

        if form.is_valid():
            user = authenticate(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )

            if user:
                login(request, user)
                return redirect(home)
            else:
                form.add_error(None, 'Invalid username or password')

    else:
        form = UserLoginForm()

    return render(request, 'login.html', {'form': form})


def logout_view(request):
    auth_logout(request)
    return redirect('home')