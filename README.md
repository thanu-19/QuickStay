# 🏨 QuickStay

**QuickStay** is a Django-based hotel booking web application that allows users to **browse rooms**, **book stays**, and **complete secure payments using Stripe Checkout** (test/sandbox mode).  

It’s a clean and minimal demo app that demonstrates real-world features like booking workflows, payment integration, image uploads, and media/static handling.

---

## 🎯 Summary / Purpose

- 🏠 Browse hotel rooms on the **landing page**.  
- 🧾 Click **“Book Now”** to open a booking form pre-filled with room details.  
- 💬 Submit the form to create a booking record in the database.  
- 💳 Click **“Pay Now”** to launch **Stripe Checkout** (test mode).  
- ✅ When payment succeeds, the booking is marked as **Paid** and displayed as `Paid ✅` in the UI.  
- ⚙️ Stripe webhooks (optional) can be used to automatically update booking statuses for reliability.

---

## 🧠 Tech Stack

| Component | Technology |
|------------|-------------|
| **Backend** | Django 5.2.x (Python 3.13) |
| **Database** | SQLite (Development) |
| **Payment Gateway** | Stripe Checkout API |
| **Frontend** | Django Templates (HTML, CSS, JS) |
| **Media Handling** | Django’s Static and Media configuration |
| **Webhooks** | Stripe CLI (optional, for local testing) |

---

## 🗂️ Project Structure


```
Quickstay/
├─ .env
├─ .gitignore
├─ README.md
├─ replacements.txt
├─ manage.py
├─ requirements.txt
├─ venv/                           # virtual environment (ignored)
├─ db.sqlite3                      # (ignored in .gitignore)
├─ static/
│  ├─ css/
│  │  └─ landing.css
│  └─ images/                       # optional public static images
├─ media/                           # uploaded media (ImageField files)
│  └─ room_images/
├─ templates/
│  ├─ base.html / mainbase.html
│  ├─ landingpage.html
│  ├─ book_room.html
│  ├─ bookings.html
│  └─ other templates...
├─ quickstay/                       # Django project
│  ├─ __init__.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ asgi.py
│  └─ wsgi.py
└─ accounts/                        # Django app
   ├─ __init__.py
   ├─ admin.py
   ├─ apps.py
   ├─ models.py
   ├─ views.py
   ├─ urls.py
   ├─ forms.py (optional)
   ├─ migrations/
   │  └─ ...
   └─ templates/accounts/ (optional app templates)
```
---
## 🏗️ Data Models (Entities)

### **HotelRoom**
| Field | Type | Description |
|--------|------|-------------|
| `name` | CharField | Name of the hotel room |
| `price` | DecimalField | Price per night |
| `image` | ImageField | Room photo (`upload_to='room_images/'`) |
| `is_available` | BooleanField | Indicates if the room is currently available |

### **Booking**
| Field | Type | Description |
|--------|------|-------------|
| `room_name` | CharField | Room booked |
| `email` | EmailField | Customer’s email |
| `persons` | IntegerField | Number of guests |
| `checkin`, `checkout` | DateFields | Booking dates |
| `price` | DecimalField | Total price |
| `image_name` | CharField (optional) | Associated room image |
| `paid` | BooleanField (default=False) | Payment status |
| `stripe_session_id` | CharField | Stripe session identifier |
| `paid_at` | DateTimeField | Payment timestamp |
| `created_at` | DateTimeField (auto_now_add=True) | When booking was created |

> 🧩 A simple custom user model is included (you can later switch to Django’s built-in `User` model).

---

## 🖼️ Important Templates

| Template File | Description |
|----------------|-------------|
| `templates/landingpage.html` | Displays all available hotel rooms with “Book Now” links |
| `templates/book_room.html` | Booking form with room details and image |
| `templates/bookings.html` | Displays user’s bookings and payment statuses |
| `templates/base.html` / `mainbase.html` | Base templates that include CSS and shared layout |

---

## 🌐 URL Routes (Expected in `accounts/urls.py`)

| URL Pattern | View Function | Purpose |
|--------------|----------------|----------|
| `/book/` | `book_room` | Handles room booking form |
| `/bookings/` | `user_bookings` | Lists user bookings |
| `/pay/<int:booking_id>/` | `pay_now` | Creates Stripe Checkout session |
| `/delete_booking/<int:booking_id>/` | `delete_booking` | Deletes an existing booking |
| `/payment-success/` | `payment_success` | Displays payment confirmation |
| `/stripe/webhook/` | `stripe_webhook` | Handles Stripe webhook events |

---

## 💳 Stripe Payment Flow (High-Level Overview)

1. **User clicks “Pay Now”** on the bookings page (`bookings.html`).
2. The request hits the `pay_now` view:
   - Verifies user ownership (ensures booking email matches logged-in user).
   - Computes price as `unit_amount = int(float(price) * 100)` (Stripe uses cents).
   - Builds success URL like:  
     `/payment-success/?session_id={CHECKOUT_SESSION_ID}&booking_id=<id>`
3. Stripe Checkout session is created and the user is redirected to Stripe.
4. Payment completes using **test card** `4242 4242 4242 4242`.
5. Stripe redirects to `success_url` — app verifies session:
   ```python
   stripe.checkout.Session.retrieve(session_id, expand=['payment_intent.charges.data'])
6. If payment_status == "paid", marks booking.paid = True.

7. (Recommended) Stripe webhook endpoint (checkout.session.completed) ensures reliable server-side payment confirmation.
