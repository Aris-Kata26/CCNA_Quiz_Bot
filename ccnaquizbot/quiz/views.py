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
    try:
        level = request.GET.get('level')

        if not level:
            logger.warning("Missing CCNA level parameter")
            return Response({"error": "Missing CCNA level"}, status=400)

        try:
            level = int(level)
            if level not in [1, 2, 3]:
                logger.warning(f"Invalid level: {level}")
                return Response({"error": "Level must be 1, 2, or 3"}, status=400)
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

        # Debugging output for image
        if question.image:
            try:
                logger.debug(f"Image field for question {question.id}: {question.image}")
                logger.debug(f"Image name: {question.image.name}")
                logger.debug(f"Cloudinary URL: {question.image.url}")
            except Exception as e:
                logger.error(f"Error accessing image for question {question.id}: {str(e)}")

        serializer = QuestionSerializer(question)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Error in get_ccna_question: {str(e)}", exc_info=True)
        return Response({"error": "Server error"}, status=500)