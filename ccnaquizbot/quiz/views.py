from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Question, Answer
from .serializers import QuestionSerializer
from django.db.models import Prefetch

@api_view(['GET'])
def get_ccna_question(request):
    level = request.GET.get('level')

    # Check if 'level' parameter is missing
    if not level:
        return Response({"error": "Missing CCNA level"}, status=400)

    try:
        # Try to convert the level to an integer
        level = int(level)
    except ValueError:
        # If conversion fails, return an error response
        return Response({"error": "Invalid level format"}, status=400)

    # Fetch the question with related answers
    question = Question.objects.filter(
        ccna_level=level,
        is_active=True
    ).prefetch_related(
        Prefetch('answers', queryset=Answer.objects.filter(is_active=True))
    ).order_by('?').first()

    # If no question is found, return a 404 error
    if not question:
        return Response({"error": "No questions found for this level"}, status=404)

    # Serialize the question data along with answers
    serializer = QuestionSerializer(question, context={'request': request})

    # Return the serialized data as a response
    return Response(serializer.data)