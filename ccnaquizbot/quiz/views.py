from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Question, Answer
from .serializers import QuestionSerializer
from django.db.models import Prefetch

@api_view(['GET'])
def get_ccna_question(request):
    level = request.GET.get('level')

    if not level:
        return Response({"error": "Missing CCNA level"}, status=400)

    try:
        level = int(level)
        if level not in [1, 2, 3]:
            return Response({"error": "Level must be 1, 2, or 3"}, status=400)
    except ValueError:
        return Response({"error": "Invalid level format"}, status=400)

    question = Question.objects.filter(
        ccna_level=level,
        is_active=True
    ).prefetch_related(
        Prefetch('answers', queryset=Answer.objects.filter(is_active=True))
    ).order_by('?').first()

    if not question:
        return Response({"error": "No questions found for this level"}, status=404)

    # Debugging output
    if question.image:
        print(f"Cloudinary URL: {question.image.url}")
        print(f"Image field: {question.image}")
        print(f"Image name: {question.image.name}")

    serializer = QuestionSerializer(question, context={
        'request': request,
        'use_cloudinary': True
    })

    return Response(serializer.data)