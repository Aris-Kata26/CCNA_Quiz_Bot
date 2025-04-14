from rest_framework import serializers
from .models import Question, Answer

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
        if obj.image and hasattr(obj.image, 'url'):
            try:
                raw_url = str(obj.image.url)
                print(f"Raw image URL: {raw_url}")  # Debug log
                # Ensure URL is absolute
                if not raw_url.startswith(('http://', 'https://')):
                    raw_url = f"https:{raw_url}" if raw_url.startswith('//') else f"https://res.cloudinary.com/{os.environ.get('CLOUDINARY_CLOUD_NAME')}/image/upload/{raw_url}"
                # Add Cloudinary optimizations
                optimized_url = raw_url.replace('/upload/', '/upload/q_auto,f_auto/')
                print(f"Optimized URL: {optimized_url}")  # Debug log
                return optimized_url
            except Exception as e:
                print(f"Error processing image URL: {e}")
                return None
        print("No image or invalid image field")
        return None