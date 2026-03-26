from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.home, name='home'),
    path('menu/', views.menu_page, name='menu_page'),
    path('checkout/', views.checkout, name='checkout'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('admin-panel/', views.admin_dashboard, name='admin_dashboard'),
    path('api/cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('api/cart/remove/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('api/cart/', views.get_cart, name='get_cart'),
    path('toggle-rider-mode/', views.toggle_rider_mode, name='toggle_rider_mode'),
    path('rider-dashboard/', views.rider_dashboard, name='rider_dashboard'),
]