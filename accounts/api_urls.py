from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import CustomTokenObtainPairView, RegisterView, ProfileView

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
]
