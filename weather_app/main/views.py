from django.shortcuts import render, redirect
import requests
import openmeteo_requests
import requests_cache
import pandas as pd
from retry_requests import retry
import numpy as np
from .forms import RegistrationForm
from .models import CityHistory
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import CityHistorySerializer
from django.db.models import Count



def current_weather_encode(code):
    if code == 0:
        encode = "Ясно"
    elif code in [1, 2, 3]:
        encode = "Преимущественно ясно"
    elif code in [45, 48]:
        encode = "Туман"
    elif code in [51, 53, 55]:
        encode = "Морось"
    elif code in [56, 57]:
        encode = "Ледяная морось"
    elif code in [61, 63, 65]:
        encode = "Дождь"
    elif code in [66, 67]:
        encode = "Ледяной дождь"
    elif code in [71, 73, 75]:
        encode = "Снегопад"
    elif code in [77]:
        encode = "Снежные зерна"
    elif code in [80, 81, 82]:
        encode = "Ливень"
    elif code in [85, 86]:
        encode = "Снежный ливень"
    elif code in [95, 97, 98, 96, 99]:
        encode = "Гроза"
    else:
        encode = "Код погоды не известен"
    return encode


def precipitation_encode(code):
    if code == 0:
        encode = "нет осадков"
    elif 0 < code < 5:
        encode = "небольшие осадки"
    elif 5 <= code < 20:
        encode = "умеренные осадки"
    elif code >= 20:
        encode = "сильные осадки"
    else:
        encode = "осадки не известны"
    return encode


def encoding_wind_degrees(degrees):
    directions = {
        0: "север",
        45: "северо-восток",
        90: "восток",
        135: "юго-восток",
        180: "юг",
        225: "юго-запад",
        270: "запад",
        315: "северо-запад",
    }
    closest_direction = min(directions.keys(), key=lambda x: abs(x - degrees))
    return directions[closest_direction]


def get_weather(location_name):
    api_url_geocode = "https://geocoding-api.open-meteo.com/v1/search"
    params_geocode = {"name": location_name, "count": 1, "format": "json"}

    geo_response = requests.get(api_url_geocode, params=params_geocode)
    geo_data = geo_response.json()

    if "results" in geo_data:
        result = geo_data["results"][0]
        latitude = result["latitude"]
        longitude = result["longitude"]

        api_url_weather = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "current": [
                "temperature_2m",
                "precipitation",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ],
            "hourly": [
                "temperature_2m",
                "precipitation_probability",
                "weather_code",
                "wind_speed_10m",
                "wind_direction_10m",
            ],
            "timezone": "Europe/Moscow",
            "wind_speed_unit": "ms",
            "forecast_hours": 24,
        }
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        retry_session = retry(cache_session, retries=5, backoff_factor=0.2)
        openmeteo = openmeteo_requests.Client(session=retry_session)
        weather_response = openmeteo.weather_api(api_url_weather, params=params)
        weather_response = weather_response[0]

        current_weather = weather_response.Current()
        current_temperature_2m = round(current_weather.Variables(0).Value())

        precipitation_code = current_weather.Variables(1).Value()

        current_precipitation = precipitation_encode(precipitation_code)

        current_wind_speed_10m = round(current_weather.Variables(3).Value())

        wind_degrees = round(current_weather.Variables(4).Value())
        current_wind_direction_10m = encoding_wind_degrees(wind_degrees)

        current_weather_code = current_weather.Variables(2).Value()
        weather_from_code = current_weather_encode(current_weather_code)

        hourly = weather_response.Hourly()
        hourly_temperature_2m = hourly.Variables(0).ValuesAsNumpy().astype(int)
        hourly_precipitation_probability = hourly.Variables(1).ValuesAsNumpy()
        vectorized_encode = np.vectorize(precipitation_encode)
        encoded_precipitation = vectorized_encode(hourly_precipitation_probability)
        hourly_weather_code = hourly.Variables(2).ValuesAsNumpy()
        vectorized_weather_encode = np.vectorize(current_weather_encode)
        encoded_weather_code = vectorized_weather_encode(hourly_weather_code)
        hourly_wind_speed_10m = hourly.Variables(3).ValuesAsNumpy()
        hourly_wind_direction_10m = hourly.Variables(4).ValuesAsNumpy()

        hourly_data = {
            "date": pd.date_range(
                start=pd.to_datetime(hourly.Time(), unit="s", utc=True),
                end=pd.to_datetime(hourly.TimeEnd(), unit="s", utc=True),
                freq=pd.Timedelta(seconds=hourly.Interval()),
                inclusive="left",
            )
        }
        hourly_data["temperature_2m"] = hourly_temperature_2m
        hourly_data["precipitation_probability"] = encoded_precipitation
        hourly_data["weather_code"] = encoded_weather_code
        hourly_data["wind_speed_10m"] = hourly_wind_speed_10m
        hourly_data["wind_direction_10m"] = hourly_wind_direction_10m

        hourly_dataframe = pd.DataFrame(data=hourly_data)

        return (
            current_precipitation,
            current_temperature_2m,
            current_wind_speed_10m,
            current_wind_direction_10m,
            weather_from_code,
            hourly_dataframe,
        )
    else:
        print("Что-то пошло не так!")
        return None


def main_page(request):
    cities_cookie = request.COOKIES.get("last_cities", "")
    cities_list = cities_cookie.split(",") if cities_cookie else []
    cookie_exists = 'last_cities' in request.COOKIES
    return render(
        request, "main.html", {"page": "main-page", "cities_list": cities_list, "cookie_exists": cookie_exists}
    )


from transliterate import translit


def wheather_page(request):
    if request.method == "POST":
        city = request.POST.get("city")
        if city == "Москва":
            city = "Moscow"
        elif city == "Санкт-Петербург":
            city = "St Peterburg"
        else:
            city = translit(city, "ru", reversed=True)

        cities_cookie = request.COOKIES.get("last_cities", "")
        cities_list = cities_cookie.split(",") if cities_cookie else []

        if city not in cities_list:
            if len(cities_list) >= 5:
                cities_list.pop(0)
            cities_list.append(city)

        weather = get_weather(city)

        if request.user.is_authenticated:
            CityHistory.objects.create(user=request.user, city=city)

        context = {
            "page": "main-page",
            "weather": weather,
            "location_name": city,
        }
        response = render(request, "main.html", context)
        response.set_cookie(
            "last_cities", ",".join(cities_list), max_age=30 * 24 * 60 * 60
        )
        return response
    else:
        return render(request, "main.html", {})


def register(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('main-page')
    else:
        form = RegistrationForm()
    return render(request, 'registration/reg.html', {'form': form})

def history_page(request):
    history = CityHistory.objects.filter(user=request.user)
    return render(request, 'history.html', {'history': history})


class CityHistoryAPIView(APIView):
    def get(self, request):
        history = CityHistory.objects.all()
        city_counts = history.values('city').annotate(count=Count('city'))
        serializer = CityHistorySerializer(city_counts, many=True)
        return Response(serializer.data)