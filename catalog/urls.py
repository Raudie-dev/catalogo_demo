from django.urls import path
from . import views

app_name = 'catalog'

urlpatterns = [
    # Vista pública del Catálogo (Solo para Clientes / Compradores)
    path('', views.catalog_index, name='index'),

    # Acceso privado del Administrador (/administrador/ y /admin/)
    path('administrador/login/', views.owner_login, name='owner_login'),
    path('administrador/logout/', views.owner_logout, name='owner_logout'),
    path('administrador/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/login/', views.owner_login, name='admin_login'),
    path('admin/logout/', views.owner_logout, name='admin_logout'),
    path('admin/', views.admin_dashboard, name='admin_panel'),

    # Páginas de Mi Cuenta, Login y Registro de Usuarios
    path('cuenta/', views.customer_account_view, name='customer_account'),
    path('login/', views.customer_login_view, name='customer_login'),
    path('registro/', views.customer_register_view, name='customer_register'),
    path('logout/', views.customer_logout_view, name='customer_logout'),

    # Endpoints de Cuentas de Usuario Registradas (Clientes)
    path('api/auth/register/', views.api_user_register, name='api_user_register'),
    path('api/auth/login/', views.api_user_login, name='api_user_login'),
    path('api/auth/logout/', views.api_user_logout, name='api_user_logout'),
    path('api/auth/profile/', views.api_user_update_profile, name='api_user_update_profile'),

    # Endpoints API de Catálogo, Pedidos y Reseñas
    path('api/orders/create/', views.api_create_order, name='api_create_order'),
    path('api/reviews/add/', views.api_add_review, name='api_add_review'),
    path('api/products/add/', views.api_add_product, name='api_add_product'),
    path('api/products/upload-images/', views.api_upload_product_images, name='api_upload_product_images'),
    path('api/products/edit/<int:product_id>/', views.api_edit_product, name='api_edit_product'),
    path('api/products/delete/<int:product_id>/', views.api_delete_product, name='api_delete_product'),
    path('api/orders/status/<int:order_id>/', views.api_update_order_status, name='api_update_order_status'),
    path('api/settings/update/', views.api_update_settings, name='api_update_settings'),
    path('api/reset-demo/', views.api_reset_demo, name='api_reset_demo'),

    # Endpoints para Gestión Personalizada de Tallas, Colores y Categorías
    path('api/sizes/save/', views.api_save_size, name='api_save_size'),
    path('api/sizes/delete/<int:size_id>/', views.api_delete_size, name='api_delete_size'),
    path('api/colors/save/', views.api_save_color, name='api_save_color'),
    path('api/colors/delete/<int:color_id>/', views.api_delete_color, name='api_delete_color'),
    path('api/categories/save/', views.api_save_category, name='api_save_category'),
    path('api/categories/upload-image/', views.api_upload_category_image, name='api_upload_category_image'),
    path('api/categories/delete/<int:category_id>/', views.api_delete_category, name='api_delete_category'),

    # Endpoints para Banner Publicitario / Promociones en Inicio
    path('api/promo-banner/update/', views.api_update_promo_banner, name='api_update_promo_banner'),
    path('api/promo-banner/upload-image/', views.api_upload_promo_image, name='api_upload_promo_image'),
]
