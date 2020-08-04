"""dec URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from websites.views import HomeView, ItemDetailView, ProductCreateView, ProductUpdateView, ProductDeleteView
from websites.views import add_to_cart, remove_from_cart, OrderSummaryView, remove_single_item_from_cart 
from websites.views import CheckoutView, Payment
admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', HomeView.as_view(), name="home" ),    
    path('add_to_cart/<int:pk>/', add_to_cart, name="add_to_cart"),
    path('remove_single_item_from_cart/<int:pk>/', remove_single_item_from_cart, name="remove_single_item_from_cart"),
    path('order-summary/', OrderSummaryView.as_view(), name="order-summary"),
    path('remove_from_cart/<int:pk>/', remove_from_cart, name="remove_from_cart"),
    path('product/create/', ProductCreateView.as_view(), name="create"),
    path('product/<int:pk>/', ItemDetailView.as_view(), name="product"),
    path('product/<int:pk>/update/', ProductUpdateView.as_view(), name="update"),
    path('product/<int:pk>/delete/', ProductDeleteView.as_view(), name="delete"),
    path('checkoutview/', CheckoutView.as_view(), name="checkout"),
    path('payment/<payment_option>/', Payment.as_view(), name="payment"),
    
]
