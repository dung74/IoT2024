from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse 
from .models import *
import json
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate,login, logout
from django.contrib import messages
from django.core.paginator import Paginator
from .models import Monitor
from paho.mqtt.client import Client  # Thư viện MQTT
from .models import DeviceState, LichSu  # Model lưu trạng thái thiết bị
from datetime import datetime

import time
import pandas as pd
import plotly.express as px

def profile(request):
    context = {}
    return render(request, 'app/html/profile.html', context)
def logoutPage(request):
    logout(request)
    return redirect('login')
def home(request):
    device_states  = DeviceState.objects.all()
    
    return render(request, 'app/html/home.html', {'device_states': device_states})

def history(request):
    
 # Giả sử bạn có một queryset từ mô hình LichSu
    lich_su_list = LichSu.objects.all().order_by('-thoi_gian')

    id_filter = request.GET.get('id_filter')
    if id_filter :
        lich_su_list = lich_su_list.filter(id = id_filter)

    thoi_gian_filter = request.GET.get('thoi_gian_filter')
    if thoi_gian_filter:
        try:
            filter_date = datetime.strptime(thoi_gian_filter, "%Y-%m-%d")
            start_of_day = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = filter_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            lich_su_list = lich_su_list.filter(thoi_gian__range=(start_of_day, end_of_day))
        except ValueError: 
            pass  # Nếu ngày không hợp lệ, bỏ qua

    
    thiet_bi_filter = request.GET.get('thiet_bi_filter')
    if thiet_bi_filter:
        lich_su_list = lich_su_list.filter(thiet_bi__icontains = thiet_bi_filter)

    trang_thai_filter = request.GET.get('trang_thai_filter')
    if trang_thai_filter:
        lich_su_list = lich_su_list.filter(trang_thai__icontains = trang_thai_filter)

         # Lấy page_size từ request, nếu không có thì mặc định là 10
    page_size = request.GET.get('page_size', request.session.get('page_size', 10))

    # Lưu page_size vào session
    request.session['page_size'] = page_size

    try:
        page_size = int(page_size)
        if page_size<=0:
            page_size = 10
    except ValueError:
        page_size = 10



    paginator = Paginator(lich_su_list, page_size)  # Mỗi trang hiển thị 10 mục
    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'page_size': page_size

    }

    return render(request,'app/html/history.html', context)



def monitor(request):
    if not Monitor.objects.exists():
        populate_data2()
    monitor_list = Monitor.objects.all().order_by('-timestamp')

    id_filter = request.GET.get('id_filter')
    if id_filter:
        monitor_list = monitor_list.filter(id = id_filter)
    
    thoi_gian_filter = request.GET.get('thoi_gian_filter')
    if thoi_gian_filter:
        try:
            filter_date = datetime.strptime(thoi_gian_filter, "%Y-%m-%d")
            start_of_day = filter_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = filter_date.replace(hour=23, minute=59, second=59, microsecond=999999)
            monitor_list = monitor_list.filter(timestamp__range=(start_of_day, end_of_day))
        except ValueError:
            pass  # Nếu ngày không hợp lệ, bỏ qua

    temperature_filter = request.GET.get('temperature_filter')
    if temperature_filter == "lt20":
        monitor_list = monitor_list.filter(temperature__lt=20)
    elif temperature_filter == "20-30":
        monitor_list = monitor_list.filter(temperature__gte=20, temperature__lte=30)
    elif temperature_filter == "gt30":
        monitor_list = monitor_list.filter(temperature__gt=30)

    humidity_filter = request.GET.get('humidity_filter')
    if humidity_filter == "lt50":
        monitor_list = monitor_list.filter(humidity__lt=50)
    elif humidity_filter == "50-80":
        monitor_list = monitor_list.filter(humidity__gte=50, humidity__lte=80)
    elif humidity_filter == "gt80":
        monitor_list = monitor_list.filter(humidity__gt=80)

    light_intensity_filter = request.GET.get('light_intensity_filter')
    if light_intensity_filter == "lt200":
        monitor_list = monitor_list.filter(light_intensity__lt=200)
    elif light_intensity_filter == "200-600":
        monitor_list = monitor_list.filter(light_intensity__gte=200, light_intensity__lte=600)
    elif light_intensity_filter == "gt600":
        monitor_list = monitor_list.filter(light_intensity__gt=600)

    
     # Lấy page_size từ request, nếu không có thì mặc định là 10
    page_size = request.GET.get('page_size', request.session.get('page_size', 10))

    # Lưu page_size vào session
    request.session['page_size'] = page_size

    try:
        page_size = int(page_size)
        if page_size<=0:
            page_size = 10
    except ValueError:
        page_size = 10



    paginator = Paginator(monitor_list, page_size)  # Mỗi trang hiển thị 10 mục
    page_number = request.GET.get('page',1)
    page_obj = paginator.get_page(page_number)

    context = {
        'page_obj': page_obj,
        'page_size': page_size

    }

    return render(request,'app/html/monitor.html', context)


def populate_data2():
    Monitor.objects.bulk_create([
    Monitor(temperature=25, humidity=60, light_intensity=150),
    Monitor(temperature=26, humidity=65, light_intensity=160),
    Monitor(temperature=27, humidity=62, light_intensity=155),
    Monitor(temperature=28, humidity=63, light_intensity=158),
    Monitor(temperature=24, humidity=58, light_intensity=145),
    Monitor(temperature=29, humidity=64, light_intensity=170),
    Monitor(temperature=22, humidity=59, light_intensity=140),
    Monitor(temperature=23, humidity=61, light_intensity=152),
    Monitor(temperature=30, humidity=67, light_intensity=180),
    Monitor(temperature=21, humidity=55, light_intensity=130),
    Monitor(temperature=20, humidity=54, light_intensity=120),

])

def publish_mqtt_command(device_name, state):
    client = Client()
    client.username_pw_set(username="dungx", password="1234567")
    client.connect("localhost", 1883, 60)
    
    # Publish lệnh MQTT
    message = f"{device_name} {'ON' if state else 'OFF'}"
    client.publish("ledControll", message)
    client.loop_start()     

   
def toggle_device(request):
    if request.method =='POST':
        device_name = request.POST.get('device_name')
        if device_name =="Bóng Đèn":
            device = 'LED1'
        elif device_name =="Quạt":
            device = 'LED2'
        elif device_name =="Điều Hòa":
            device = 'LED3'
        state = request.POST.get('state') == 'true'


        device_state, created  =DeviceState.objects.get_or_create(device_name = device_name)
        device_state.state = state
        device_state.save()

        LichSu.objects.create(
            thiet_bi = device_name,
            trang_thai = 'Bật' if state else 'Tắt',
            thoi_gian = timezone.now()

        )
 # Publish lệnh MQTT để điều khiển thiết bị
        publish_mqtt_command(device, state)
        time.sleep(0.5)
        # Trả về phản hồi JSON thành công
        return JsonResponse({'status': 'success'})

    # Trả về phản hồi lỗi nếu không phải phương thức POST
    return JsonResponse({'status': 'failed'}, status=400)



def get_sensor_data(request):
    data = list(Monitor.objects.values('timestamp', 'temperature', 'humidity', 'light_intensity'))
    return JsonResponse(data, safe=False)


