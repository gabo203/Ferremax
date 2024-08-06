from rest_framework import serializers
from .models import Producto, Carrito, CarritoItem

class ProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Producto
        fields = '__all__'

class CarritoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Carrito
        fields = '__all__'

class CarritoItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = CarritoItem
        fields = '__all__'