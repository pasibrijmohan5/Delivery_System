from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api_views import ProductViewSet, CategoryViewSet, OrderViewSet, verify_khalti_payment

router = DefaultRouter()
router.register(r'dishes', ProductViewSet, basename='product')
router.register(r'categories', CategoryViewSet, basename='category')
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('payment/khalti/verify/', verify_khalti_payment, name='verify_khalti'),
]
