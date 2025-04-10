from rest_framework import serializers
from .models import Question, Answer

class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['answer', 'is_correct']
        extra_kwargs = {
            'answer': {'label': 'Answer'},
            'is_correct': {'label': 'Correct Answer'},
        }

class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)  # No need for source='answers' here if it's a direct relationship
    ccna_level_display = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()
    points = serializers.IntegerField(required=False)
    explanation = serializers.CharField(required=False, allow_blank=True)
    additional_metadata = serializers.DictField(required=False, allow_null=True)

    class Meta:
        model = Question
        fields = [
            'title',
            'answers',
            'ccna_level_display',
            'image_url',
            'points',
            'explanation',
            'additional_metadata',
        ]
        extra_kwargs = {
            'title': {'label': 'Title'},
        }

    def get_ccna_level_display(self, obj):
        return obj.get_ccna_level_display()

    def get_image_url(self, obj):
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
