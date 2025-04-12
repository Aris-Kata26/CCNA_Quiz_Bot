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
    answers = AnswerSerializer(many=True, read_only=True)  # Get related answers
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
            'ccna_level_display'
            'image_url',
            'is_active',
            'answers',  # Include answers in the serialized data
            'created_at', 
            'updated_at',
        ]
        extra_kwargs = {
            'title': {'label': 'Title'},
            'points': {'required': False}
        }

    def get_answers(self, obj):
        # Ensure there are answers related to the question and filter for active ones
        answers = obj.answers.filter(is_active=True)
        # If no answers exist, return an empty list to avoid errors
        return AnswerSerializer(answers, many=True).data if answers else []

    def get_ccna_level_display(self, obj):
        return obj.get_ccna_level_display()  # Return level display for better readability

    def get_image_url(self, obj):
        # Ensure the 'request' context is passed for building image URLs
        request = self.context.get('request')
        if obj.image and request:
            return request.build_absolute_uri(obj.image.url)
        return None
