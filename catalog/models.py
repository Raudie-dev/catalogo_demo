from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nombre")
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True, verbose_name="Descripción")
    icon = models.CharField(max_length=60, default="fa-tag", blank=True, verbose_name="Ícono FontAwesome")
    image_url = models.CharField(max_length=500, blank=True, default="", verbose_name="Imagen o Ícono de la Categoría")

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_image_url(self):
        """Devuelve la URL de la imagen del ícono de la categoría."""
        if self.image_url and self.image_url.strip():
            return self.image_url.strip()
        first_prod = self.products.first()
        if first_prod and first_prod.image_url:
            return first_prod.image_url
        return ""

    def get_icon(self):
        """Devuelve la clase CSS completa de FontAwesome para renderizar en la tienda."""
        if self.icon and self.icon.strip():
            val = self.icon.strip()
            if val.startswith("fa-solid ") or val.startswith("fa-regular ") or val.startswith("fa-brands "):
                return val
            if val.startswith("fa-"):
                return f"fa-solid {val}"
            return f"fa-solid fa-{val}"
        
        # Deducción estética automática según el nombre
        name_lower = self.name.lower()
        if 'conjunto' in name_lower or 'set' in name_lower:
            return 'fa-solid fa-layer-group'
        elif 'blusa' in name_lower or 'top' in name_lower or 'camisa' in name_lower:
            return 'fa-solid fa-shirt'
        elif 'vestido' in name_lower:
            return 'fa-solid fa-person-dress'
        elif 'pantal' in name_lower or 'jean' in name_lower:
            return 'fa-solid fa-lines-leaning'
        elif 'body' in name_lower or 'corset' in name_lower:
            return 'fa-solid fa-vest'
        elif 'falda' in name_lower:
            return 'fa-solid fa-scissors'
        elif 'accesorio' in name_lower or 'joya' in name_lower:
            return 'fa-solid fa-gem'
        elif 'bolso' in name_lower or 'cartera' in name_lower:
            return 'fa-solid fa-bag-shopping'
        elif 'zapato' in name_lower or 'calzado' in name_lower:
            return 'fa-solid fa-shoe-prints'
        return 'fa-solid fa-tag'

    def __str__(self):
        return self.name


class Size(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="Talla")
    order = models.PositiveIntegerField(default=0, verbose_name="Orden de visualización")

    class Meta:
        verbose_name = "Talla"
        verbose_name_plural = "Tallas"
        ordering = ['order', 'name']

    def __str__(self):
        return self.name


class Color(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Nombre del Color")
    hex_code = models.CharField(max_length=7, default="#000000", verbose_name="Código Hexadecimal")

    class Meta:
        verbose_name = "Color"
        verbose_name_plural = "Colores"
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.hex_code})"


class Product(models.Model):
    name = models.CharField(max_length=200, verbose_name="Nombre de la Prenda")
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="products", verbose_name="Categoría")
    sku = models.CharField(max_length=50, blank=True, verbose_name="Referencia / SKU")
    description = models.TextField(blank=True, verbose_name="Descripción de la Prenda")
    image_url = models.URLField(max_length=500, verbose_name="URL de la Fotografía")
    
    # Precios y Reglas de Mayoreo
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Detal (Unidad)")
    price_wholesale = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio al Mayor")
    wholesale_min_qty = models.PositiveIntegerField(default=6, verbose_name="Unidades Mínimas al Mayor")
    
    # Stock y Estado
    stock = models.PositiveIntegerField(default=50, verbose_name="Stock Disponible")
    is_active = models.BooleanField(default=True, verbose_name="Activo en Catálogo")
    is_featured = models.BooleanField(default=False, verbose_name="Destacado")
    is_immediate = models.BooleanField(default=True, verbose_name="⚡ Disponible ya (Entrega inmediata)")

    # Variantes
    sizes = models.ManyToManyField(Size, blank=True, related_name="products", verbose_name="Tallas Disponibles")
    colors = models.ManyToManyField(Color, blank=True, related_name="products", verbose_name="Colores Disponibles")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Actualización")

    class Meta:
        verbose_name = "Prenda de Ropa"
        verbose_name_plural = "Prendas de Ropa"
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    @property
    def discount_percent(self):
        """Calcula el porcentaje de ahorro al comprar al mayor"""
        if self.price_retail > 0 and self.price_wholesale < self.price_retail:
            diff = self.price_retail - self.price_wholesale
            return round((diff / self.price_retail) * 100)
        return 0

    def get_images_list(self):
        """Retorna hasta un máximo de 4 fotografías de la prenda (WebP prioritarias)"""
        gallery = [img.image.url for img in self.gallery_images.all().order_by('order', 'id')[:4]]
        if gallery:
            return gallery
        if self.image_url:
            return [self.image_url]
        return ["https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80"]

    @property
    def main_image(self):
        imgs = self.get_images_list()
        return imgs[0] if imgs else (self.image_url or "")

    def __str__(self):
        return f"{self.name} - Ref: {self.sku or 'N/A'}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="gallery_images", verbose_name="Prenda")
    image = models.ImageField(upload_to="products/webp/", verbose_name="Foto (WebP)")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="Orden (0 a 3)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Foto de Prenda"
        verbose_name_plural = "Fotos de Prenda (Máx 4 por publicación)"
        ordering = ['order', 'id']

    def __str__(self):
        return f"Foto #{self.order + 1} de {self.product.name}"


class StoreSetting(models.Model):
    store_name = models.CharField(max_length=150, default="SHIBUI", verbose_name="Nombre de la Tienda")
    store_subtitle = models.CharField(max_length=250, default="Catálogo Oficial · Ventas al Detal y al Mayor", verbose_name="Subtítulo")
    store_location = models.CharField(max_length=120, default="Caracas · Envíos Nacionales", verbose_name="Ubicación de la Tienda")
    store_address = models.CharField(max_length=255, default="Calle Principal, Local Comercial #12, Caracas", blank=True, verbose_name="Dirección Física del Negocio")
    owner_name = models.CharField(max_length=100, default="SHIBUI Team", verbose_name="Nombre del Dueño")
    owner_phone = models.CharField(max_length=30, default="+584128945112", verbose_name="WhatsApp del Dueño (con código de país)")
    currency_symbol = models.CharField(max_length=5, default="$", verbose_name="Símbolo de Moneda")
    currency_code = models.CharField(max_length=5, default="USD", verbose_name="Código de Moneda")
    bcv_rate = models.DecimalField(max_digits=10, decimal_places=2, default=45.80, verbose_name="Tasa Bs. / USD (Referencial)")
    announcement = models.CharField(max_length=300, default="🐾 Precios de MAYOREO automáticos desde 6 piezas surtidas o por mínimo del modelo · Envíos MRW y Zoom", verbose_name="Anuncio Superior")
    
    # Mayoreo combinado
    combine_wholesale_enabled = models.BooleanField(default=True, verbose_name="Permitir combinar modelos surtidos para mayoreo")
    global_wholesale_min_units = models.PositiveIntegerField(default=6, verbose_name="Prendas surtidas en carrito para activar mayoreo global")

    # Banner Publicitario / Descuentos Destacados en la Página Principal
    promo_banner_active = models.BooleanField(default=True, verbose_name="Mostrar Banner Publicitario en Inicio")
    promo_badge = models.CharField(max_length=80, default="COLECCIÓN DESTACADA", blank=True, verbose_name="Etiqueta Superior")
    promo_title = models.CharField(max_length=200, default="Body Manga Larga Escote en V", blank=True, verbose_name="Título del Anuncio")
    promo_price = models.CharField(max_length=60, default="$19", blank=True, verbose_name="Precio o Descuento")
    promo_price_note = models.CharField(max_length=100, default="/ Tallas Disponibles", blank=True, verbose_name="Nota de Precio")
    promo_wholesale_note = models.CharField(max_length=200, default="Al Mayor: $13,00 (desde 5 uds)", blank=True, verbose_name="Texto de Descuento o Mayoreo")
    promo_button_text = models.CharField(max_length=60, default="Comprar Ahora", blank=True, verbose_name="Texto del Botón")
    promo_button_link = models.CharField(max_length=300, default="", blank=True, verbose_name="Enlace Personalizado (Opcional)")
    promo_image_url = models.CharField(max_length=500, default="", blank=True, verbose_name="Foto / Imagen del Banner")
    promo_product = models.ForeignKey('Product', on_delete=models.SET_NULL, null=True, blank=True, related_name="promo_banners", verbose_name="Prenda Vinculada")

    class Meta:
        verbose_name = "Configuración de la Tienda"
        verbose_name_plural = "Configuraciones de la Tienda"

    def __str__(self):
        return self.store_name

    @classmethod
    def get_settings(cls):
        settings_obj, _ = cls.objects.get_or_create(id=1)
        return settings_obj


class Order(models.Model):
    STATUS_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Confirmado', 'Confirmado'),
        ('Enviado', 'Enviado'),
        ('Entregado', 'Entregado'),
        ('Cancelado', 'Cancelado'),
    ]

    ORDER_TYPE_CHOICES = [
        ('retail', 'Venta al Detal'),
        ('wholesale', 'Pedido al Mayor'),
    ]

    order_number = models.CharField(max_length=30, unique=True, verbose_name="Número de Orden")
    customer_name = models.CharField(max_length=120, verbose_name="Nombre del Cliente")
    customer_phone = models.CharField(max_length=40, verbose_name="Teléfono / WhatsApp")
    customer_city = models.CharField(max_length=100, blank=True, verbose_name="Ciudad / Región")
    customer_address = models.TextField(blank=True, verbose_name="Dirección de Entrega")
    payment_method = models.CharField(max_length=80, default="Pago Móvil / Transferencia", verbose_name="Método de Pago")
    notes = models.TextField(blank=True, verbose_name="Notas del Pedido")
    
    order_type = models.CharField(max_length=20, choices=ORDER_TYPE_CHOICES, default='retail', verbose_name="Tipo de Tarifa")
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='Pendiente', verbose_name="Estado")
    
    total_units = models.PositiveIntegerField(default=1, verbose_name="Unidades Totales")
    subtotal_retail = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Subtotal Detal")
    wholesale_savings = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Ahorro por Mayoreo")
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, verbose_name="Total a Pagar")

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de Creación")

    class Meta:
        verbose_name = "Pedido"
        verbose_name_plural = "Pedidos"
        ordering = ['-created_at']

    def __str__(self):
        return f"#{self.order_number} - {self.customer_name} ({self.status})"


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items", verbose_name="Pedido")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True, related_name="order_items")
    product_name = models.CharField(max_length=200, verbose_name="Nombre de la Prenda")
    size_name = models.CharField(max_length=30, verbose_name="Talla")
    color_name = models.CharField(max_length=50, verbose_name="Color")
    color_hex = models.CharField(max_length=10, default="#000000", verbose_name="Color Hex")
    
    quantity = models.PositiveIntegerField(default=1, verbose_name="Cantidad")
    price_retail = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Detal")
    price_applied = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio Unitario Aplicado")
    is_wholesale_applied = models.BooleanField(default=False, verbose_name="¿Aplicó Precio al Mayor?")
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, verbose_name="Subtotal")

    class Meta:
        verbose_name = "Ítem de Pedido"
        verbose_name_plural = "Ítems de Pedido"

    def __str__(self):
        return f"{self.product_name} ({self.size_name}, {self.color_name}) x {self.quantity}"


class CustomerProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="customer_profile", verbose_name="Cuenta de Usuario")
    phone = models.CharField(max_length=40, blank=True, default="", verbose_name="Teléfono / WhatsApp")
    city = models.CharField(max_length=100, blank=True, default="", verbose_name="Ciudad / Estado")
    preferred_size = models.CharField(max_length=20, blank=True, default="S", verbose_name="Talla Habitual")

    class Meta:
        verbose_name = "Perfil de Cliente"
        verbose_name_plural = "Perfiles de Clientes"

    def __str__(self):
        return f"Perfil de {self.user.get_full_name() or self.user.username}"


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews", verbose_name="Prenda / Conjunto")
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="reviews", verbose_name="Usuario Registrado")
    author_name = models.CharField(max_length=100, verbose_name="Nombre del Usuario")
    rating = models.PositiveSmallIntegerField(default=5, verbose_name="Calificación (1-5)")
    size_purchased = models.CharField(max_length=20, blank=True, default="M", verbose_name="Talla Comprada")
    fit_feedback = models.CharField(max_length=40, blank=True, default="Fiel a la talla", verbose_name="Ajuste de la Prenda")
    comment = models.TextField(verbose_name="Comentario / Reseña")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Fecha")

    class Meta:
        verbose_name = "Reseña de Prenda"
        verbose_name_plural = "Reseñas de Prendas"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.author_name} ({self.rating}★) - {self.product.name}"


