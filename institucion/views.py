import json
import os
from django.shortcuts import render
from .models import Delegacion, Autoridad

def tu_vista_principal(request):

    lista_autoridades = Autoridad.objects.all()

    context = {
        'autoridades': lista_autoridades
    }
    return render(request, 'institucion/inicio.html', context)
def inicio(request):
    ruta = os.path.join(os.path.dirname(__file__), 'autoridades.json')
    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    return render(request, 'institucion/inicio.html', {'autoridades': datos})

def historia(request):
    return render(request, 'institucion/historia.html')
