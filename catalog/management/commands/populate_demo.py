from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from catalog.models import Category, Size, Color, Product, StoreSetting, Order, OrderItem, Review, CustomerProfile
from decimal import Decimal


class Command(BaseCommand):
    help = 'Puebla la base de datos en español con el catálogo SHIBUI, cuentas de usuarios registradas, reseñas y pedidos'

    def handle(self, *args, **kwargs):
        self.stdout.write("Iniciando carga de catálogo SHIBUI en español...")

        # 1. Configuración de Tienda (SHIBUI)
        settings, _ = StoreSetting.objects.get_or_create(id=1)
        settings.store_name = "SHIBUI"
        settings.store_subtitle = "Catálogo Oficial · Ventas al Detal y al Mayor"
        settings.store_location = "Caracas · Envíos Nacionales"
        settings.owner_name = "Equipo SHIBUI"
        settings.owner_phone = "+584128945112"
        settings.currency_symbol = "$"
        settings.currency_code = "USD"
        settings.bcv_rate = Decimal("45.80")
        settings.announcement = "🐾 Precios de MAYOREO automáticos a partir de 6 piezas surtidas o por mínimo del modelo · Envíos MRW y Zoom"
        settings.combine_wholesale_enabled = True
        settings.global_wholesale_min_units = 6
        settings.save()

        # Limpiar categorías y productos anteriores para una demo impecable
        Product.objects.all().delete()
        Category.objects.all().delete()

        # 2. Categorías 100% en Español
        categories_data = [
            ("Conjuntos", "Conjuntos de dos piezas coordinados en lino, tejido acanalado y algodón."),
            ("Blusas", "Blusas asimétricas, tops de doble tela y básicos en tendencia."),
            ("Vestidos", "Vestidos cortos, midi y largos de corte de tienda."),
            ("Bodys", "Bodys moldeadores de doble tela y ajuste perfecto."),
            ("Corsets", "Corsets estructurados con varillas suaves de diseño."),
            ("Faldas", "Faldas plisadas, midi satinadas y minifaldas casuales."),
            ("Pantalones", "Pantalones palazzo, de corte sastre y tiro alto."),
            ("Camisas", "Camisas holgadas en popelina de algodón y lino fresco."),
        ]
        cat_map = {}
        for name, desc in categories_data:
            c, _ = Category.objects.get_or_create(name=name, defaults={'description': desc})
            cat_map[name] = c

        # 3. Tallas
        sizes_data = [
            ("XS", 1), ("S", 2), ("M", 3), ("L", 4), ("XL", 5), ("Única", 6)
        ]
        size_map = {}
        for name, order in sizes_data:
            s, _ = Size.objects.get_or_create(name=name, defaults={'order': order})
            size_map[name] = s

        # 4. Colores en Español
        colors_data = [
            ("Vino Tinto", "#390007"),
            ("Negro", "#141414"),
            ("Blanco", "#ffffff"),
            ("Café Moca", "#6f4e37"),
            ("Beige Arena", "#d6c6b2"),
            ("Visón", "#8b796e"),
            ("Verde Oliva", "#4b5320"),
            ("Rosa Viejo", "#d8a39d"),
            ("Azul Cielo", "#a2c4e0"),
            ("Gris Jaspeado", "#9ca3af"),
            ("Rojo Cereza", "#990f1b"),
            ("Amarillo Mantequilla", "#f9ebb2"),
        ]
        color_map = {}
        for name, hex_code in colors_data:
            col, _ = Color.objects.update_or_create(name=name, defaults={'hex_code': hex_code})
            color_map[name] = col

        # 5. Prendas y Conjuntos de Ropa (100% en Español con Detal y Mayor)
        products_data = [
            {
                "name": "Conjunto Antonella de Lino 2 Piezas",
                "category": "Conjuntos",
                "sku": "CON-101",
                "description": "Conjunto de chaleco sastre abotonado y pantalón corto de tiro alto en lino fresco prelavado. No transparenta, horma estilizada ideal para ocasiones casuales o elegantes.",
                "price_retail": Decimal("28.00"),
                "price_wholesale": Decimal("19.50"),
                "wholesale_min_qty": 4,
                "stock": 45,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1515886657613-9f3515b0c78f?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Beige Arena", "Blanco", "Vino Tinto", "Negro", "Café Moca"]
            },
            {
                "name": "Vestido Midi Satinado Isabella",
                "category": "Vestidos",
                "sku": "VES-102",
                "description": "Vestido midi de caída fluida con escote drapeado y tirantes ajustables. Confeccionado en satén pesado de tacto sedoso.",
                "price_retail": Decimal("32.00"),
                "price_wholesale": Decimal("22.00"),
                "wholesale_min_qty": 3,
                "stock": 30,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1595777457583-95e059d581b8?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Vino Tinto", "Rojo Cereza", "Negro", "Beige Arena"]
            },
            {
                "name": "Blusa Asimétrica Doble Tela Acanalada",
                "category": "Blusas",
                "sku": "BLU-103",
                "description": "Blusa de corte asimétrico confeccionada en tejido acanalado suave con doble forro delantero para soporte total y ajuste cómodo.",
                "price_retail": Decimal("14.00"),
                "price_wholesale": Decimal("9.00"),
                "wholesale_min_qty": 6,
                "stock": 95,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1503342217505-b0a15ec3261c?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Blanco", "Negro", "Vino Tinto", "Café Moca", "Verde Oliva"]
            },
            {
                "name": "Body Moldeador Cuello Cuadrado",
                "category": "Bodys",
                "sku": "BOD-104",
                "description": "Body moldeador en tela suplex suave de alta elongación. Escote cuadrado favorecedor y broche inferior hipoalergénico de 2 niveles.",
                "price_retail": Decimal("18.00"),
                "price_wholesale": Decimal("12.00"),
                "wholesale_min_qty": 6,
                "stock": 80,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1539109136881-3be0616acf4b?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Negro", "Café Moca", "Blanco", "Visón"]
            },
            {
                "name": "Corset Estructurado Camila",
                "category": "Corsets",
                "sku": "COR-105",
                "description": "Corset con varillas flexibles que definen la cintura cómodamente. Cierre posterior con ajuste regulable.",
                "price_retail": Decimal("22.00"),
                "price_wholesale": Decimal("15.00"),
                "wholesale_min_qty": 4,
                "stock": 40,
                "is_featured": True,
                "is_immediate": False,
                "image_url": "https://images.unsplash.com/photo-1529139574466-a303027c1d8b?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Vino Tinto", "Negro", "Blanco"]
            },
            {
                "name": "Pantalón Palazzo Sastre Tiro Alto",
                "category": "Pantalones",
                "sku": "PAN-106",
                "description": "Pantalón de bota ancha con pinzas delanteras y caída impecable. Pretina alta que estiliza la silueta y bolsillos laterales.",
                "price_retail": Decimal("26.00"),
                "price_wholesale": Decimal("18.00"),
                "wholesale_min_qty": 4,
                "stock": 55,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L", "XL"],
                "colors": ["Beige Arena", "Negro", "Blanco", "Visón"]
            },
            {
                "name": "Falda Short Plisada Clásica",
                "category": "Faldas",
                "sku": "FAL-107",
                "description": "Falda tableada con short interno incluido para total comodidad. Cierre lateral invisible y tela de alta firmeza.",
                "price_retail": Decimal("20.00"),
                "price_wholesale": Decimal("13.50"),
                "wholesale_min_qty": 5,
                "stock": 50,
                "is_featured": False,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1582142306909-195724d33ffc?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Blanco", "Negro", "Gris Jaspeado", "Beige Arena"]
            },
            {
                "name": "Camisa Holgada Popelina Capri",
                "category": "Camisas",
                "sku": "CAM-108",
                "description": "Camisa de corte relajado en popelina 100% algodón. Ideal para usar abierta sobre blusas o anudada a la cintura.",
                "price_retail": Decimal("24.00"),
                "price_wholesale": Decimal("16.50"),
                "wholesale_min_qty": 4,
                "stock": 60,
                "is_featured": False,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1598554747436-c9293d6a588f?w=800&auto=format&fit=crop&q=80",
                "sizes": ["S", "M", "L", "Única"],
                "colors": ["Azul Cielo", "Blanco", "Rosa Viejo"]
            },
            {
                "name": "Vestido Corto Manga Larga Valentina",
                "category": "Vestidos",
                "sku": "VES-109",
                "description": "Vestido corto ajustado en tela doble licrada con abertura lateral sutil en cintura y manga larga.",
                "price_retail": Decimal("25.00"),
                "price_wholesale": Decimal("17.00"),
                "wholesale_min_qty": 4,
                "stock": 35,
                "is_featured": False,
                "is_immediate": False,
                "image_url": "https://images.unsplash.com/photo-1572804013309-59a88b7e92f1?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Negro", "Vino Tinto", "Café Moca", "Verde Oliva"]
            },
            {
                "name": "Conjunto Tejido Cárdigan y Blusa",
                "category": "Conjuntos",
                "sku": "CON-110",
                "description": "Dúo tejido de hilo suave compuesto por blusa corta de tiras y cárdigan abotonado a tono.",
                "price_retail": Decimal("29.00"),
                "price_wholesale": Decimal("20.00"),
                "wholesale_min_qty": 3,
                "stock": 40,
                "is_featured": True,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1434389677669-e08b4cac3105?w=800&auto=format&fit=crop&q=80",
                "sizes": ["S", "M", "L"],
                "colors": ["Amarillo Mantequilla", "Rosa Viejo", "Beige Arena", "Blanco"]
            },
            {
                "name": "Blusa Cuello Halter Espalda Descubierta",
                "category": "Blusas",
                "sku": "BLU-111",
                "description": "Blusa cuello halter con amarre graduable y espalda baja. Confeccionada en tela fría doble sin costuras visibles.",
                "price_retail": Decimal("15.00"),
                "price_wholesale": Decimal("9.50"),
                "wholesale_min_qty": 6,
                "stock": 110,
                "is_featured": False,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1485230895905-ec40ba36b9bc?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Rojo Cereza", "Vino Tinto", "Negro", "Blanco", "Café Moca"]
            },
            {
                "name": "Body Manga Larga Escote en V",
                "category": "Bodys",
                "sku": "BOD-112",
                "description": "Body clásico de manga larga con escote en V pronunciado y ajuste estilizado al cuerpo.",
                "price_retail": Decimal("19.00"),
                "price_wholesale": Decimal("13.00"),
                "wholesale_min_qty": 5,
                "stock": 70,
                "is_featured": False,
                "is_immediate": True,
                "image_url": "https://images.unsplash.com/photo-1509631179647-0177331693ae?w=800&auto=format&fit=crop&q=80",
                "sizes": ["XS", "S", "M", "L"],
                "colors": ["Negro", "Vino Tinto", "Blanco"]
            }
        ]

        for p_data in products_data:
            cat = cat_map[p_data["category"]]
            prod, _ = Product.objects.update_or_create(
                sku=p_data["sku"],
                defaults={
                    "name": p_data["name"],
                    "category": cat,
                    "description": p_data["description"],
                    "price_retail": p_data["price_retail"],
                    "price_wholesale": p_data["price_wholesale"],
                    "wholesale_min_qty": p_data["wholesale_min_qty"],
                    "stock": p_data["stock"],
                    "is_featured": p_data["is_featured"],
                    "is_immediate": p_data["is_immediate"],
                    "image_url": p_data["image_url"],
                    "is_active": True
                }
            )
            p_sizes = [size_map[s] for s in p_data["sizes"] if s in size_map]
            p_colors = [color_map[c] for c in p_data["colors"] if c in color_map]
            prod.sizes.set(p_sizes)
            prod.colors.set(p_colors)

        # 6. Pedidos Iniciales de Ejemplo
        Order.objects.all().delete()
        order1 = Order.objects.create(
            order_number="SH-1042",
            customer_name="Mariana Rojas",
            customer_phone="+58 412 9876543",
            customer_city="Caracas, Distrito Capital",
            customer_address="Agencia MRW Altamira",
            payment_method="Pago Móvil / Divisas",
            notes="Cédula/ID: V-26845120 | Entrega: Envío Nacional (MRW / Zoom)",
            order_type="wholesale",
            status="Confirmado",
            total_units=8,
            subtotal_retail=Decimal("168.00"),
            wholesale_savings=Decimal("54.00"),
            total=Decimal("114.00")
        )
        p1 = Product.objects.filter(sku="CON-101").first()
        if p1:
            OrderItem.objects.create(
                order=order1,
                product=p1,
                product_name=p1.name,
                size_name="S",
                color_name="Beige Arena",
                color_hex="#d6c6b2",
                quantity=4,
                price_retail=Decimal("28.00"),
                price_applied=Decimal("19.50"),
                is_wholesale_applied=True,
                subtotal=Decimal("78.00")
            )
        p3 = Product.objects.filter(sku="BLU-103").first()
        if p3:
            OrderItem.objects.create(
                order=order1,
                product=p3,
                product_name=p3.name,
                size_name="M",
                color_name="Vino Tinto",
                color_hex="#390007",
                quantity=4,
                price_retail=Decimal("14.00"),
                price_applied=Decimal("9.00"),
                is_wholesale_applied=True,
                subtotal=Decimal("36.00")
            )

        order2 = Order.objects.create(
            order_number="SH-1043",
            customer_name="Gabriela Mendoza",
            customer_phone="+58 414 3321980",
            customer_city="Aragua, Maracay",
            customer_address="Retiro en Tienda Las Delicias",
            payment_method="Zinli / Efectivo",
            notes="Cédula/ID: V-28110443 | Entrega: Retiro Personal",
            order_type="retail",
            status="Pendiente",
            total_units=1,
            subtotal_retail=Decimal("32.00"),
            wholesale_savings=Decimal("0.00"),
            total=Decimal("32.00")
        )
        p2 = Product.objects.filter(sku="VES-102").first()
        if p2:
            OrderItem.objects.create(
                order=order2,
                product=p2,
                product_name=p2.name,
                size_name="S",
                color_name="Vino Tinto",
                color_hex="#390007",
                quantity=1,
                price_retail=Decimal("32.00"),
                price_applied=Decimal("32.00"),
                is_wholesale_applied=False,
                subtotal=Decimal("32.00")
            )

        # 7. Cuentas de Usuarios Registradas + Reseñas Verificadas
        Review.objects.all().delete()
        registered_customers = [
            ("camila", "Camila Rodríguez", "camila@correo.com", "0412-5551020", "Caracas", "S"),
            ("valentina", "Valentina Pérez", "valentina@correo.com", "0414-8823110", "Valencia", "M"),
            ("andrea", "Andrea Morales", "andrea@correo.com", "0424-9104432", "Maracay", "S"),
            ("sofia", "Sofía Castillo", "sofia@correo.com", "0412-3349012", "Barquisimeto", "XS"),
            ("daniela", "Daniela Rivas", "daniela@correo.com", "0416-7712098", "Lechería", "M"),
            ("mariana", "Mariana Rojas", "mariana@correo.com", "0412-9876543", "Caracas", "M"),
        ]
        user_map = {}
        for uname, full_name, email, phone, city, pref_size in registered_customers:
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    "first_name": full_name,
                    "email": email,
                }
            )
            u.first_name = full_name
            u.email = email
            u.set_password("1234")
            u.save()
            CustomerProfile.objects.update_or_create(
                user=u,
                defaults={
                    "phone": phone,
                    "city": city,
                    "preferred_size": pref_size
                }
            )
            user_map[uname] = u

        sample_reviews = [
            ("CON-101", "camila", 5, "S", "Fiel a la talla", "El lino de este conjunto es espectacular, no transparenta nada y la horma del chaleco queda perfecta."),
            ("CON-101", "valentina", 5, "M", "Fiel a la talla", "Compré 6 conjuntos surtidos al mayor para mi tienda y se vendieron rapidísimo. La calidad de costura de SHIBUI es 10/10."),
            ("VES-102", "andrea", 5, "S", "Horma perfecta", "El satén tiene una caída pesada súper elegante. Lo usé para un evento de noche y recibí demasiados cumplidos."),
            ("BLU-103", "sofia", 5, "XS", "Fiel a la talla", "Doble tela real, sostiene súper bien y el corte asimétrico estiliza muchísimo."),
            ("BOD-104", "daniela", 4, "M", "Ajustado moldeador", "Moldea increíble la cintura, la tela suplex es gruesa y muy cómoda para usar todo el día."),
            ("CON-110", "mariana", 5, "M", "Fiel a la talla", "El tejido es súper suave y fresco, el color amarillo mantequilla en persona es aún más lindo."),
        ]
        for sku_code, uname, stars, sz, fit, text in sample_reviews:
            prod_obj = Product.objects.filter(sku=sku_code).first()
            u_obj = user_map.get(uname)
            if prod_obj and u_obj:
                Review.objects.create(
                    product=prod_obj,
                    user=u_obj,
                    author_name=u_obj.first_name,
                    rating=stars,
                    size_purchased=sz,
                    fit_feedback=fit,
                    comment=text
                )

        self.stdout.write(self.style.SUCCESS("¡Catálogo SHIBUI en español y cuentas registradas pobladas exitosamente!"))
