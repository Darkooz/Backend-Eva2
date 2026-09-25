import json
import os
from django.shortcuts import render

def inicio(request):
    ruta = os.path.join(os.path.dirname(__file__), 'autoridades.json')
    with open(ruta, 'r', encoding='utf-8') as f:
        datos = json.load(f)
    return render(request, 'institucion/inicio.html', {'autoridades': datos})

def historia(request):
    return render(request, 'institucion/historia.html')
