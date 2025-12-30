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
from django.contrib import messages
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

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
            messages.success(request, 'Codigo agregado exitosamente.')  
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

       results = {
          
          #inputs
          "tipo_horario": tipo_horario,
          "cantidad_dias_de_trabajo": calculo.cantidad_dias_de_trabajo,
            "cantidad_supervisores": calculo.cantidad_supervisores,
            "cantidad_equipos_tecnicos": calculo.cantidad_equipos_tecnicos,
            "cantidad_vehiculos": calculo.cantidad_vehiculos,
            "incluye_dieta": calculo.incluye_dieta,
            "incluye_alojamiento": calculo.incluye_alojamiento,
            "margen_beneficio": calculo.margen_beneficio,
            "distancia_a_recorrer_km": calculo.distancia_a_recorrer_km,
            "tasa_dolar": float(calculo.tasa_dolar),
            "gerenated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),

          
          #outputs
          "costo_personal": float(costo_personal),
          "costo_diario_brigada_rd": float(costo_diario_brigada_rd),
          "costo_dietas": float(costo_dietas),
          "costo_combustible": float(costo_combustible),
          "costo_depreciacion_vehiculo": float(costo_depreciacion_vehiculo),
          "costo_depreciacion_herramientas": float(costo_depreciacion_herramientas),
          "costo_administrativo": float(costo_administrativo),
          "costo_total_brigada": float(costo_personal + costo_dietas),
          "costo_general_brigada_rd": float(costo_general_brigada_rd),
          "costo_diario_brigada_usd": float(costo_diario_brigada_usd),
          "costo_general_brigada_usd": float(costo_general_brigada_usd), 
          "costo_general_brigada_beneficio_usd": float(costo_general_brigada_beneficio_usd),                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                            
            

       }

       request.session['last_brigada_results'] = results
       request.session.modified = True

       return render(request, 'html/calculo_brigada.html', contexto)
    return render(request, 'html/calculo_brigada.html')

# view to generate pdf report of the last brigada calculation
@login_required(login_url='login')
def generar_reporte_brigada_view(request):
    results = request.session.get('last_brigada_results')
    if not results:
        messages.error(request, 'No hay resultados de brigada disponibles para generar el reporte.')
        return redirect('brigadas')

    # Crear el PDF
    response = HttpResponse(content_type='application/pdf')
    datetime_now = datetime.now().strftime("%Y%m%d")
    response['Content-Disposition'] = f'attachment; filename="reporte_brigada_{datetime_now}.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    width, height = letter

    y = height - 60

    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, y, "Reporte de Cálculo de Brigada")
    y -= 18
    p.drawString(50, y, f"Generado el: {results['gerenated_at']}")
    y -= 14
    p.drawString(50, y, f"Tasa USD/DOP: {results['tasa_dolar']}")

    y -= 24
    def row(label, value):
        nonlocal y
        p.setFont("Helvetica", 12)
        p.drawString(50, y, f"{label}:")
        p.drawRightString(width - 50, y, f"{value}")
        y -= 16

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Parámetros de Entrada")
    y -= 20
    for key in ['tipo_horario', 'cantidad_dias_de_trabajo', 'cantidad_supervisores',
                'cantidad_equipos_tecnicos', 'cantidad_vehiculos', 'incluye_dieta',
                'incluye_alojamiento', 'margen_beneficio', 'distancia_a_recorrer_km']:
        row(key.replace('_', ' ').capitalize(), results[key])
        if y < 50:
            p.showPage()
            p.setFont("Helvetica", 12)
            y = height - 50

    p.setFont("Helvetica-Bold", 14)
    p.drawString(50, y, "Resultados del Cálculo")
    y -= 20

    row("Costo de Personal (DOP)", f"{results['costo_personal']:.2f}")
    row("Dietas (DOP)", f"{results['costo_dietas']:.2f}")
    row("Combustible (DOP)", f"{results['costo_combustible']:.2f}")
    row("Depreciación Vehículo (DOP)", f"{results['costo_depreciacion_vehiculo']:.2f}")
    row("Depreciación Herramientas (DOP)", f"{results['costo_depreciacion_herramientas']:.2f}")
    row("Costo Administrativo (DOP)", f"{results['costo_administrativo']:.2f}")
    row("Costo Total Brigada (DOP)", f"{results['costo_total_brigada']:.2f}")
    row("Costo Diario Brigada (DOP)", f"{results['costo_diario_brigada_rd']:.2f}")
    row("Costo General Brigada (DOP)", f"{results['costo_general_brigada_rd']:.2f}")
    row("Costo Diario Brigada (USD)", f"{results['costo_diario_brigada_usd']:.2f}")
    row("Costo General Brigada (USD)", f"{results['costo_general_brigada_usd']:.2f}")
    row("Costo General + Beneficio (USD)", f"{results['costo_general_brigada_beneficio_usd']:.2f}")

    y -= 8

    p.setFont("Helvetica-Oblique", 14)
    p.drawString(50, y, "Totales calculados según los parámetros ingresados.")

    y -= 20

    row("costo diario brigada rd", f"{results['costo_diario_brigada_rd']:.2f} DOP")
    row("costo general brigada rd", f"{results['costo_general_brigada_rd']:.2f} DOP")
    row("costo diario brigada usd", f"{results['costo_diario_brigada_usd']:.2f} USD")
    row("costo general brigada usd", f"{results['costo_general_brigada_usd']:.2f} USD")

    y-= 10
    p.setFont("Helvetica-Bold", 12)
    p.drawString(50, y, "Costo General + Beneficio (USD):")
    p.drawRightString(width - 50, y, f"{results['costo_general_brigada_beneficio_usd']:.2f} USD")

    p.showPage()
    p.save()
    return response