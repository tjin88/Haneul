from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Profile
import uuid
import logging

logger = logging.getLogger(__name__)

def generate_profile_id():
    """Generate a 24-character ID similar to MongoDB ObjectID"""
    return uuid.uuid4().hex[:24]

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if created:
        try:
            Profile.objects.create(
                id=generate_profile_id(),
                user=instance,
                reading_list=[],
                dark_mode=False,
                profile_image='',
                email_notifications=False,
                is_paying_user=False
            )
            logger.info(f"Created new profile for user {instance.username}")
        except Exception as e:
            logger.error(f"Error creating profile for user {instance.username}: {str(e)}")
            raise
    else:
        try:
            instance.profile.save()
            logger.info(f"Updated profile for user {instance.username}")
        except Exception as e:
            logger.error(f"Error updating profile for user {instance.username}: {str(e)}")
            raise

@receiver(post_delete, sender=User)
def delete_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        try:
            instance.profile.delete()
            logger.info(f"Deleted profile for user {instance.username}")
        except Exception as e:
            logger.error(f"Error deleting profile for user {instance.username}: {str(e)}")
            raise