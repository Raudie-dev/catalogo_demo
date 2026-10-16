# 🛍️ Catálogo de Ropa en Django (Venta al Mayor y Detal con WhatsApp)

Aplicación web desarrollada en **Django 5 (Python)** con base de datos SQLite, Tailwind CSS y JavaScript para la gestión de catálogos de ropa con precios diferenciales (Detal vs Mayor), selección de variantes (tallas y colores) y checkout directo por WhatsApp.

---

## 🚀 Características Principales

### 1. 👥 Niveles de Usuario
* **🛒 Nivel Cliente / Comprador (`/`):**
  * Catálogo interactivo de prendas de ropa con filtros por categoría, tallas, colores, precio y ofertas al mayor.
  * Vista rápida de producto para elegir talla, color y cantidad con cálculo de ahorro al mayor en tiempo real.
  * **Carrito de Compras con Gamificación Mayorista**: Barra de progreso que indica cuántas prendas faltan para activar el precio al mayor en todo el carrito (soporta combinar diferentes modelos).
  * **Crear Pedido y Checkout**: Guarda el pedido en la base de datos de Django (`Order` y `OrderItem`) y genera automáticamente el mensaje con emojis y desglose completo para **abrir el chat de WhatsApp directo con el dueño**.
  * Botón flotante para consultar con el dueño por WhatsApp en cualquier momento.

* **👑 Nivel Dueño / Administrador (`/dueno/` y `/admin/`):**
  * **Inventario de Prendas**:
    * Botón `+ Nueva Prenda de Ropa` con selector de fotos, tallas disponibles (checkboxes) y paleta de colores.
    * Definición de **Precio Detal** y **Precio al Mayor**.
    * Configuración de **Unidades Mínimas** requeridas para el precio de mayoreo.
    * Edición y eliminación de prendas.
  * **Gestión de Pedidos Recibidos**:
    * Listado de todas las órdenes generadas por los clientes con su número `#PED-XXXX`.
    * Desglose de cliente, dirección, método de pago y prendas solicitadas.
    * Selector para actualizar estado (*Pendiente*, *Confirmado*, *Enviado*, *Cancelado*).
    * Botón directo para **responder al cliente por WhatsApp** con un solo clic.
  * **Ajustes del Negocio**:
    * Configurar número de WhatsApp oficial del dueño.
    * Nombre de tienda, símbolo de moneda y reglas de mayoreo combinado.
    * Botón para restablecer el catálogo a los datos demo de fábrica.

---

## 📂 Estructura del Proyecto en Django

```text
catalogo_demo/
├── manage.py                    # Gestor de comandos de Django
├── iniciar_demo.bat             # Script para iniciar el servidor y abrir el navegador en Windows
├── db.sqlite3                   # Base de datos SQLite
├── config/
│   ├── settings.py              # Configuración de Django (apps, plantillas, static, localización)
│   ├── urls.py                  # Enrutador principal
│   └── wsgi.py                  # WSGI para despliegue
├── catalog/
│   ├── models.py                # Modelos: Category, Size, Color, Product, StoreSetting, Order, OrderItem
│   ├── views.py                 # Vistas HTML y endpoints API JSON
│   ├── urls.py                  # Rutas del catálogo y panel
│   ├── admin.py                 # Registro en el panel Django Admin estándar
│   ├── context_processors.py    # Inyección de ajustes globales y pedidos pendientes
│   └── management/commands/
│       └── populate_demo.py     # Comando para sembrar prendas, tallas, colores y pedidos demo
├── templates/
│   ├── base.html                # Plantilla base con Tailwind CDN, drawer del carrito y modales
│   └── catalog/
│       ├── index.html           # Vista del catálogo para clientes con filtros y modal de producto
│       └── admin_panel.html     # Panel del dueño con inventario, pedidos y ajustes
└── static/
    └── js/
        └── cart.js              # Motor del carrito, cálculo mayorista y despacho a WhatsApp
```

---

## ⚡ Cómo Ejecutar la Aplicación

### Opción 1 (Doble Clic):
Haz doble clic sobre `iniciar_demo.bat` en la carpeta del proyecto.

### Opción 2 (Vía Terminal):
```bash
python manage.py runserver
```

Abre en tu navegador:
* **Catálogo Cliente:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
* **Panel del Dueño:** [http://127.0.0.1:8000/dueno/](http://127.0.0.1:8000/dueno/)
* **Django Admin Estándar:** [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
  * Usuario: `admin`
  * Contraseña: `admin123`
