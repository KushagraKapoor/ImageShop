from django.urls import path
from . import views

urlpatterns = [
    path('upload/', views.upload_image, name='upload_image'),
    path('results/<str:results_file>/', views.results, name='results'),
    path('product_summary/', views.product_summary, name='product_summary'),
]
