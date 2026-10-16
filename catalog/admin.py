from django.contrib import admin
from .models import Category, Size, Color, Product, StoreSetting, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Size)
class SizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    ordering = ('order', 'name')


@admin.register(Color)
class ColorAdmin(admin.ModelAdmin):
    list_display = ('name', 'hex_code')
    search_fields = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'sku', 'price_retail', 'price_wholesale', 'wholesale_min_qty', 'stock', 'is_active')
    list_filter = ('category', 'is_active', 'is_featured')
    search_fields = ('name', 'sku', 'description')
    filter_horizontal = ('sizes', 'colors')


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'customer_name', 'customer_phone', 'order_type', 'status', 'total', 'created_at')
    list_filter = ('status', 'order_type', 'created_at')
    search_fields = ('order_number', 'customer_name', 'customer_phone')
    inlines = [OrderItemInline]


@admin.register(StoreSetting)
class StoreSettingAdmin(admin.ModelAdmin):
    list_display = ('store_name', 'owner_name', 'owner_phone', 'currency_symbol', 'global_wholesale_min_units')
