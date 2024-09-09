from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from profiles.models import UserProfile  # предполагается, что модель профиля находится в profiles/models.py
from .models import OrderLineItem

# Signal to create a user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

# Signal to save the user profile when user data is updated
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()

# Signal to update the order total when an order line item is created or updated
@receiver(post_save, sender=OrderLineItem)
def update_on_save(sender, instance, created, **kwargs):
    """
    Update the order total when a line item is created or updated
    """
    instance.order.update_total()

# Signal to update the order total when an order line item is deleted
@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance, **kwargs):
    """
    Update the order total when a line item is deleted
    """
    instance.order.update_total()