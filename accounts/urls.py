from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include

from django.contrib.auth import views as auth_views

urlpatterns = [
    path("signup/", views.signup_view, name="signup"),
    path("login/", views.login_view, name="login"),
    path("landing/", views.landing_view, name="landing"),
    path('book/', views.book_room, name='book_room'),
    path('bookings/', views.user_bookings, name='bookings'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete_booking/<int:booking_id>/', views.delete_booking, name='delete_booking'),
    path('pay/<int:booking_id>/', views.pay_now, name='pay_now'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-cancel/', views.payment_cancel, name='payment_cancel'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('add-room/', views.add_room_view, name='add_room'),
    path('view-rooms/', views.view_rooms_view, name='view_rooms'),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
