from django.shortcuts import render
from django.db.models import Q
from .models import Autoridad

def inicio(request):
    q = request.GET.get('q', '')
    autoridades = Autoridad.objects.select_related('delegacion').order_by('nombre')
    if q:
        autoridades = autoridades.filter(
            Q(nombre__icontains=q) | Q(cargo__icontains=q)
        )
    return render(request, 'institucion/inicio.html', {
        'autoridades': autoridades,
        'q': q,
    })

def historia(request):
    return render(request, 'institucion/historia.html')
