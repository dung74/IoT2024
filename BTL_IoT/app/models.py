from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
# Create your models here.
# chance from register djange

class CreateUserForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']


    
class DeviceState(models.Model):
    device_name = models.CharField(max_length=100 , unique= True)
    state = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.device_name}:{'Bật' if self.state else 'Tắt'}"

    
class LichSu(models.Model):
    id = models.AutoField(primary_key=True)
    thoi_gian = models.DateTimeField(auto_now_add=True)
    thiet_bi = models.CharField(max_length=100)
    trang_thai = models.CharField(max_length=10, choices=[('Bật', 'Bật'), ('Tắt', 'Tắt')])

    def __str__(self):
        return f"{self.thiet_bi} - {self.trang_thai} lúc {self.thoi_gian}"

class Monitor(models.Model):
    id = models.AutoField(primary_key=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    temperature = models.FloatField()
    humidity = models.FloatField()
    light_intensity = models.FloatField()

    def __str__(self):
        return f"{self.timestamp} - Temp: {self.temperature}°C, Humidity: {self.humidity}%, Light: {self.light_intensity} lux"


# class EnvironmentalData(models.Model):
#     temperature = models.FloatField()
#     humidity = models.FloatField()
#     dust_level = models.FloatField()
#     timestamp = models.DateTimeField(default=timezone.now)

#     def __str__(self):
#         return f"{self.timestamp} - Temp: {self.temperature}, Humidity: {self.humidity}, Dust: {self.dust_level}"




    