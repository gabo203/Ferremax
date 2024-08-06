import random
import requests
from datetime import datetime, timedelta
from django.shortcuts import get_object_or_404, render, redirect
from django.core.cache import cache
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.views import APIView
from transbank.error.transbank_error import TransbankError
from transbank.webpay.webpay_plus.transaction import Transaction
from .models import Producto, Carrito, CarritoItem
from .serializers import ProductoSerializer, CarritoSerializer
API_URL = "https://mindicador.cl/api/dolar"

def obtener_fecha_actual():
    return datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%fZ")

def obtener_valor_dolar_actual():
    response = requests.get(API_URL)
    data = response.json()

    if response.status_code == 200:
        try:
            fecha_actual = datetime.now().strftime("%Y-%m-%d")
            valor_dolar = next((item["valor"] for item in data["serie"] if item["fecha"].startswith(fecha_actual)), None)

            if valor_dolar is None:
                fecha_anterior = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
                valor_dolar = next((item["valor"] for item in data["serie"] if item["fecha"].startswith(fecha_anterior)), None)

            if valor_dolar is None:
                raise ValueError("No se encontró el valor del dólar para la fecha actual ni para la fecha anterior")
            
            return valor_dolar
        except KeyError:
            raise ValueError("Error al analizar la respuesta JSON de la API")
    else:
        raise ValueError(f"Error al obtener el valor del dólar: {response.status_code}")

def obtener_precio_usd(precio_clp):
    valor_dolar = cache.get('valor_dolar')
    if not valor_dolar:
        valor_dolar = obtener_valor_dolar_actual()
        cache.set('valor_dolar', valor_dolar, 60 * 60)  # Cache por 1 hora
    precio_usd = precio_clp / valor_dolar
    return "{:.2f}".format(precio_usd)

class ProductoViewSet(viewsets.ViewSet):
    def list(self, request):
        productos = Producto.objects.all().only('id', 'nombre', 'marca', 'precio')
        data = []
        for producto in productos:
            precio_usd = obtener_precio_usd(producto.precio)
            data.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'marca': producto.marca,
                'precio': producto.precio,
                'precio_usd': precio_usd,
            })
        return Response(data)

    def retrieve_by_name(self, request, nombre=None):
        producto = get_object_or_404(Producto, nombre=nombre)
        precio_usd = obtener_precio_usd(producto.precio)
        precio_clp = producto.precio

        serializer = ProductoSerializer(producto)
        data = serializer.data
        data['precio'] = [
            {
                'fecha': obtener_fecha_actual(),
                'valor_usd': precio_usd,
                'valor_clp': precio_clp
            }
        ]

        return Response(data)

    def retrieve(self, request, pk=None):
        producto = get_object_or_404(Producto, pk=pk)
        precio_usd = obtener_precio_usd(producto.precio)
        precio_clp = producto.precio

        serializer = ProductoSerializer(producto)
        data = serializer.data
        data['precio'] = [
            {
                'fecha': obtener_fecha_actual(),
                'valor_usd': precio_usd,
                'valor_clp': precio_clp
            }
        ]

        return Response(data)
    
    def create(self, request):
        serializer = ProductoSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CarritoViewSet(viewsets.ViewSet):
    def retrieve(self, request, pk=None):
        carrito = get_object_or_404(Carrito, pk=pk)
        serializer = CarritoSerializer(carrito)
        return Response(serializer.data)

    def create(self, request):
        carrito = Carrito.objects.create()
        return Response({'id': carrito.id}, status=status.HTTP_201_CREATED)

    def add_item(self, request, pk=None):
        carrito = get_object_or_404(Carrito, pk=pk)
        producto_id = request.data.get('producto_id')
        cantidad = request.data.get('cantidad', 1)
        producto = get_object_or_404(Producto, pk=producto_id)
        carrito_item, created = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)
        if not created:
            carrito_item.cantidad += cantidad
        carrito_item.save()
        return Response({'status': 'item added'}, status=status.HTTP_200_OK)

class WebpayPlusCreate(APIView):
    def get(self, request, carrito_id):
        carrito = get_object_or_404(Carrito, id=carrito_id)
        total_amount = sum(item.subtotal() for item in carrito.carritoitem_set.all())
        
        buy_order = str(random.randrange(1000000, 99999999))
        session_id = str(random.randrange(1000000, 99999999))
        return_url = "http://localhost:8000/api/webpay-plus/commit/"

        create_request = {
            "buy_order": buy_order,
            "session_id": session_id,
            "amount": total_amount,
            "return_url": return_url,
        }

        try:
            response = (Transaction()).create(buy_order, session_id, total_amount, return_url)
            url_webpay_form = response["url"]+"?"+"token_ws="+response["token"]
            
            return Response(
                {"request": create_request, "response": response, "url_webpay_form": url_webpay_form},
                 status=status.HTTP_200_OK,
             )
        except TransbankError as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class CommitWebpayTransaction(APIView):
    def get(self, request):
        token_ws = request.query_params.get('token_ws')

        if token_ws:
            try:
                result = (Transaction()).commit(token_ws)
                return Response({"status": "Success", "detail": result})
            except TransbankError as e:
                return Response({"error": str(e)}, status=500)
        else:
            return Response({"error": "Token not provided"}, status=400)

# Create your views here.
def home(request):
    return render(request, 'api/home.html')

def productos(request):
    carrito_id = request.session.get('carrito_id')
    if carrito_id:
        carrito = get_object_or_404(Carrito, id=carrito_id)
    else:
        carrito = Carrito.objects.create()
        request.session['carrito_id'] = carrito.id

    if request.method == 'POST':
        producto_id = request.POST.get('producto_id')
        cantidad = int(request.POST.get('cantidad', 1))
        producto = get_object_or_404(Producto, id=producto_id)
        carrito_item, created = CarritoItem.objects.get_or_create(carrito=carrito, producto=producto)
        if not created:
            carrito_item.cantidad += cantidad
        carrito_item.save()
        return redirect('carrito')

    productos = Producto.objects.all().only('id', 'nombre', 'marca', 'precio')
    data = []
    for producto in productos:
        precio_usd = obtener_precio_usd(producto.precio)
        data.append({
            'id': producto.id,
            'nombre': producto.nombre,
            'marca': producto.marca,
            'precio': producto.precio,
            'precio_usd': precio_usd,
        })
    return render(request, 'api/productos.html', {'productos': data, 'carrito': carrito})

def carrito(request):
    carrito_id = request.session.get('carrito_id')
    carrito = get_object_or_404(Carrito, id=carrito_id)
    carrito_items = CarritoItem.objects.filter(carrito=carrito)
    total = sum(item.subtotal() for item in carrito_items)
    return render(request, 'api/carrito.html', {'carrito_items': carrito_items, 'total': total})

def eliminar_item_carrito(request, item_id):
    item = get_object_or_404(CarritoItem, id=item_id)
    item.delete()
    return redirect('carrito')