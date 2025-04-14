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
            if obj.image:
                image_str = str(obj.image)
                logger.debug(f"Raw image field for question {obj.id}: {image_str}")
                # Handle legacy ImageField URLs
                if image_str.startswith(('http://', 'https://')):
                    # Extract public ID if possible
                    match = re.search(r'/image/upload/[^/]+/(.+?)(?:\.\w+)?$', image_str)
                    if match:
                        public_id = match.group(1)
                        logger.debug(f"Extracted public ID: {public_id}")
                        optimized_url = f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/image/upload/q_auto,f_auto/{public_id}.jpg"
                    else:
                        optimized_url = image_str.replace('/upload/', '/upload/q_auto,f_auto/')
                    logger.debug(f"Legacy URL optimized: {optimized_url}")
                    return optimized_url
                # Handle CloudinaryField public ID
                elif hasattr(obj.image, 'url'):
                    raw_url = str(obj.image.url)
                    logger.debug(f"Cloudinary raw URL: {raw_url}")
                    if not raw_url.startswith(('http://', 'https://')):
                        raw_url = f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/image/upload/{raw_url}"
                    optimized_url = raw_url.replace('/upload/', '/upload/q_auto,f_auto/')
                    logger.debug(f"Optimized URL: {optimized_url}")
                    return optimized_url
                else:
                    logger.warning(f"Invalid image field for question {obj.id}: {image_str}")
                    return None
            logger.debug(f"No image for question {obj.id}")
            return None
        except Exception as e:
            logger.error(f"Error processing image URL for question {obj.id}: {str(e)}")
            return None