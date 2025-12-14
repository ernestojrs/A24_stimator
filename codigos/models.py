from django.db import models 
import requests

# Create your models here.
class Items(models.Model):
    Codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=100)
    categoria = models.TextField()

    def __str__(self):
        return self.nombre
    

def get_usd_to_dop_rate():
    try:
        response = requests.get('https://api.exchangerate-api.com/v4/latest/USD')
        data = response.json()
        rate = data['rates']['DOP']
        return rate
    except Exception as e:
        print(f"Error fetching exchange rate: {e}")
        return 62  # default rate if API call fails

class calculoFlotilla():

    #inputs para el calculo de costos
    tipo_horario = ['Diurno', 'Nocturno', 'Feriado']  # opciones: Diurno, Nocturno, Feriado
    rate_horario = {
        'Diurno': 1.0,
        'Nocturno': 1.8,
        'Feriado': 2.0,
    }
    cantidad_dias_de_trabajo = 1
    cantidad_supervisores = 0
    cantidad_equipos_tecnicos = 1
    cantidad_vehiculos = 1
    incluye_dieta = False
    incluye_alojamiento = False
    cantidad_dias_alojamiento = 1
    costo_alojamiento_por_dia = 2000
    distancia_a_recorrer_km = 0.0
    margen_beneficio = 40  # porcentaje

    def __init__(self):
        #combustible
        self.consumo_vehiculo = 40.0 # galones por kilometro
        self.precio_galon = 300 # precio por galon en pesos
        #Depreciacion del vehiculo
        self.valor_vehiculo = 974000 # valor del vehiculo en pesos
        self.costo_gomas = 40000 # costo de gomas en pesos
        self.mantenimiento = 11000 # costo de mantenimiento cada 6k kilometros
        #costo personal
        self.sueldo_tecnicos = 60000 # sueldo mensual de tecnicos
        self.sueldo_supervisor = 70000 # sueldo mensual de supervisor

        # tasa del dolar
        self.tasa_dolar = get_usd_to_dop_rate()  # pesos por dolar

        # dietas personal
        self.dieta_dos_tecnicos = 1600 # dieta por dia para dos tecnicos
        self.dieta_supervisor = 1000 # dieta por dia para un supervisor

    def costo_personal(self, tipo_horario):
        costo_personal = 0
        self.tipo_horario = self.tipo_horario[tipo_horario]
        if self.tipo_horario == 'Diurno':
            if self.cantidad_supervisores == 0:
                costo_personal = (((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos)/24) * self.rate_horario['Diurno']) * self.cantidad_dias_de_trabajo
            else:
                costo_personal = ((((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos) + (self.sueldo_supervisor * self.cantidad_supervisores))/24) * self.rate_horario['Diurno']) * self.cantidad_dias_de_trabajo
        elif self.tipo_horario == 'Nocturno':
            if self.cantidad_supervisores == 0:
                costo_personal = (((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos)/24) * self.rate_horario['Nocturno']) * self.cantidad_dias_de_trabajo
            else:
                costo_personal = ((((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos) + (self.sueldo_supervisor * self.cantidad_supervisores))/24) * self.rate_horario['Nocturno']) * self.cantidad_dias_de_trabajo
        elif self.tipo_horario == 'Feriado':
            if self.cantidad_supervisores == 0:
                costo_personal = (((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos)/24) * self.rate_horario['Feriado']) * self.cantidad_dias_de_trabajo
            else:
                costo_personal = ((((self.sueldo_tecnicos * self.cantidad_equipos_tecnicos) + (self.sueldo_supervisor * self.cantidad_supervisores))/24) * self.rate_horario['Feriado']) * self.cantidad_dias_de_trabajo

        return costo_personal
    
    def dietas_personal(self):
        costo_dietas = 0
        if self.incluye_dieta:
            if self.cantidad_supervisores == 0:
                costo_dietas = (self.dieta_dos_tecnicos * self.cantidad_equipos_tecnicos) * self.cantidad_dias_de_trabajo
            else:
                costo_dietas = ((self.dieta_dos_tecnicos * self.cantidad_equipos_tecnicos) + (self.dieta_supervisor * self.cantidad_supervisores)) * self.cantidad_dias_de_trabajo
        return costo_dietas
    def combustible_vehiculos(self):
        costo_combustible = (((self.distancia_a_recorrer_km / self.consumo_vehiculo) * self.precio_galon) * self.cantidad_vehiculos) * self.cantidad_dias_de_trabajo
        return costo_combustible
    def depreciacion_vehiculos(self):
        costo_depreciacion = ((((self.valor_vehiculo / 300000) * self.distancia_a_recorrer_km) + 
                              ((self.costo_gomas / 10000)* self.distancia_a_recorrer_km) + 
                              ((self.mantenimiento / 5000)* self.distancia_a_recorrer_km)) 
                              * self.cantidad_vehiculos) * self.cantidad_dias_de_trabajo
        return costo_depreciacion
    def depreciacion_equipos(self):
        costo_depreciacion = self.cantidad_dias_de_trabajo * 500 
        return costo_depreciacion
    def costo_administrativo(self, subtotal):
        costo_admin = subtotal * 0.25
        return costo_admin
    

        
        
    
