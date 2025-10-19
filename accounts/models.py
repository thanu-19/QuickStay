from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    number = models.CharField(max_length=15)
    password = models.CharField(max_length=100)

    def __str__(self):
        return self.email


class Booking(models.Model):
    room_name = models.CharField(max_length=200)
    email = models.EmailField()
    persons = models.PositiveSmallIntegerField()
    checkin = models.DateField()
    checkout = models.DateField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image_name = models.CharField(max_length=255, blank=True, null=True)  # ✅ just to store image filename
    created_at = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)
    stripe_session_id = models.CharField(max_length=255, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    @property
    def image_url(self):
        if self.image_name:
            return f"/media/{self.image_name}"  # Django serves uploaded media at /media/
        return ''  # fallback
    def __str__(self):
        return f"{self.room_name} — {self.email} ({self.checkin} → {self.checkout})"


class HotelRoom(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='room_images/')
    is_available = models.BooleanField(default=True)

    def __str__(self):
        return self.name
