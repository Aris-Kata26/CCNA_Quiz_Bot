from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Question
from .serializers import QuestionSerializer  # Import the updated serializer

@api_view(['GET'])
def get_ccna_question(request):
    level = request.GET.get('level')

    if not level:
        return Response({"error": "Missing CCNA level"}, status=400)
    
    try:
        level = int(level)
    except ValueError:
        return Response({"error": "Invalid level format"}, status=400)

    question = Question.objects.filter(
        ccna_level=level,
        is_active=True
    ).order_by('?').first()

    if not question:
        return Response({"error": "No questions found for this level"}, status=404)

    serializer = QuestionSerializer(question, context={'request': request})
    return Response([serializer.data])  # Return as a list
