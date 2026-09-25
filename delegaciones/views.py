import json
import os
from django.shortcuts import render

def lista_delegaciones(request):
    # 1. Obtener la ruta absoluta del archivo JSON dentro de la app
    ruta_archivo = os.path.join(os.path.dirname(__file__), 'delegaciones.json')
    
    # 2. Abrir y leer los datos
    with open(ruta_archivo, 'r', encoding='utf-8') as archivo:
        datos_delegaciones = json.load(archivo)
        
    # 3. Enviar los datos al template a través de un diccionario de contexto
    contexto = {
        'delegaciones': datos_delegaciones
    }
    
    return render(request, 'delegaciones/lista.html', contexto)

def contacto_delegaciones(request):
    return render(request, 'delegaciones/contacto.html')