from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from .models import Producto
from transbank.webpay.webpay_plus.transaction import Transaction, WebpayOptions, IntegrationCommerceCodes, IntegrationApiKeys, TransbankError
from transbank.common.integration_type import IntegrationType
from django.http import JsonResponse

def producto_list(request):
    productos = Producto.objects.all()
    return render(request, 'producto_list.html', {'productos': productos})


def carrito(request):
    carrito = request.session.get('carrito', [])  # Obtener el carrito de la sesión como lista
    productos_carrito = []
    total = 0
    
    # Agrupar los productos por ID y calcular la cantidad de cada uno
    productos_cantidad = {}
    for producto_id in carrito:
        if producto_id in productos_cantidad:
            productos_cantidad[producto_id] += 1
        else:
            productos_cantidad[producto_id] = 1
    
    # Obtener los productos y calcular el total
    for producto_id, cantidad in productos_cantidad.items():
        try:
            producto = Producto.objects.get(id=producto_id)
            total += producto.precio * cantidad
            productos_carrito.append({
                'producto': producto,
                'cantidad': cantidad
            })
        except Producto.DoesNotExist:
            # Manejar el caso cuando el producto no existe en la base de datos
            pass
    
    return render(request, 'carrito.html', {'productos_carrito': productos_carrito, 'total': total})

def contacto(request):
    return render(request, 'contacto.html')

from django.shortcuts import render

def home(request):
    return render(request, 'index.html')

def producto_detalle(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id)
    return render(request, 'producto_detalle.html', {'producto': producto})



def agregar_al_carrito(request, producto_id):
    if request.method == 'POST':
        cantidad = int(request.POST.get('cantidad', 1))
        carrito = request.session.get('carrito', [])

        for _ in range(cantidad):
            carrito.append(producto_id)

        request.session['carrito'] = carrito

    return redirect('producto_list')





def eliminar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', [])  # Obtener el carrito de la sesión como lista
    
    while producto_id in carrito:
        carrito.remove(producto_id)
    
    request.session['carrito'] = carrito
    
    return redirect('carrito')


def procesar_compra(request):
    carrito = request.session.get('carrito', [])
    total = 0

    # Agrupar los productos por ID y calcular la cantidad de cada uno
    productos_cantidad = {}
    for producto_id in carrito:
        if producto_id in productos_cantidad:
            productos_cantidad[producto_id] += 1
        else:
            productos_cantidad[producto_id] = 1

    # Obtener los productos y calcular el total
    for producto_id, cantidad in productos_cantidad.items():
        producto = Producto.objects.filter(id=producto_id).first()
        if producto:
            total += producto.precio * cantidad
        else:
            # Manejar el caso cuando el producto no existe
            print(f"El producto con ID {producto_id} no existe.")
            # Puedes realizar alguna acción adicional, como eliminar el producto del carrito

    # Convertir el monto total a un valor entero en pesos chilenos
    amount = int(total)

    buy_order = "orden_compra_123"  # Genera un número de orden único
    session_id = "sesion_123"  # Genera un ID de sesión único
    return_url = "http://localhost:8000/confirmacion_pago/"  # URL de retorno después del pago

    try:
        # Crear una instancia de Transaction con las opciones de Webpay Plus
        tx = Transaction(WebpayOptions(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, IntegrationType.TEST))

        # Crear una transacción de Webpay Plus
        response = tx.create(buy_order, session_id, amount, return_url)

        # Obtener la URL y el token de la respuesta
        url = response['url']
        token = response['token']

        # Redireccionar al formulario de pago de Transbank
        return redirect(url + "?token_ws=" + token)

    except TransbankError as e:
        # Manejar errores de Transbank
        print(e.message)
        return redirect('carrito')





def confirmacion_pago(request):
    token = request.GET.get("token_ws")

    try:
        # Crear una instancia de Transaction con las opciones de Webpay Plus
        tx = Transaction(WebpayOptions(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, IntegrationType.TEST))

        # Confirmar la transacción
        response = tx.commit(token)

        if response['status'] == "AUTHORIZED":
            # Pago exitoso, realizar acciones adicionales (guardar la venta, limpiar el carrito, etc.)
            carrito = request.session.get('carrito', [])
            productos_comprados = []

            # Agrupar los productos por ID y calcular la cantidad de cada uno
            productos_cantidad = {}
            for producto_id in carrito:
                if producto_id in productos_cantidad:
                    productos_cantidad[producto_id] += 1
                else:
                    productos_cantidad[producto_id] = 1

            # Obtener los productos comprados y calcular el subtotal
            total = 0
            for producto_id, cantidad in productos_cantidad.items():
                producto = Producto.objects.get(id=producto_id)
                subtotal = producto.precio * cantidad
                total += subtotal
                productos_comprados.append({
                    'producto': producto,
                    'cantidad': cantidad,
                    'subtotal': subtotal
                })

            # Limpiar el carrito después del pago exitoso
            request.session['carrito'] = []

            # Renderizar la plantilla de pago exitoso con los detalles de la compra
            context = {
                'productos_comprados': productos_comprados,
                'total': total,
                'numero_orden': response['buy_order'],
                'fecha_transaccion': response['transaction_date'],
                'numero_tarjeta': response['card_detail']['card_number']
            }
            return render(request, "pago_exitoso.html", context)

        else:
            # Pago fallido, realizar acciones de manejo de errores
            error_message = response['error_message']
            context = {'error_message': error_message}
            return render(request, "pago_fallido.html", context)

    except TransbankError as e:
        # Manejar errores de Transbank
        error_message = e.message
        context = {'error_message': error_message}
        return render(request, "pago_fallido.html", context)




def estado_transaccion(request):
    token = request.GET.get("token_ws")

    try:
        # Crear una instancia de Transaction con las opciones de Webpay Plus
        tx = Transaction(WebpayOptions(IntegrationCommerceCodes.WEBPAY_PLUS, IntegrationApiKeys.WEBPAY, IntegrationType.TEST))

        # Obtener el estado de la transacción
        response = tx.status(token)

        # Realizar acciones según el estado de la transacción
        if response.status == "AUTHORIZED":
            # La transacción está autorizada
            return render(request, "transaccion_autorizada.html")
        else:
            # La transacción no está autorizada
            return render(request, "transaccion_no_autorizada.html")

    except TransbankError as e:
        # Manejar errores de Transbank
        print(e.message)
        return redirect('carrito')
