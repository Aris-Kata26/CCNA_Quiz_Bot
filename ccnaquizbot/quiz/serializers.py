from rest_framework import serializers
from .models import Question, Answer
import os
import re
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
        try:
            if not obj.image:
                logger.debug(f"No image for question {obj.id}")
                return None

            image_str = str(obj.image).strip()
            logger.debug(f"Raw image field for question {obj.id}: {image_str}")

            # Validate image field is not empty or invalid
            if not image_str or image_str in ['res', '/']:
                logger.warning(f"Invalid image field for question {obj.id}: {image_str}")
                return None

            # Check if the image field contains a full Cloudinary URL
            if image_str.startswith(('http://', 'https://')):
                # Ensure it's a Cloudinary URL
                if 'res.cloudinary.com' in image_str:
                    # Handle URLs with or without version number
                    if '/upload/v' in image_str:
                        optimized_url = image_str.replace('/upload/v', '/upload/q_auto,f_auto/v')
                    else:
                        optimized_url = image_str.replace('/upload/', '/upload/q_auto,f_auto/')
                    logger.debug(f"Optimized Cloudinary URL: {optimized_url}")
                    return optimized_url
                else:
                    logger.debug(f"Non-Cloudinary URL for question {obj.id}: {image_str}")
                    return image_str  # Return as-is if not Cloudinary

            # Handle CloudinaryField public ID (e.g., '5.ccna2_vu1frn')
            cloud_name = os.environ.get('CLOUDINARY_CLOUD_NAME')
            if not cloud_name:
                logger.error("CLOUDINARY_CLOUD_NAME environment variable not set")
                return None

            # Validate public ID: no slashes, not empty, reasonable length
            if '/' in image_str or len(image_str) < 3:
                logger.warning(f"Invalid public ID for question {obj.id}: {image_str}")
                return None

            # Construct URL from public ID
            optimized_url = f"https://res.cloudinary.com/{cloud_name}/image/upload/q_auto,f_auto/{image_str}"
            logger.debug(f"Constructed Cloudinary URL from public ID: {optimized_url}")
            return optimized_url

        except Exception as e:
            logger.error(f"Error processing image URL for question {obj.id}: {str(e)}")
            return None