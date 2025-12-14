from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from .forms import RegisterForm, loginForm, CodigoForm
from .models import Items, calculoFlotilla
from django.db.models import Q

# Create your views here.

def login_view(request):
    if request.method == 'POST':
       username = request.POST.get('username')
       password = request.POST.get('password')
       user = authenticate(request, username=username, password=password)
       if user is not None:
            login(request, user)
            next_url =request.POST.get('next') or request.GET.get('next') or 'home'
            return redirect(next_url)
       else:
        error_message = 'Invalid username or password'  
        return render(request, 'html/login.html', {'error_message': error_message})
    else:   
     return render(request, 'html/login.html')
 
     
def register_view(request):
    if request.method == 'POST':
     form  = RegisterForm(request.POST)
     if form.is_valid():
        username = form.cleaned_data['username']
        password = form.cleaned_data['password']
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('home')
    else:
     form = RegisterForm()
     return render(request, 'html/register.html', {'form': form})
     
def logout_view(request):
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    else:
       return redirect('home')
     

#home view
@login_required(login_url='login')
def home_view(request):     
    return render(request, 'html/home.html', )

#protected view
class ProtectedView(LoginRequiredMixin, View):
    login_url = 'login'
    redirect_field_name = 'redirect_to'
    
    def get(self, request):
        return render(request, 'html/protected.html')
    
#view codigo form to create items
@login_required(login_url='login')
def codigo_form_view(request):
    form = CodigoForm()
    if request.method == 'POST':  
        form = CodigoForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_codigos')
    return render(request, 'html/codigo_form.html', {'form': form})

#view to list items
@login_required(login_url='login')
def lista_codigos_view(request):
    query = request.GET.get('q', '')
    items = Items.objects.all()
    if query:
        items = items.filter(Q(Codigo__icontains=query) | Q(nombre__icontains=query))
    else:
        items = Items.objects.all()
    return render(request, 'html/lista_codigos.html', {'items': items, 'query': query})

# update de los codigos
'''@login_required(login_url='login')
def actualizar_codigo_view(request, codigo):
   item = Items.objects.get(id=codigo)
   form = CodigoForm(instance=item) 
   if request.method == 'POST':
     form = CodigoForm(request.POST, instance=item)
     if form.is_valid():
      form.save()
      return redirect('lista_codigos')
   return render(request, 'html/actualizar_codigo.html', {'form': form, 'item': item})'''

# delete de los codigos
@login_required(login_url='login')
def eliminar_codigo_view(request, codigo):
    item = Items.objects.get(id=codigo)
    if request.method == 'POST':
        item.delete()
        return redirect('lista_codigos')
    return render(request, 'html/eliminar_codigo.html', {'item': item})

# view for brigadas
@login_required(login_url='login')
def brigadas_view(request):
    if request.method == 'POST':
       calculo = calculoFlotilla()
       # obtener los datos del formulario
       tipo_horario = int(request.POST.get('tipo_horario'))
       calculo.cantidad_dias_de_trabajo = int(request.POST.get('cantidad_dias_de_trabajo'))
       calculo.cantidad_supervisores = int(request.POST.get('cantidad_supervisores'))   
       calculo.cantidad_equipos_tecnicos = int(request.POST.get('cantidad_equipos_tecnicos'))
       calculo.cantidad_vehiculos = int(request.POST.get('cantidad_vehiculos'))
       calculo.incluye_dieta = request.POST.get('incluye_dieta') == 'on'
       calculo.incluye_alojamiento = request.POST.get('incluye_alojamiento') == 'on'
       calculo.margen_beneficio = int(request.POST.get('margen_beneficio'))
       # calculo.cantidad_dias_alojamiento = int(request.POST.get('cantidad_dias_alojamiento'))
       calculo.distancia_a_recorrer_km = float(request.POST.get('distancia_a_recorrer_km')) 
         # asignar los valores a la clase calculoFlotilla
         
       # realizar el calculo costo personal
       costo_personal = calculo.costo_personal(tipo_horario)
       # realizar calculo dietas
       if calculo.incluye_dieta:
           costo_dietas = calculo.dietas_personal()
       else:
           costo_dietas = 0
        
        # combustible vehiculo
       costo_combustible = calculo.combustible_vehiculos()

       # depreciacion vehiculo
       costo_depreciacion_vehiculo = calculo.depreciacion_vehiculos()

       # depreciacion equipo tecnico
       costo_depreciacion_herramientas = calculo.depreciacion_equipos()

       #costo administrativo y margen de beneficio
       costo_administrativo = (costo_personal + costo_combustible + costo_depreciacion_vehiculo + costo_depreciacion_herramientas + costo_dietas) * 0.25

       # costo diario brigada rd
       costo_diario_brigada_rd = (costo_personal + costo_combustible + costo_depreciacion_vehiculo + costo_depreciacion_herramientas + costo_dietas + costo_administrativo) / calculo.cantidad_dias_de_trabajo

       #costo general de la brigada
       costo_general_brigada_rd = costo_personal + costo_combustible + costo_depreciacion_vehiculo + costo_depreciacion_herramientas + costo_dietas + costo_administrativo

       # costo diario brigada en usd
       costo_diario_brigada_usd = costo_diario_brigada_rd / calculo.tasa_dolar

       #costo general de la brigada en usd
       costo_general_brigada_usd = costo_general_brigada_rd / calculo.tasa_dolar

       # costo general + beneficio
       costo_general_brigada_beneficio_usd = costo_general_brigada_usd * (1 + (calculo.margen_beneficio / 100))

       contexto = {
        'costo_personal': costo_personal,
        'costo_diario_brigada_rd': costo_diario_brigada_rd,
        'costo_dieta_personal': costo_dietas,
        'costo_combustible': costo_combustible,
        'costo_depreciacion_vehiculo': costo_depreciacion_vehiculo,
        'costo_depreciacion_herramientas': costo_depreciacion_herramientas,
        'costo_administrativo': costo_administrativo,
        'costo_total_brigada': costo_personal + costo_dietas,
        'costo_general_brigada_rd' : costo_general_brigada_rd,
        'costo_diario_brigada_usd': costo_diario_brigada_usd,
        'costo_general_brigada_usd': costo_general_brigada_usd,
        'costo_general_brigada_beneficio_usd': costo_general_brigada_beneficio_usd,
        
       } 
       return render(request, 'html/calculo_brigada.html', contexto)
    return render(request, 'html/calculo_brigada.html')