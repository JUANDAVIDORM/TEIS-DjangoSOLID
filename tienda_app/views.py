from django.shortcuts import render
from django.views import View

from .infra.factories import PaymentFactory
from .services import CompraService


class CompraView(View):
    """
    CBV: Vista Basada en Clases.
    Actúa como un "Portero": recibe la petición y delega al servicio.
    """

    template_name = 'tienda_app/compra.html'

    def setup_service(self):
        gateway = PaymentFactory.get_processor()
        return CompraService(procesador_pago=gateway)

    def get(self, request, libro_id):
        servicio = self.setup_service()
        contexto = servicio.obtener_detalle_producto(libro_id)
        return render(request, self.template_name, contexto)

    def post(self, request, libro_id):
        servicio = self.setup_service()
        try:
            total = servicio.ejecutar_compra(libro_id, cantidad=1)
            return render(
                request,
                self.template_name,
                {
                    'mensaje_exito': f"¡Gracias por su compra! Total: ${total}",
                    'total': total,
                },
            )
        except (ValueError, Exception) as e:
            return render(request, self.template_name, {'error': str(e)}, status=400)


class CompraRapidaView(View):
    template_name = 'tienda_app/compra_rapida.html'

    def get(self, request, libro_id):
        from .models import Libro
        from .domain.logic import CalculadorImpuestos
        from django.shortcuts import get_object_or_404
        libro = get_object_or_404(Libro, id=libro_id)
        total = CalculadorImpuestos.obtener_total_con_iva(libro.precio)
        return render(request, self.template_name, {'libro': libro, 'total': total})

    def post(self, request, libro_id):
        from .services import CompraRapidaService
        from .infra.factories import PaymentFactory
        try:
            servicio = CompraRapidaService(PaymentFactory.get_processor())
            total = servicio.procesar(libro_id)
            return render(request, self.template_name, {'mensaje_exito': f'Compra exitosa por: ${total}', 'total': total})
        except ValueError as e:
            return render(request, self.template_name, {'error': str(e)}, status=400)