from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import UserMovieRating, UserMovieWatchlist
from .cache_utils import invalidate_user_cache


@receiver(post_save, sender=UserMovieRating)
def invalidate_user_cache_on_rating_save(sender, instance, **kwargs):
    """
    Invalidate user cache when a rating is created or updated
    """
    invalidate_user_cache(instance.user.id)


@receiver(post_delete, sender=UserMovieRating)
def invalidate_user_cache_on_rating_delete(sender, instance, **kwargs):
    """
    Invalidate user cache when a rating is deleted
    """
    invalidate_user_cache(instance.user.id)


@receiver(post_save, sender=UserMovieWatchlist)
def invalidate_user_cache_on_watchlist_save(sender, instance, **kwargs):
    """
    Invalidate user cache when a watchlist item is created or updated
    """
    invalidate_user_cache(instance.user.id)


@receiver(post_delete, sender=UserMovieWatchlist)
def invalidate_user_cache_on_watchlist_delete(sender, instance, **kwargs):
    """
    Invalidate user cache when a watchlist item is deleted
    """
    invalidate_user_cache(instance.user.id)