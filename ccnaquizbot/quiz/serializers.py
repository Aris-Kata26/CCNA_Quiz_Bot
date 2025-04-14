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

    def get_answers(self, obj):
        answers = obj.answers.filter(is_active=True)
        return AnswerSerializer(answers, many=True).data if answers else []

    def get_ccna_level_display(self, obj):
        return obj.get_ccna_level_display()

    def get_image_url(self, obj):
        if obj.image:
            # For Cloudinary, just return the URL directly
            url = obj.image.url
            
            # Add Cloud