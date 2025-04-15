from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Score

class LeaderboardView(APIView):
    """
    API endpoint to get the leaderboard.
    """
    def get(self, request):
        leaderboard = Score.get_leaderboard()
        data = [{"name": score.name, "points": score.point} for score in leaderboard]
        return Response(data)

