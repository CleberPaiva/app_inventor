from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_file, name='upload_file'),
    path('files/', views.AiaFileListView.as_view(), name='file_list'),
    path('files/<int:pk>/', views.file_detail, name='file_detail'),
    path('files/<int:pk>/analyze/', views.analyze_file, name='analyze_file'),
    path('files/<int:pk>/results/', views.analysis_results, name='analysis_results'),
    path('files/<int:pk>/print/', views.print_analysis, name='print_analysis'),
    path('images/<int:pk>/', views.image_detail, name='image_detail'),
    path('images/<int:image_id>/material-design/', views.material_design_analysis, name='material_design_analysis'),
    path('api/material-icons/search/', views.api_material_icons_search, name='api_material_icons_search'),
]
