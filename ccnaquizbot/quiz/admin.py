from django.contrib import admin
from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'explanation', 'is_active']  # Added explanation here
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    fields = [
        'title',
        'points',
        'ccna_level',
        'image',
        'is_active',
        'created_at',
        'updated_at',
    ]  # Removed 'explanation' from here
    list_display = [
        'title',
        'ccna_level',
        'points',
        'is_active',
        'updated_at',
    ]
    list_filter = [
        'ccna_level',
        'is_active',
    ]
    search_fields = [
        'title',
        'answers__explanation',  # Changed to search through related answers
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AnswerInline]