from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Question, Answer
from .serializers import QuestionSerializer
from django.db.models import Prefetch
import logging

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
def get_ccna_question(request):
    """
    Retrieve a random active CCNA question for the specified level.
    Query parameter: level (1, 2, or 3).
    Returns serialized question data or an error response.
    """
    try:
        level = request.GET.get('level')

        if not level:
            logger.warning("Missing CCNA level parameter")
            return Response({"error": "Missing CCNA level"}, status=400)

        try:
            level = int(level)
            valid_levels = [choice[0] for choice in Question.LEVEL if choice[0] != 0]  # Exclude 'Any'
            if level not in valid_levels:
                logger.warning(f"Invalid level: {level}")
                return Response({"error": f"Level must be one of {valid_levels}"}, status=400)
        except ValueError:
            logger.warning(f"Invalid level format: {level}")
            return Response({"error": "Invalid level format"}, status=400)

        question = Question.objects.filter(
            ccna_level=level,
            is_active=True
        ).prefetch_related(
            Prefetch('answers', queryset=Answer.objects.filter(is_active=True))
        ).order_by('?').first()

        if not question:
            logger.warning(f"No questions found for level {level}")
            return Response({"error": "No questions found for this level"}, status=404)

        # Rely on serializer for image handling
        serializer = QuestionSerializer(question)
        logger.debug(f"Serialized question {question.id}: {serializer.data.get('image_url') or 'no image'}")
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error in get_ccna_question: {str(e)}", exc_info=True)
        return Response({"error": "Server error"}, status=500)