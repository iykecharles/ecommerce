from django.db import models
from django.contrib.auth.models import User
from django.conf import settings
from django.utils import timezone
from django.db.models.signals import post_save
from django.urls import reverse
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


category_choices = (
    ("S", "Shirt"),
    ("SW", "SportsWear"),
    ("O", "Outwear"),
)

label_choices = (
    ("P", "Primary"),
    ("S", "Secondary"),
    ("D", "Danger"),
)

ADDRESS_CHOICES = (
    ("P", "Paypal"),
    ("S", "Stripe"),
    
)



class Item(models.Model):
    title = models.CharField(max_length=50)
    description = models.TextField(max_length=250)    
    label = models.CharField(choices=label_choices, max_length=2, blank=True, null=True)
    category = models.CharField(choices=category_choices, max_length=2, blank=True, null=True)
    price = models.FloatField()
    discount_price = models.FloatField(blank=True, null=True)
    #image = models.ImageField()
    slug = models.SlugField()  
    

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse("product", kwargs={'pk': self.pk})

    def get_add_to_cart_url(self):
        return reverse("add_to_cart", kwargs={'pk': self.pk}) 

    def get_remove_from_cart_url(self):
        return reverse("remove_from_cart", kwargs={'pk': self.pk})


class OrderItem(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    quantity = models.IntegerField(default=1)
    item = models.ForeignKey(Item, on_delete=models.CASCADE)

    def get_total(self):
        return self.quantity * self.item.price

    def get_discount_total(self):
        return self.quantity * self.item.discount_price

    


class Order(models.Model):
    items = models.ManyToManyField(OrderItem)
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    ordered = models.BooleanField(default=False)
    start_date = models.DateTimeField(auto_now_add=True)
    ordered_date = models.DateTimeField()
    billing_address = models.ForeignKey(
        "Address", related_name="billing_address", on_delete=models.SET_NULL, blank=True, null=True)
    shipping_address = models.ForeignKey(
        "Address", related_name="shipping_address", on_delete=models.SET_NULL, blank=True, null=True)
    payment = models.ForeignKey(
        "Payment", on_delete=models.SET_NULL, blank=True, null=True)




class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    one_click_purchasing = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


    def get_total1(self):
        total = 0
        for order_item in self.items.all():
            total += order_item.get_total()        
        return total

def userprofile_receiver(sender, instance, created, *args, **kwargs):
    if created:
        userprofile = UserProfile.objects.create(user=instance)


post_save.connect(userprofile_receiver, sender=settings.AUTH_USER_MODEL)

class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    street_address =  models.CharField(max_length=100)                        
    apartment_address = models.CharField(max_length=100)
    countries = CountryField(multiple=False)
    zip = models.CharField(max_length=100)
    address_type = models.CharField(max_length=1, choices=ADDRESS_CHOICES)
    default = models.BooleanField(default=False)
    

    def __str__(self):
        return self.user.username


class Payment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE)
    stripe_charge_id = models.CharField(max_length=50)
    amount = models.FloatField()
    timestamp = models.DateTimeField(auto_now_add=True)






