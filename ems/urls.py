from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # Auth
    #path('accounts/login/', auth_views.LoginView.as_view(template_name='ems/login.html'), name='login'),
    #path('accounts/logout/', auth_views.LogoutView.as_view(next_page='ems/login.html'), name='logout'),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    # Home
    path('', views.home, name='home'),
    # Categories
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.create_category, name='create_category'),
    path('categories/<int:category_id>/', views.category_events, name='category_events'),
    path('categories/delete/<int:category_id>/', views.delete_category, name='delete_category'),
    # Events
    path('events/create/', views.create_event, name='create_event'),
    path('events/update/<int:event_id>/', views.update_event, name='update_event'),
    path('events/delete/<int:event_id>/', views.delete_event, name='delete_event'),
    # Event timeline & chart
    path('timeline/', views.event_timeline, name='event_timeline'),
    path('event-chart/', views.event_chart, name='event_chart'),
    # Outcomes
    path('events/<int:event_id>/outcomes/', views.outcome_list, name='outcome_list'),  # Create new outcomes & list
    path('outcomes/<int:outcome_id>/', views.outcome_detail, name='outcome_detail'),   # Get single outcome
    path('outcomes/<int:outcome_id>/update/', views.outcome_update, name='outcome_update'),  # Update existing outcome
]
