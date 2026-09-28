from django.shortcuts import render
from django.db.models import Q, Count
from institucion.models import Delegacion

def lista_delegaciones(request):
    q = request.GET.get('q', '')
    delegaciones = Delegacion.objects.annotate(
        total_autoridades=Count('autoridades')
    ).order_by('nombre')
    if q:
        delegaciones = delegaciones.filter(
            Q(nombre__icontains=q) | Q(direccion__icontains=q)
        )
    return render(request, 'delegaciones/lista.html', {
        'delegaciones': delegaciones,
        'q': q,
    })

def contacto_delegaciones(request):
    return render(request, 'delegaciones/contacto.html')