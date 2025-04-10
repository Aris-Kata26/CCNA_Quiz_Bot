from django.contrib import admin
from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Question)

class QuestionAdmin(admin.ModelAdmin):
    fields = [
        'title',
        'points',
        'ccna_level',
        'explanation',
        'image',
        'is_active',
        'created_at',
        'updated_at',
    ]
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
        'explanation',
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AnswerInline]