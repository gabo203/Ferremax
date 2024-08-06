from django.db import models

class Producto(models.Model):
    codigo_producto = models.CharField(max_length=255)
    marca = models.CharField(max_length=255)
    codigo = models.CharField(max_length=255)
    nombre = models.CharField(max_length=255)
    precio = models.PositiveIntegerField()

    def __str__(self):
        return self.nombre

class Carrito(models.Model):
    productos = models.ManyToManyField(Producto, through='CarritoItem')

class CarritoItem(models.Model):
    carrito = models.ForeignKey(Carrito, on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)

    def subtotal(self):
        return self.cantidad * self.producto.precio
