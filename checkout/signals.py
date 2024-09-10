from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from profiles.models import UserProfile
from .models import OrderLineItem
from django.db.utils import IntegrityError

# Signal to create or update a user profile when a new user is created
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """
    Create a user profile if one doesn't exist and skip for superusers.
    """
    if instance.is_superuser:  # Skip superuser profile creation
        return

    if created:
        try:
            UserProfile.objects.create(user=instance)
        except IntegrityError:
            pass  # Handle IntegrityError when profile already exists

# Signal to save the user profile when user data is updated
@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """
    Save the user profile, if it exists.
    """
    if hasattr(instance, 'userprofile'):
        instance.userprofile.save()

# Signal to update the order total when an order line item is created or updated
@receiver(post_save, sender=OrderLineItem)
def update_on_save(sender, instance, created, **kwargs):
    """
    Update the order total when a line item is created or updated.
    """
    instance.order.update_total()

# Signal to update the order total when an order line item is deleted
@receiver(post_delete, sender=OrderLineItem)
def update_on_delete(sender, instance, **kwargs):
    """
    Update the order total when a line item is deleted.
    """
    instance.order.update_total()