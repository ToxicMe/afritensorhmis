"""
URL configuration for AFRITENSORHMIS project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
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
from accounts import views as accounts_views  # import your login view directly


urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')),
    path('hospital/', include('hospital.urls')),
    path('companies/', include('companies.urls')),
    path('registration/', include('registration.urls')),
    path('triage/', include('triage.urls')),
    path('doctor/', include('doctor.urls')),
    path('laboratory/', include('laboratory.urls')),
    path('pharmacy/', include('pharmacy.urls')),
    path('billing/', include('billing.urls')),
    path('finance/', include('finance.urls')),
    path('', accounts_views.login_view, name='index'),  # Root URL shows login

    




]
