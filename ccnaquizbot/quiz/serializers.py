from rest_framework import serializers
from .models import Question, Answer
import logging

logger = logging.getLogger(__name__)

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'answer', 'is_correct', 'explanation']
        extra_kwargs = {
            'answer': {'label': 'Answer'},
            'is_correct': {'label': 'Correct Answer'},
        }

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    ccna_level_display = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    points = serializers.IntegerField(required=False)

    class Meta:
        model = Question
        fields = [
            'id',
            'title',
            'points',
            'ccna_level',
            'ccna_level_display',
            'image_url',
            'is_active',
            'answers',
            'created_at',
            'updated_at',
        ]
        extra_kwargs = {
            'title': {'label': 'Title'},
            'points': {'required': False}
        }

    def get_ccna_level_display(self, obj):
        return obj.get_ccna_level_display()

    def get_image_url(self, obj):
        """
        Returns the exact Cloudinary URL needed for Discord embeds
        - Preserves version numbers (v1744625190)
        - Maintains original URL structure
        - Handles both direct URLs and public IDs
        """
        try:
            if not obj.image:
                logger.debug(f"No image for question {obj.id}")
                return None

            # Get the stored image value
            image_value = str(obj.image).strip()
            
            # Case 1: Already a full URL (from admin paste)
            if image_value.startswith(('http://', 'https://')):
                if 'res.cloudinary.com' in image_value:
                    # Ensure consistent lowercase 'aristide' in URL
                    normalized_url = image_value.replace(
                        'res.cloudinary.com/Aristide/',
                        'res.cloudinary.com/aristide/'
                    )
                    logger.debug(f"Using direct Cloudinary URL: {normalized_url}")
                    return normalized_url
                # Non-Cloudinary URL (unlikely in your case)
                return image_value

            # Case 2: Cloudinary public ID (from file upload)
            if hasattr(obj, 'get_cloudinary_url'):
                url = obj.get_cloudinary_url()
                logger.debug(f"Using get_cloudinary_url(): {url}")
                return url

            # Fallback: Construct URL from public ID (legacy support)
            cloud_name = 'aristide'  # Hardcoded to match your requirements
            if '/' not in image_value:  # Basic public ID validation
                constructed_url = (
                    f"https://res.cloudinary.com/{cloud_name}/"
                    f"image/upload/{image_value}"
                )
                logger.debug(f"Constructed URL from public ID: {constructed_url}")
                return constructed_url

            logger.warning(f"Unrecognized image format for question {obj.id}: {image_value}")
            return None

        except Exception as e:
            logger.error(f"Error processing image URL for question {obj.id}: {str(e)}")
            return None