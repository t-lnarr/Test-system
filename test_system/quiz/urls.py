from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('student/login/', views.student_login, name='student_login'),
    path('student/search/', views.search_test, name='search_test'),
    path('student/solve/<str:test_code>/', views.solve_test, name='solve_test'),
    path('teacher/login/', views.teacher_login, name='teacher_login'),
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/create/', views.create_test, name='create_test'),
    path('teacher/test/<str:test_code>/', views.test_detail, name='test_detail'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
# 'search_test' yolunu kaldırıp bunu ekle
]
