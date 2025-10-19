
import os
import stripe
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone
from accounts.models import Booking
from django.utils.http import urlencode
from django.contrib.auth.decorators import login_required
from .models import Booking
from .models import HotelRoom
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User
from datetime import datetime,date
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.files.storage import default_storage
from django.templatetags.static import static
from django.http import HttpResponseBadRequest
from django.views.decorators.http import require_POST

User = get_user_model()


stripe.api_key = settings.STRIPE_SECRET_KEY






stripe.api_key = settings.STRIPE_SECRET_KEY

session_id = "cs_test_a1voNNupVRtlTiDRm6SU5xeh78UNMtOovZw0qEn9c9p7e154LVZQi1m1IR"
s = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent.charges.data'])

print("session.id =", s.id)
print("session.payment_status =", getattr(s, 'payment_status', None))
pi = s.get('payment_intent')
print("payment_intent =", pi)

paid = False
if getattr(s, 'payment_status', '') == 'paid':
    paid = True
else:
    if pi:
        status = pi.get('status') if isinstance(pi, dict) else getattr(pi, 'status', None)
        if status == 'succeeded':
            paid = True

if paid:
    try:
        b = Booking.objects.get(stripe_session_id=session_id)
        b.paid = True
        b.paid_at = timezone.now()
        b.save(update_fields=['paid','paid_at'])
        print("Marked booking paid:", b.id)
    except Booking.DoesNotExist:
        print("No Booking found with stripe_session_id =", session_id)
else:
    print("Not paid according to Stripe. Check Stripe Dashboard for details.")



@login_required
def my_bookings(request):
    bookings = Booking.objects.filter(email=request.user.email).order_by('-id')
    return render(request, 'bookings.html', {'bookings': bookings})


@require_POST
@login_required
def pay_now(request, booking_id):
    """
    Create a Stripe Checkout Session and redirect to it.
    No intermediate page — the booking POST triggers the redirect to Stripe.
    """
    booking = get_object_or_404(Booking, id=booking_id)

    # ownership check (booking.email must match logged-in user's email)
    if booking.email.lower() != request.user.email.lower():
        messages.error(request, "You are not allowed to access this booking.")
        return redirect('bookings')

    try:
        unit_amount = int(float(booking.price) * 100)  # price -> paise
    except Exception:
        return HttpResponseBadRequest("Invalid booking price")

    try:
        success_url = request.build_absolute_uri(reverse('bookings') + '?paid=1')
        cancel_url = request.build_absolute_uri(reverse('bookings') + '?paid=0')

        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'inr',
                    'product_data': {'name': f'Booking: {booking.room_name}'},
                    'unit_amount': unit_amount,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url,
            cancel_url=cancel_url,
        )
        # redirect client to Stripe Checkout
        return redirect(session.url, code=303)
    except Exception as e:
        messages.error(request, "Payment initialization failed: " + str(e))
        return redirect('bookings')

def payment_success(request):
    session_id = request.GET.get('session_id')
    booking_id = request.GET.get('booking_id')
    if not session_id or not booking_id:
        messages.error(request, "Missing session or booking id.")
        return redirect('bookings')

    try:
        # expand payment_intent so status is available immediately
        session = stripe.checkout.Session.retrieve(session_id, expand=['payment_intent'])
    except Exception as e:
        messages.error(request, "Unable to verify payment session: " + str(e))
        return redirect('bookings')

    paid = False
    if getattr(session, 'payment_status', '') == 'paid':
        paid = True
    else:
        pi = getattr(session, 'payment_intent', None)
        status = pi.get('status') if isinstance(pi, dict) else getattr(pi, 'status', None)
        if status == 'succeeded':
            paid = True

    if paid:
        booking = get_object_or_404(Booking, id=booking_id)
        booking.paid = True
        booking.paid_at = timezone.now()
        booking.save(update_fields=['paid', 'paid_at'])
        messages.success(request, "Payment successful — booking updated.")
    else:
        messages.error(request, "Payment not completed yet. Check Stripe dashboard.")

    return redirect('bookings')

def payment_cancel(request):
    return render(request, "payment_cancel.html")

def user_bookings(request):
    """
    Shows bookings for the logged-in user's email. If not logged in, allow passing
    ?email=someone@example.com for testing. In production link bookings to User.
    """
    # prefer authenticated user's email
    user_email = None
    if request.user.is_authenticated:
        user_email = getattr(request.user, "email", "") or None

    # allow ?email= override for testing
    email_param = request.GET.get("email")
    if not user_email and email_param:
        user_email = email_param

    if user_email:
        bookings = Booking.objects.filter(email__iexact=user_email).order_by("-id")
    else:
        bookings = Booking.objects.none()

    # compute image_url for each booking
    for b in bookings:
        img_name = getattr(b, "image_name", None) or ""
        if img_name:
            b.image_url = static(f"images/{img_name}")
        else:
            base = b.room_name.lower().replace(" ", "_")
            b.image_url = static(f"images/{base}.jpg")  # fallback name
    # for debugging show which email was used
    return render(request, "bookings.html", {
        "bookings": bookings,
        "debug_email_used": user_email,
        "bookings_count": bookings.count(),
    })

@login_required
def delete_booking(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id)
    # ensure the booking belongs to the logged-in user
    if booking.email.lower() != request.user.email.lower():
        messages.error(request, "You are not allowed to delete this booking.")
        return redirect('bookings')

    if request.method == "POST":
        booking.delete()
        messages.success(request, "Booking deleted.")
    return redirect('bookings')

# def book_room(request):
#     room_name = request.GET.get('name', '')
#     price = request.GET.get('price', '')
#     image_name = request.GET.get('image', '')  # filename from landing page

#     if request.method == 'POST':
#         email = request.POST.get('email', '').strip()
#         checkin = request.POST.get('checkin')
#         checkout = request.POST.get('checkout')
#         persons = request.POST.get('persons', '1')

#         # basic validation
#         if not (email and checkin and checkout and int(persons) > 0):
#             messages.error(request, 'Please fill all required fields.')
#         elif checkout <= checkin:
#             messages.error(request, 'Check-out must be after check-in.')
#         else:
#             booking = Booking.objects.create(
#                 room_name=room_name,
#                 email=email,
#                 persons=int(persons),
#                 checkin=checkin,
#                 checkout=checkout,
#                 price=price or 0,
#                 image_name=image_name or ''
#             )
#             messages.success(request, f"🎉 Room booked successfully! Ref #{booking.id}")
#             return redirect('/landing')
#             # params = {'name': room_name, 'price': price, 'image': image_name}
#             # return redirect(reverse('book_room') + '?' + urlencode(params))

#     return render(request, 'book_room.html', {
#         'image': image_name,
#         'room_name': room_name,
#         'price': price
#     })

# def book_room(request):
#     room_name = request.GET.get('name', '')
#     price = request.GET.get('price', '')
#     image_url = ''

#     # 🏨 Fetch room details directly from database by name
#     room = None
#     if room_name:
#         room = get_object_or_404(HotelRoom, name=room_name)
#         price = room.price
#         if room.image:
    #         image_url = room.image.url  # /media/room_images/xxx.jpg

    # if request.method == 'POST':
    #     email = request.POST.get('email', '').strip()
    #     checkin = request.POST.get('checkin')
    #     checkout = request.POST.get('checkout')
    #     persons = request.POST.get('persons', '1')

    #     if not (email and checkin and checkout and int(persons) > 0):
    #         messages.error(request, 'Please fill all required fields.')
    #     elif checkout <= checkin:
    #         messages.error(request, 'Check-out must be after check-in.')
    #     else:
    #         booking = Booking.objects.create(
    #             room_name=room_name,
    #             email=email,
    #             persons=int(persons),
    #             checkin=checkin,
    #             checkout=checkout,
    #             price=price,
    #             image_name=room.image.name if room and room.image else ''
    #         )
    #         messages.success(request, f"🎉 Room booked successfully! Ref #{booking.id}")
    #         return redirect('/landing')

    # return render(request, 'book_room.html', {
    #     'room_name': room_name,
    #     'price': price,
    #     'image_url': image_url
    # })


def book_room(request):
    room_id = request.GET.get('room_id')
    room = None
    image_url = ''
    price = ''
    room_name = ''

    if room_id:
        room = get_object_or_404(HotelRoom, id=room_id)
        room_name = room.name
        price = room.price
        if room.image:
            image_url = room.image.url  # fetch from MEDIA

    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        checkin = request.POST.get('checkin')
        checkout = request.POST.get('checkout')
        persons = request.POST.get('persons', '1')

        if not (email and checkin and checkout and int(persons) > 0):
            messages.error(request, 'Please fill all required fields.')
        elif checkout <= checkin:
            messages.error(request, 'Check-out must be after check-in.')
        else:
            booking = Booking.objects.create(
                room_name=room_name,
                email=email,
                persons=int(persons),
                checkin=checkin,
                checkout=checkout,
                price=price,
                image_name=room.image.name if room and room.image else ''
            )
            messages.success(request, f"🎉 Room booked successfully! Ref #{booking.id}")
            return redirect('/landing')

    return render(request, 'book_room.html', {
        'room_name': room_name,
        'price': price,
        'image_url': image_url
    })


# def my_bookings(request):
#     bookings = Booking.objects.filter(email=request.user.email)  # or however you filter
#     for b in bookings:
#         if b.image_name:
#             b.image_url = f"{settings.MEDIA_URL}{b.image_name}"
#         else:
#             b.image_url = ''
#     context = {
#         'bookings': bookings,
#     }
#     return render(request, 'bookings.html', context)


# def user_bookings(request):
#     bookings = Booking.objects.filter(email=request.user.email)  # or filter as needed
#     # image_url is handled in the model property
#     context = {
#         'bookings': bookings
#     }
#     return render(request, 'bookings.html', context)

def user_bookings(request):
    bookings = Booking.objects.filter(email=request.user.email)
    return render(request, 'bookings.html', {'bookings': bookings})

def signup_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        number = request.POST.get("phone")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(request, "Passwords do not match")
            return redirect("signup")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered")
            return redirect("signup")

        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = name
        user.save()

        messages.success(request, "Account created successfully! Please login.")
        return redirect("login")

    return render(request, "signup.html")


# def login_view(request):
#     if request.method == "POST":
#         email = request.POST.get("email")
#         password = request.POST.get("password")

#         user = authenticate(request, username=email, password=password)
#         if user is not None:
#             login(request, user)
#             messages.success(request, "Login successful! 🎉")
#             return redirect("landing")  # <-- redirect to landing page
#         else:
#             messages.error(request, "Invalid email or password")

#     return render(request, "login.html")



from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, "Login successful! 🎉")

            # Redirect QuickStay admin to dashboard
            if email == "quickstay@gmail.com":
                return redirect("dashboard")
            else:
                return redirect("landing")
        else:
            messages.error(request, "Invalid email or password")

    return render(request, "login.html")



def dashboard_view(request):
    # Optional: check if user is logged in
    if not request.user.is_authenticated:
        return redirect('login')

    # For QuickStay admin only (optional)
    if request.user.email != "quickstay@gmail.com":
        return redirect('login')

    return render(request, "dashboard.html")


@login_required
def add_room_view(request):
    if request.method == "POST":
        name = request.POST.get("name")
        price = request.POST.get("price")
        image = request.FILES.get("image")

        # Create and save new room
        room = HotelRoom(name=name, price=price, image=image)
        room.save()

        messages.success(request, "Room added successfully! 🎉")
        return redirect("view_rooms")  # Redirect to view all rooms page

    return render(request, "add_room.html")

# View Rooms View
def view_rooms_view(request):
    if not request.user.is_authenticated:
        return redirect('login')

    rooms = HotelRoom.objects.all()
    return render(request, 'view_rooms.html', {'rooms': rooms})

def landing_view(request):
    rooms = HotelRoom.objects.all()  # fetch all rooms from DB
    return render(request, 'landingpage.html', {'rooms': rooms})
