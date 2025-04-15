from django.db import models
from django.utils.translation import gettext as _

class Score(models.Model):
    discord_id = models.CharField(_("Discord ID"), max_length=255, unique=True, default="Unknown")  # Store Discord user ID
    name = models.CharField(_("name"), max_length=255)  # Optional: Store Discord username
    point = models.IntegerField(_("points"))

    def __str__(self):
        return f"{self.name}: {self.point}"

    @staticmethod
    def get_leaderboard(limit=10):
        """
        Returns the top users ordered by points in descending order.
        """
        return Score.objects.order_by('-point')[:limit]