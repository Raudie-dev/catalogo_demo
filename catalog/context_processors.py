from .models import StoreSetting, Order


def store_context(request):
    settings = StoreSetting.get_settings()
    pending_count = Order.objects.filter(status='Pendiente').count()
    return {
        'store_settings': settings,
        'pending_orders_count': pending_count,
    }
