import io
import uuid
import json
from decimal import Decimal
import urllib.parse
from PIL import Image, ImageOps
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db.models import Max, Count, Q, F
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings as django_settings
from .models import Category, Size, Color, Product, StoreSetting, Order, OrderItem, Review, CustomerProfile, ProductImage


def process_uploaded_image_to_webp(uploaded_file, max_dimension=1400, quality=82):
    """
    Abre una imagen subida (JPG, PNG, etc.), corrige su orientación EXIF para móviles,
    redimensiona proporcionalmente si supera max_dimension,
    y la exporta comprimida en formato WebP optimizado para máxima velocidad de carga.
    """
    img = Image.open(uploaded_file)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ('RGB', 'RGBA'):
        img = img.convert('RGB')

    img.thumbnail((max_dimension, max_dimension), Image.Resampling.LANCZOS)

    output = io.BytesIO()
    img.save(output, format='WEBP', quality=quality, method=6)
    output.seek(0)

    filename = f"{uuid.uuid4().hex[:14]}.webp"
    return ContentFile(output.getvalue(), name=filename)


def _serialize_customer_user(user):
    """Serializa los datos de la cuenta registrada del comprador."""
    if not user or not user.is_authenticated:
        return {
            'is_authenticated': False,
            'id': None,
            'username': '',
            'name': '',
            'email': '',
            'phone': '',
            'city': '',
            'preferred_size': 'S'
        }
    profile, _ = CustomerProfile.objects.get_or_create(user=user)
    full_name = (user.first_name or '').strip() or user.username
    return {
        'is_authenticated': True,
        'id': user.id,
        'username': user.username,
        'name': full_name,
        'email': user.email or '',
        'phone': profile.phone or '',
        'city': profile.city or '',
        'preferred_size': profile.preferred_size or 'S'
    }


def catalog_index(request):
    """Vista principal del catálogo para compradores y clientes."""
    settings = StoreSetting.get_settings()
    bcv_rate = float(settings.bcv_rate or Decimal('45.80'))
    
    # Queryset base de productos activos
    products_qs = Product.objects.filter(is_active=True).prefetch_related('sizes', 'colors', 'category', 'reviews', 'gallery_images')
    
    # Filtros
    search_query = request.GET.get('q', '').strip()
    category_slug = request.GET.get('categoria', '').strip()
    size_filter = request.GET.get('talla', '').strip()
    color_filter = request.GET.get('color', '').strip()
    price_max = request.GET.get('precio_max', '').strip()
    only_wholesale = request.GET.get('solo_mayor', '').strip()
    only_immediate = request.GET.get('disponible', '').strip()

    if search_query:
        products_qs = products_qs.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(sku__icontains=search_query) |
            Q(category__name__icontains=search_query)
        )

    if category_slug and category_slug != 'todas':
        products_qs = products_qs.filter(category__slug=category_slug)

    if size_filter and size_filter != 'todas':
        products_qs = products_qs.filter(sizes__name=size_filter).distinct()

    if color_filter and color_filter != 'todos':
        products_qs = products_qs.filter(colors__name=color_filter).distinct()

    if price_max:
        try:
            products_qs = products_qs.filter(price_retail__lte=Decimal(price_max))
        except Exception:
            pass

    if only_wholesale == '1':
        products_qs = products_qs.filter(price_wholesale__lt=F('price_retail'))

    if only_immediate == '1':
        products_qs = products_qs.filter(is_immediate=True)

    # Datos complementarios para los filtros
    categories = Category.objects.annotate(prod_count=Count('products')).all()
    sizes = Size.objects.all().order_by('order', 'name')
    colors = Color.objects.all().order_by('name')

    # Serialización a JSON para la interactividad del modal, reseñas, carrito y selección de tallas/colores
    products_list = []
    for p in products_qs:
        p_colors = list(p.colors.all())
        p_sizes = list(p.sizes.all())
        p_reviews = list(p.reviews.all())
        p.colors_preview = p_colors[:3]
        p.extra_colors_count = max(0, len(p_colors) - 3)
        p.price_retail_bs = round(float(p.price_retail) * bcv_rate, 2)
        p.price_wholesale_bs = round(float(p.price_wholesale) * bcv_rate, 2)

        reviews_count = len(p_reviews)
        avg_rating = round(sum(r.rating for r in p_reviews) / reviews_count, 1) if reviews_count > 0 else 5.0
        p.avg_rating = avg_rating
        p.reviews_count = reviews_count

        products_list.append({
            'id': p.id,
            'name': p.name,
            'category': p.category.name,
            'category_slug': p.category.slug,
            'sku': p.sku or 'N/A',
            'description': p.description,
            'image_url': p.main_image,
            'images': p.get_images_list(),
            'price_retail': float(p.price_retail),
            'price_wholesale': float(p.price_wholesale),
            'price_retail_bs': p.price_retail_bs,
            'price_wholesale_bs': p.price_wholesale_bs,
            'wholesale_min_qty': p.wholesale_min_qty,
            'discount_percent': p.discount_percent,
            'stock': p.stock,
            'is_immediate': p.is_immediate,
            'sizes': [s.name for s in p_sizes],
            'colors': [{'name': c.name, 'hex': c.hex_code} for c in p_colors],
            'avg_rating': avg_rating,
            'reviews_count': reviews_count,
            'reviews': [
                {
                    'id': r.id,
                    'author_name': r.author_name,
                    'rating': r.rating,
                    'size_purchased': r.size_purchased,
                    'fit_feedback': r.fit_feedback,
                    'comment': r.comment,
                    'date': r.created_at.strftime('%d/%m/%Y')
                }
                for r in p_reviews
            ]
        })

    active_filters_count = 0
    if search_query: active_filters_count += 1
    if category_slug and category_slug != 'todas': active_filters_count += 1
    if size_filter and size_filter != 'todas': active_filters_count += 1
    if color_filter and color_filter != 'todos': active_filters_count += 1
    if price_max and Decimal(price_max) < 100: active_filters_count += 1
    if only_wholesale == '1': active_filters_count += 1
    if only_immediate == '1': active_filters_count += 1

    recent_reviews = Review.objects.select_related('product').all()[:12]

    context = {
        'products': products_qs,
        'products_json': json.dumps(products_list),
        'categories': categories,
        'sizes': sizes,
        'colors': colors,
        'current_category': category_slug or 'todas',
        'current_size': size_filter or 'todas',
        'current_color': color_filter or 'todos',
        'search_query': search_query,
        'price_max': price_max or '100',
        'only_wholesale': only_wholesale == '1',
        'only_immediate': only_immediate == '1',
        'active_filters_count': active_filters_count,
        'total_products_count': Product.objects.filter(is_active=True).count(),
        'store_settings': settings,
        'bcv_rate': bcv_rate,
        'recent_reviews': recent_reviews,
        'current_user_json': json.dumps(_serialize_customer_user(request.user)),
    }
    return render(request, 'catalog/index.html', context)


def owner_login(request):
    """Acceso privado exclusivo para el administrador de la tienda (no visible para compradores)."""
    if request.session.get('is_store_owner'):
        return redirect('catalog:admin_dashboard')

    settings = StoreSetting.get_settings()
    error = None

    if request.method == 'POST':
        username = request.POST.get('username', '').strip().lower()
        password = request.POST.get('password', '').strip()
        if username in ('admin', 'administrador', 'dueno', 'dueño') and password == '1234':
            request.session['is_store_owner'] = True
            return redirect('catalog:admin_dashboard')
        else:
            error = "Credenciales incorrectas. Usa el usuario 'admin' y clave '1234'."

    return render(request, 'catalog/owner_login.html', {
        'store_settings': settings,
        'error': error
    })


def owner_logout(request):
    """Cierra la sesión privada del administrador y redirige al catálogo."""
    request.session.pop('is_store_owner', None)
    return redirect('catalog:index')


def _find_user_by_email_and_phone(email, phone):
    """Busca y valida una cuenta registrada usando únicamente Correo Electrónico y Teléfono."""
    email_clean = (email or '').strip().lower()
    phone_digits = ''.join(c for c in (phone or '') if c.isdigit())
    if not email_clean or not phone_digits:
        return None

    user_obj = User.objects.filter(Q(email__iexact=email_clean) | Q(username__iexact=email_clean)).first()
    if not user_obj:
        return None

    profile, _ = CustomerProfile.objects.get_or_create(user=user_obj)
    stored_digits = ''.join(c for c in (profile.phone or '') if c.isdigit())

    # Coincidencia exacta o últimos 7 dígitos del teléfono
    if stored_digits and (stored_digits == phone_digits or stored_digits[-7:] == phone_digits[-7:]):
        return user_obj
    return None


def customer_login_view(request):
    """Página normal de Inicio de Sesión usando Correo Electrónico y Número de Teléfono."""
    if request.user.is_authenticated:
        return redirect('catalog:customer_account')

    settings = StoreSetting.get_settings()
    error = None

    if request.method == 'POST':
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()

        user = _find_user_by_email_and_phone(email, phone)
        if user:
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            next_url = request.GET.get('next') or request.POST.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('catalog:customer_account')
        else:
            error = "No encontramos una cuenta con ese correo y número de teléfono. Verifica tus datos o regístrate."

    return render(request, 'catalog/customer_login.html', {
        'store_settings': settings,
        'error': error,
        'current_user_json': json.dumps(_serialize_customer_user(request.user)),
    })


def customer_register_view(request):
    """Página normal de Registro de Cuenta sin nombre de usuario (solo Nombre, Correo y Teléfono)."""
    if request.user.is_authenticated:
        return redirect('catalog:customer_account')

    settings = StoreSetting.get_settings()
    error = None

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        phone = request.POST.get('phone', '').strip()
        city = request.POST.get('city', '').strip()
        preferred_size = request.POST.get('preferred_size', 'S').strip() or 'S'

        phone_digits = ''.join(c for c in phone if c.isdigit())

        if not name or not email or not phone_digits:
            error = "Por favor completa tu nombre, correo electrónico y número de teléfono."
        elif User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
            error = "Ese correo electrónico ya está registrado. Por favor inicia sesión con tu correo y teléfono."
        else:
            user = User.objects.create_user(
                username=email,
                email=email,
                password=phone_digits,
                first_name=name
            )
            CustomerProfile.objects.update_or_create(
                user=user,
                defaults={
                    'phone': phone,
                    'city': city,
                    'preferred_size': preferred_size
                }
            )
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            return redirect('catalog:customer_account')

    return render(request, 'catalog/customer_register.html', {
        'store_settings': settings,
        'sizes': Size.objects.all().order_by('order', 'name'),
        'error': error,
        'current_user_json': json.dumps(_serialize_customer_user(request.user)),
    })


def customer_logout_view(request):
    """Cierra la sesión del usuario registrado."""
    logout(request)
    return redirect('catalog:index')


def customer_account_view(request):
    """Página de Mi Cuenta para el usuario registrado (perfil y reseñas de ropa)."""
    if not request.user.is_authenticated:
        return redirect('catalog:customer_login')

    settings = StoreSetting.get_settings()
    profile, _ = CustomerProfile.objects.get_or_create(user=request.user)
    products = Product.objects.filter(is_active=True)
    success_msg = None
    error_msg = None

    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'update_profile':
            name = request.POST.get('name', '').strip()
            email = request.POST.get('email', '').strip()
            phone = request.POST.get('phone', '').strip()
            city = request.POST.get('city', '').strip()
            preferred_size = request.POST.get('preferred_size', 'S').strip() or 'S'

            if name:
                request.user.first_name = name
            request.user.email = email
            request.user.save()

            profile.phone = phone
            profile.city = city
            profile.preferred_size = preferred_size
            profile.save()
            success_msg = "Tus datos de cuenta han sido actualizados."

        elif action == 'add_review':
            product_id = request.POST.get('product_id')
            rating = int(request.POST.get('rating', 5))
            size_purchased = request.POST.get('size_purchased', 'S').strip()
            fit_feedback = request.POST.get('fit_feedback', 'Fiel a la talla').strip()
            comment = request.POST.get('comment', '').strip()

            if product_id and comment:
                prod = Product.objects.filter(id=product_id).first()
                if prod:
                    Review.objects.create(
                        product=prod,
                        user=request.user,
                        author_name=(request.user.first_name or '').strip() or request.user.username,
                        rating=max(1, min(5, rating)),
                        size_purchased=size_purchased or 'Única',
                        fit_feedback=fit_feedback or 'Fiel a la talla',
                        comment=comment
                    )
                    success_msg = f"¡Tu reseña sobre '{prod.name}' fue publicada con éxito!"
            else:
                error_msg = "Por favor selecciona una prenda y escribe tu comentario."

    my_reviews = Review.objects.filter(user=request.user).select_related('product')
    all_reviews = Review.objects.select_related('product').all()[:15]

    return render(request, 'catalog/customer_account.html', {
        'store_settings': settings,
        'profile': profile,
        'products': products,
        'sizes': Size.objects.all().order_by('order', 'name'),
        'my_reviews': my_reviews,
        'all_reviews': all_reviews,
        'success_msg': success_msg,
        'error_msg': error_msg,
        'current_user_json': json.dumps(_serialize_customer_user(request.user)),
    })


def admin_dashboard(request):
    """Panel de control privado del dueño de la tienda de ropa."""
    if not request.session.get('is_store_owner'):
        return redirect('catalog:owner_login')

    settings = StoreSetting.get_settings()
    products = Product.objects.all().select_related('category').prefetch_related('sizes', 'colors', 'gallery_images')
    orders = Order.objects.all().prefetch_related('items')
    categories = Category.objects.annotate(prod_count=Count('products')).all().order_by('name')
    sizes = Size.objects.all().order_by('order', 'name')
    colors = Color.objects.all().order_by('name')

    status_filter = request.GET.get('estado', 'Todos')
    if status_filter != 'Todos':
        orders = orders.filter(status=status_filter)

    # Métricas clave
    total_stock = sum(p.stock for p in products)
    wholesale_items_count = sum(1 for p in products if p.price_wholesale < p.price_retail)
    pending_orders_count = Order.objects.filter(status='Pendiente').count()
    total_sales = sum(o.total for o in Order.objects.exclude(status='Cancelado'))

    # JSON de productos para modal de edición
    products_admin_list = []
    for p in products:
        products_admin_list.append({
            'id': p.id,
            'name': p.name,
            'category_id': p.category.id,
            'sku': p.sku or '',
            'description': p.description,
            'image_url': p.main_image,
            'images': p.get_images_list(),
            'price_retail': float(p.price_retail),
            'price_wholesale': float(p.price_wholesale),
            'wholesale_min_qty': p.wholesale_min_qty,
            'stock': p.stock,
            'is_active': p.is_active,
            'is_immediate': p.is_immediate,
            'size_ids': [s.id for s in p.sizes.all()],
            'color_ids': [c.id for c in p.colors.all()]
        })

    context = {
        'products': products,
        'products_admin_json': json.dumps(products_admin_list),
        'orders': orders,
        'categories': categories,
        'sizes': sizes,
        'colors': colors,
        'store_settings': settings,
        'status_filter': status_filter,
        'total_stock': total_stock,
        'wholesale_items_count': wholesale_items_count,
        'pending_orders_count': pending_orders_count,
        'total_sales': total_sales,
    }
    return render(request, 'catalog/admin_panel.html', context)


@csrf_exempt
def api_create_order(request):
    """Endpoint para registrar pedidos y generar el enlace de WhatsApp formateado (Estilo Dobelu)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        settings = StoreSetting.get_settings()
        bcv_rate = Decimal(str(settings.bcv_rate or '45.80'))

        customer_name = data.get('customerName', '').strip()
        customer_dni = data.get('customerDni', '').strip()
        customer_phone = data.get('customerPhone', '').strip()
        delivery_type = data.get('deliveryType', 'Envío Nacional (MRW / Zoom)').strip()
        customer_city = data.get('customerCity', '').strip()
        customer_address = data.get('customerAddress', '').strip()
        payment_method = data.get('paymentMethod', 'Pago Móvil / Divisas')
        notes = data.get('notes', '').strip()
        items = data.get('items', [])

        if not customer_name or not customer_phone or not items:
            return JsonResponse({'status': 'error', 'message': 'Faltan campos obligatorios'}, status=400)

        total_units = sum(int(item.get('quantity', 1)) for item in items)
        is_global_wholesale = settings.combine_wholesale_enabled and total_units >= settings.global_wholesale_min_units

        # Contar unidades por producto
        prod_units_map = {}
        for item in items:
            pid = item.get('productId')
            prod_units_map[pid] = prod_units_map.get(pid, 0) + int(item.get('quantity', 1))

        # Generar número de pedido
        import random
        order_number = f"DB-{random.randint(1000, 9999)}"

        subtotal_retail = Decimal('0.00')
        total_final = Decimal('0.00')
        order_items_to_create = []
        whatsapp_items_text = []

        for idx, item in enumerate(items, 1):
            pid = item.get('productId')
            qty = int(item.get('quantity', 1))
            size = item.get('size', 'Única')
            color_data = item.get('color', {})
            color_name = color_data.get('name', 'Estándar') if isinstance(color_data, dict) else str(color_data)
            color_hex = color_data.get('hex', '#000000') if isinstance(color_data, dict) else '#000000'

            product = Product.objects.filter(id=pid).first()
            if not product:
                continue

            # Verificar si aplica mayoreo
            product_total_in_cart = prod_units_map.get(pid, qty)
            qualifies_wholesale = is_global_wholesale or (product_total_in_cart >= product.wholesale_min_qty)

            unit_price_applied = product.price_wholesale if (qualifies_wholesale and product.price_wholesale > 0) else product.price_retail
            item_retail = product.price_retail * qty
            item_final = unit_price_applied * qty

            subtotal_retail += item_retail
            total_final += item_final

            order_items_to_create.append({
                'product': product,
                'product_name': product.name,
                'size_name': size,
                'color_name': color_name,
                'color_hex': color_hex,
                'quantity': qty,
                'price_retail': product.price_retail,
                'price_applied': unit_price_applied,
                'is_wholesale_applied': qualifies_wholesale,
                'subtotal': item_final
            })

            tag = "(Precio Mayorista)" if qualifies_wholesale else "(Precio Detal)"
            whatsapp_items_text.append(
                f"*{product.name}* x{qty}\n"
                f"Talla: *{size}*\n"
                f"Color: *{color_name}*\n"
                f"Precio unitario: *{settings.currency_symbol}{unit_price_applied:.2f} USD* {tag}"
            )

        wholesale_savings = subtotal_retail - total_final
        total_bs = total_final * bcv_rate
        order_type = 'wholesale' if wholesale_savings > 0 else 'retail'

        full_notes = notes
        if customer_dni:
            full_notes = f"Cédula/ID: {customer_dni} | Entrega: {delivery_type}" + (f" | {notes}" if notes else "")
        elif delivery_type:
            full_notes = f"Entrega: {delivery_type}" + (f" | {notes}" if notes else "")

        # Crear Orden en Base de Datos Django
        order = Order.objects.create(
            order_number=order_number,
            customer_name=customer_name,
            customer_phone=customer_phone,
            customer_city=customer_city or delivery_type,
            customer_address=customer_address or delivery_type,
            payment_method=payment_method,
            notes=full_notes,
            order_type=order_type,
            status='Pendiente',
            total_units=total_units,
            subtotal_retail=subtotal_retail,
            wholesale_savings=wholesale_savings,
            total=total_final
        )

        for oi in order_items_to_create:
            OrderItem.objects.create(
                order=order,
                product=oi['product'],
                product_name=oi['product_name'],
                size_name=oi['size_name'],
                color_name=oi['color_name'],
                color_hex=oi['color_hex'],
                quantity=oi['quantity'],
                price_retail=oi['price_retail'],
                price_applied=oi['price_applied'],
                is_wholesale_applied=oi['is_wholesale_applied'],
                subtotal=oi['subtotal']
            )

        # Formatear Mensaje estilo Dobelu Shop para WhatsApp
        owner_phone_digits = ''.join(c for c in settings.owner_phone if c.isdigit())
        msg = f"🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢\n\n"
        msg += f"-- *ORDEN #{order.order_number} ({settings.store_name})* --\n\n"
        msg += f"-- *DATOS DEL CLIENTE* --\n"
        msg += f"Nombre: *{customer_name}*\n"
        if customer_dni:
            msg += f"Cédula: *{customer_dni}*\n"
        msg += f"Teléfono: *{customer_phone}*\n\n"
        msg += f"-- *DATOS DE ENTREGA* --\n"
        msg += f"Tipo de entrega: *{delivery_type}*\n"
        if customer_city:
            msg += f"Estado / Ciudad: *{customer_city}*\n"
        if customer_address:
            msg += f"Dirección / Agencia: *{customer_address}*\n"
        if 'retiro' in delivery_type.lower() and settings.store_address:
            msg += f"Punto de Retiro: *{settings.store_address}*\n"
        msg += f"\n-- *PRODUCTOS A PEDIR* --\n\n"
        msg += "\n\n".join(whatsapp_items_text) + "\n\n"
        msg += f"-- *DETALLES DE LA ORDEN* --\n"
        msg += f"Unidades totales: *{total_units}*\n"
        msg += f"Modalidad aplicada: *{'AL MAYOR 🔥' if order_type == 'wholesale' else 'AL DETAL'}*\n"
        if wholesale_savings > 0:
            msg += f"Ahorro por mayoreo: *-{settings.currency_symbol}{wholesale_savings:.2f} USD*\n"
        msg += f"Total en divisas: *{settings.currency_symbol}{total_final:.2f} USD*\n"
        msg += f"Total en bolívares: *Bs. {total_bs:.2f}*\n\n"
        msg += f"-- *FORMA DE PAGO* --\n"
        msg += f"Método seleccionado: *{payment_method}*\n"
        if notes:
            msg += f"Nota adicional: _{notes}_\n"
        msg += f"\n🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢🟢"

        encoded_msg = urllib.parse.quote(msg)
        whatsapp_url = f"https://wa.me/{owner_phone_digits}?text={encoded_msg}"

        return JsonResponse({
            'status': 'success',
            'order_number': order.order_number,
            'whatsapp_url': whatsapp_url,
            'total': float(total_final),
            'total_bs': float(round(total_bs, 2)),
            'total_units': total_units,
            'wholesale_savings': float(wholesale_savings)
        })

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_upload_product_images(request):
    """
    Recibe fotos de prenda subidas desde el dispositivo (máx 4 por publicación),
    las convierte automáticamente a WebP optimizado y retorna sus URLs directas.
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    files = request.FILES.getlist('images') or request.FILES.getlist('photos')
    if not files and 'image' in request.FILES:
        files = [request.FILES['image']]

    if not files:
        return JsonResponse({'status': 'error', 'message': 'No se seleccionó ningún archivo de imagen.'}, status=400)

    # Límite estricto de máximo 4 fotos por publicación
    files = files[:4]
    saved_images = []

    for idx, f in enumerate(files):
        try:
            webp_content = process_uploaded_image_to_webp(f)
            path = default_storage.save(f"products/webp/{webp_content.name}", webp_content)
            url = default_storage.url(path)
            saved_images.append({
                'url': url,
                'filename': webp_content.name,
                'order': idx
            })
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error convirtiendo imagen a WebP: {str(e)}'}, status=500)

    return JsonResponse({
        'status': 'success',
        'message': f'{len(saved_images)} foto(s) convertida(s) automáticamente a WebP.',
        'images': saved_images
    })


@csrf_exempt
def api_add_product(request):
    """Endpoint para que el dueño agregue una nueva prenda con hasta 4 fotos WebP al catálogo."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name', '').strip()
        category_id = data.get('category_id')
        sku = data.get('sku', '').strip()
        description = data.get('description', '').strip()
        image_url = data.get('image_url', '').strip()
        images = [str(u).strip() for u in data.get('images', []) if str(u).strip()][:4]
        price_retail = Decimal(str(data.get('price_retail', 0)))
        price_wholesale = Decimal(str(data.get('price_wholesale', 0)))
        wholesale_min_qty = int(data.get('wholesale_min_qty', 6))
        stock = int(data.get('stock', 50))
        is_immediate = bool(data.get('is_immediate', True))
        size_ids = data.get('size_ids', [])
        color_ids = data.get('color_ids', [])

        if not images and image_url:
            images = [image_url]

        primary_image = images[0] if images else (image_url or "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80")
        category = get_object_or_404(Category, id=category_id)

        product = Product.objects.create(
            name=name,
            category=category,
            sku=sku,
            description=description,
            image_url=primary_image,
            price_retail=price_retail,
            price_wholesale=price_wholesale,
            wholesale_min_qty=wholesale_min_qty,
            stock=stock,
            is_immediate=is_immediate,
            is_active=True
        )

        for idx, img_url in enumerate(images):
            rel_path = img_url
            if rel_path.startswith(django_settings.MEDIA_URL):
                rel_path = rel_path[len(django_settings.MEDIA_URL):]
            ProductImage.objects.create(product=product, image=rel_path, order=idx)

        if size_ids:
            product.sizes.set(Size.objects.filter(id__in=size_ids))
        if color_ids:
            product.colors.set(Color.objects.filter(id__in=color_ids))

        return JsonResponse({'status': 'success', 'product_id': product.id, 'message': 'Prenda agregada con éxito'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_edit_product(request, product_id):
    """Endpoint para que el dueño edite una prenda existente y sus hasta 4 fotos WebP."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        product = get_object_or_404(Product, id=product_id)
        data = json.loads(request.body.decode('utf-8'))

        product.name = data.get('name', product.name).strip()
        if 'category_id' in data:
            product.category = get_object_or_404(Category, id=data['category_id'])
        product.sku = data.get('sku', product.sku).strip()
        product.description = data.get('description', product.description).strip()
        
        if 'images' in data:
            images = [str(u).strip() for u in data.get('images', []) if str(u).strip()][:4]
            if images:
                product.image_url = images[0]
                product.gallery_images.all().delete()
                for idx, img_url in enumerate(images):
                    rel_path = img_url
                    if rel_path.startswith(django_settings.MEDIA_URL):
                        rel_path = rel_path[len(django_settings.MEDIA_URL):]
                    ProductImage.objects.create(product=product, image=rel_path, order=idx)
        elif 'image_url' in data and data['image_url'].strip():
            product.image_url = data.get('image_url').strip()

        product.price_retail = Decimal(str(data.get('price_retail', product.price_retail)))
        product.price_wholesale = Decimal(str(data.get('price_wholesale', product.price_wholesale)))
        product.wholesale_min_qty = int(data.get('wholesale_min_qty', product.wholesale_min_qty))
        product.stock = int(data.get('stock', product.stock))
        if 'is_active' in data:
            product.is_active = bool(data['is_active'])
        if 'is_immediate' in data:
            product.is_immediate = bool(data['is_immediate'])

        product.save()

        if 'size_ids' in data:
            product.sizes.set(Size.objects.filter(id__in=data['size_ids']))
        if 'color_ids' in data:
            product.colors.set(Color.objects.filter(id__in=data['color_ids']))

        return JsonResponse({'status': 'success', 'message': 'Prenda actualizada con éxito'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_delete_product(request, product_id):
    """Endpoint para eliminar una prenda del catálogo."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return JsonResponse({'status': 'success', 'message': 'Prenda eliminada correctamente'})


@csrf_exempt
def api_update_order_status(request, order_id):
    """Endpoint para cambiar el estado de un pedido (Pendiente, Confirmado, Enviado, etc)."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        order = get_object_or_404(Order, id=order_id)
        data = json.loads(request.body.decode('utf-8'))
        new_status = data.get('status')
        if new_status in dict(Order.STATUS_CHOICES):
            order.status = new_status
            order.save()
            return JsonResponse({'status': 'success', 'new_status': new_status})
        return JsonResponse({'status': 'error', 'message': 'Estado inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_update_settings(request):
    """Endpoint para actualizar la configuración de la tienda incluyendo ubicación y dirección física."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        settings = StoreSetting.get_settings()
        settings.store_name = data.get('store_name', settings.store_name).strip()
        settings.store_subtitle = data.get('store_subtitle', settings.store_subtitle).strip()
        settings.store_location = data.get('store_location', settings.store_location).strip()
        settings.store_address = data.get('store_address', settings.store_address).strip()
        settings.owner_name = data.get('owner_name', settings.owner_name).strip()
        settings.owner_phone = data.get('owner_phone', settings.owner_phone).strip()
        settings.currency_symbol = data.get('currency_symbol', settings.currency_symbol).strip()
        if 'bcv_rate' in data and data.get('bcv_rate'):
            settings.bcv_rate = Decimal(str(data.get('bcv_rate')))
        settings.announcement = data.get('announcement', settings.announcement).strip()
        settings.combine_wholesale_enabled = bool(data.get('combine_wholesale_enabled', True))
        settings.global_wholesale_min_units = int(data.get('global_wholesale_min_units', 6))
        settings.save()
        return JsonResponse({'status': 'success', 'message': 'Ajustes guardados correctamente'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_reset_demo(request):
    """Restaura los datos de demostración."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    from django.core.management import call_command
    call_command('populate_demo')
    return JsonResponse({'status': 'success', 'message': 'Catálogo restablecido a valores demo'})


@csrf_exempt
def api_user_register(request):
    """Registra una nueva cuenta de usuario comprador usando Nombre, Correo y Teléfono."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name', '').strip()
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()
        city = data.get('city', '').strip()
        preferred_size = data.get('preferred_size', 'S').strip() or 'S'

        phone_digits = ''.join(c for c in phone if c.isdigit())

        if not name or not email or not phone_digits:
            return JsonResponse({'status': 'error', 'message': 'Por favor completa tu nombre, correo electrónico y teléfono.'}, status=400)

        if User.objects.filter(Q(email__iexact=email) | Q(username__iexact=email)).exists():
            return JsonResponse({'status': 'error', 'message': 'Ese correo electrónico ya está registrado. Inicia sesión con tu correo y teléfono.'}, status=400)

        user = User.objects.create_user(
            username=email,
            email=email,
            password=phone_digits,
            first_name=name
        )
        CustomerProfile.objects.update_or_create(
            user=user,
            defaults={
                'phone': phone,
                'city': city,
                'preferred_size': preferred_size
            }
        )
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({
            'status': 'success',
            'message': '¡Cuenta creada con éxito! Ya puedes comentar y calificar prendas.',
            'user': _serialize_customer_user(user)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_user_login(request):
    """Inicia sesión con Correo Electrónico y Número de Teléfono."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        email = data.get('email', '').strip().lower()
        phone = data.get('phone', '').strip()

        if not email or not phone:
            return JsonResponse({'status': 'error', 'message': 'Ingresa tu correo electrónico y número de teléfono.'}, status=400)

        user = _find_user_by_email_and_phone(email, phone)
        if not user:
            return JsonResponse({'status': 'error', 'message': 'No encontramos una cuenta con ese correo y teléfono.'}, status=401)

        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        return JsonResponse({
            'status': 'success',
            'message': f'¡Bienvenido/a de nuevo, {user.first_name or user.email}!',
            'user': _serialize_customer_user(user)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_user_logout(request):
    """Cierra la sesión de la cuenta de usuario."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    logout(request)
    return JsonResponse({
        'status': 'success',
        'user': _serialize_customer_user(None)
    })


@csrf_exempt
def api_user_update_profile(request):
    """Actualiza los datos del perfil de un usuario registrado."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({'status': 'error', 'require_auth': True, 'message': 'Debes iniciar sesión primero.'}, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
        name = data.get('name', '').strip()
        phone = data.get('phone', '').strip()
        city = data.get('city', '').strip()
        preferred_size = data.get('preferred_size', 'S').strip() or 'S'

        if name:
            request.user.first_name = name
            request.user.save()

        CustomerProfile.objects.update_or_create(
            user=request.user,
            defaults={
                'phone': phone,
                'city': city,
                'preferred_size': preferred_size
            }
        )
        return JsonResponse({
            'status': 'success',
            'message': 'Datos de tu cuenta actualizados correctamente.',
            'user': _serialize_customer_user(request.user)
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_add_review(request):
    """Endpoint para que SOLO los usuarios con cuenta registrada publiquen una reseña sobre una prenda o conjunto."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    if not request.user.is_authenticated:
        return JsonResponse({
            'status': 'error',
            'require_auth': True,
            'message': 'Solo las personas con una cuenta registrada pueden comentar. Por favor inicia sesión o crea tu cuenta.'
        }, status=401)

    try:
        data = json.loads(request.body.decode('utf-8'))
        product_id = data.get('product_id')
        rating = int(data.get('rating', 5))
        size_purchased = data.get('size_purchased', 'M').strip()
        fit_feedback = data.get('fit_feedback', 'Fiel a la talla').strip()
        comment = data.get('comment', '').strip()

        author_name = (request.user.first_name or '').strip() or request.user.username

        if not product_id or not comment:
            return JsonResponse({'status': 'error', 'message': 'Por favor escribe tu comentario sobre la prenda.'}, status=400)

        rating = max(1, min(5, rating))
        product = get_object_or_404(Product, id=product_id)

        review = Review.objects.create(
            product=product,
            user=request.user,
            author_name=author_name,
            rating=rating,
            size_purchased=size_purchased or 'Única',
            fit_feedback=fit_feedback or 'Fiel a la talla',
            comment=comment
        )

        all_reviews = list(product.reviews.all())
        reviews_count = len(all_reviews)
        avg_rating = round(sum(r.rating for r in all_reviews) / reviews_count, 1) if reviews_count > 0 else 5.0

        return JsonResponse({
            'status': 'success',
            'avg_rating': avg_rating,
            'reviews_count': reviews_count,
            'review': {
                'id': review.id,
                'product_id': product.id,
                'product_name': product.name,
                'author_name': review.author_name,
                'rating': review.rating,
                'size_purchased': review.size_purchased,
                'fit_feedback': review.fit_feedback,
                'comment': review.comment,
                'date': review.created_at.strftime('%d/%m/%Y')
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_save_size(request):
    """Crea o edita una talla personalizada en la base de datos."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        size_id = data.get('id')
        name = data.get('name', '').strip()
        order = int(data.get('order', 0) or 0)

        if not name:
            return JsonResponse({'status': 'error', 'message': 'El nombre de la talla es obligatorio.'}, status=400)

        if size_id:
            size_obj = get_object_or_404(Size, id=size_id)
            size_obj.name = name
            size_obj.order = order
            size_obj.save()
        else:
            existing = Size.objects.filter(name__iexact=name).first()
            if existing:
                existing.name = name
                if order:
                    existing.order = order
                existing.save()
                size_obj = existing
            else:
                if order == 0:
                    max_order = Size.objects.aggregate(Max('order'))['order__max'] or 0
                    order = max_order + 1
                size_obj = Size.objects.create(name=name, order=order)

        return JsonResponse({
            'status': 'success',
            'size': {
                'id': size_obj.id,
                'name': size_obj.name,
                'order': size_obj.order
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_delete_size(request, size_id):
    """Elimina una talla del sistema."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        size_obj = get_object_or_404(Size, id=size_id)
        size_obj.delete()
        return JsonResponse({'status': 'success', 'message': 'Talla eliminada correctamente.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_save_color(request):
    """Crea o edita un color personalizado con su código hexadecimal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        color_id = data.get('id')
        name = data.get('name', '').strip()
        hex_code = data.get('hex_code', '#000000').strip() or '#000000'
        if not hex_code.startswith('#'):
            hex_code = '#' + hex_code

        if not name:
            return JsonResponse({'status': 'error', 'message': 'El nombre del color es obligatorio.'}, status=400)

        if color_id:
            color_obj = get_object_or_404(Color, id=color_id)
            color_obj.name = name
            color_obj.hex_code = hex_code
            color_obj.save()
        else:
            existing = Color.objects.filter(name__iexact=name).first()
            if existing:
                existing.name = name
                existing.hex_code = hex_code
                existing.save()
                color_obj = existing
            else:
                color_obj = Color.objects.create(name=name, hex_code=hex_code)

        return JsonResponse({
            'status': 'success',
            'color': {
                'id': color_obj.id,
                'name': color_obj.name,
                'hex_code': color_obj.hex_code
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_delete_color(request, color_id):
    """Elimina un color del sistema."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        color_obj = get_object_or_404(Color, id=color_id)
        color_obj.delete()
        return JsonResponse({'status': 'success', 'message': 'Color eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_upload_category_image(request):
    """Sube una imagen para el ícono de la categoría y la convierte automáticamente a WebP optimizado."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'status': 'error', 'message': 'No se recibió ninguna imagen'}, status=400)

    try:
        webp_content = process_uploaded_image_to_webp(image_file, max_dimension=600, quality=85)
        path = default_storage.save(f"categories/webp/{webp_content.name}", webp_content)
        url = default_storage.url(path)
        return JsonResponse({
            'status': 'success',
            'image_url': url
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error al procesar la imagen: {str(e)}'}, status=500)


@csrf_exempt
def api_save_category(request):
    """Crea o edita una categoría personalizada con su imagen/ícono."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        from django.utils.text import slugify
        data = json.loads(request.body.decode('utf-8'))
        category_id = data.get('id')
        name = data.get('name', '').strip()
        image_url = data.get('image_url', '').strip()
        description = data.get('description', '').strip()

        if not name:
            return JsonResponse({'status': 'error', 'message': 'El nombre de la categoría es obligatorio.'}, status=400)

        slug = slugify(name) or f"cat-{Category.objects.count() + 1}"

        if category_id:
            cat_obj = get_object_or_404(Category, id=category_id)
            cat_obj.name = name
            cat_obj.image_url = image_url
            cat_obj.description = description
            cat_obj.save()
        else:
            existing = Category.objects.filter(Q(name__iexact=name) | Q(slug=slug)).first()
            if existing:
                existing.name = name
                existing.image_url = image_url
                if description:
                    existing.description = description
                existing.save()
                cat_obj = existing
            else:
                cat_obj = Category.objects.create(name=name, slug=slug, image_url=image_url, description=description)

        return JsonResponse({
            'status': 'success',
            'category': {
                'id': cat_obj.id,
                'name': cat_obj.name,
                'slug': cat_obj.slug,
                'image_url': cat_obj.get_image_url(),
                'description': cat_obj.description
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_delete_category(request, category_id):
    """Elimina una categoría si no tiene prendas asociadas."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        cat_obj = get_object_or_404(Category, id=category_id)
        if cat_obj.products.exists():
            return JsonResponse({
                'status': 'error',
                'message': f'No puedes eliminar "{cat_obj.name}" porque tiene {cat_obj.products.count()} prenda(s) asignada(s). Cambia esas prendas de categoría primero.'
            }, status=400)
        cat_obj.delete()
        return JsonResponse({'status': 'success', 'message': 'Categoría eliminada correctamente.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


@csrf_exempt
def api_upload_promo_image(request):
    """Sube una imagen para el banner publicitario principal y la convierte a WebP optimizado."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    image_file = request.FILES.get('image')
    if not image_file:
        return JsonResponse({'status': 'error', 'message': 'No se recibió ninguna imagen'}, status=400)

    try:
        webp_content = process_uploaded_image_to_webp(image_file, max_dimension=1400, quality=85)
        path = default_storage.save(f"banners/webp/{webp_content.name}", webp_content)
        url = default_storage.url(path)
        return JsonResponse({
            'status': 'success',
            'image_url': url
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': f'Error al procesar la imagen: {str(e)}'}, status=500)


@csrf_exempt
def api_update_promo_banner(request):
    """Actualiza la configuración del banner publicitario / descuento de la página principal."""
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body.decode('utf-8'))
        settings = StoreSetting.get_settings()

        settings.promo_banner_active = bool(data.get('promo_banner_active', True))
        settings.promo_badge = data.get('promo_badge', '').strip()
        settings.promo_title = data.get('promo_title', '').strip()
        settings.promo_price = data.get('promo_price', '').strip()
        settings.promo_price_note = data.get('promo_price_note', '').strip()
        settings.promo_wholesale_note = data.get('promo_wholesale_note', '').strip()
        settings.promo_button_text = data.get('promo_button_text', '').strip() or 'Comprar Ahora'
        settings.promo_button_link = data.get('promo_button_link', '').strip()
        settings.promo_image_url = data.get('promo_image_url', '').strip()

        product_id = data.get('promo_product_id')
        if product_id:
            settings.promo_product = Product.objects.filter(id=product_id).first()
        else:
            settings.promo_product = None

        settings.save()

        return JsonResponse({
            'status': 'success',
            'message': 'Banner publicitario actualizado correctamente',
            'banner': {
                'active': settings.promo_banner_active,
                'badge': settings.promo_badge,
                'title': settings.promo_title,
                'price': settings.promo_price,
                'price_note': settings.promo_price_note,
                'wholesale_note': settings.promo_wholesale_note,
                'button_text': settings.promo_button_text,
                'button_link': settings.promo_button_link,
                'image_url': settings.promo_image_url,
                'product_id': settings.promo_product.id if settings.promo_product else None
            }
        })
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)


