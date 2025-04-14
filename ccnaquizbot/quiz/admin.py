from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Question, Answer
import re
import logging

logger = logging.getLogger(__name__)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'explanation', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

class QuestionAdminForm(forms.ModelForm):
    cloudinary_url = forms.CharField(
        required=False,
        label="Or enter Cloudinary public ID/URL",
        help_text="Alternative to file upload - paste either public ID (e.g., 'questions/ccna2_paeviz') or full URL (e.g., 'https://res.cloudinary.com/...')",
        widget=forms.TextInput(attrs={
            'placeholder': 'questions/ccna2_paeviz or https://res.cloudinary.com/...'
        })
    )

    class Meta:
        model = Question
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        image_file = cleaned_data.get('image')
        cloudinary_url = cleaned_data.get('cloudinary_url')

        if image_file and cloudinary_url:
            raise forms.ValidationError("Please use either file upload OR Cloudinary reference, not both.")

        if cloudinary_url:
            # Validate public ID or extract from URL
            public_id = self.extract_public_id(cloudinary_url)
            if not public_id:
                raise forms.ValidationError("Invalid Cloudinary public ID or URL.")
            # Basic public ID validation (mirrors models.py)
            if '/' not in public_id and len(public_id) < 3:
                raise forms.ValidationError("Public ID is too short or invalid.")
            cleaned_data['cloudinary_url'] = public_id

        return cleaned_data

    def extract_public_id(self, value):
        """Extract public ID from Cloudinary URL or return as-is if it's a public ID"""
        value = value.strip()
        if value.startswith(('http://', 'https://')):
            # Match Cloudinary URL, capturing public ID after /upload/ or /upload/v123/
            pattern = r'/image/upload/(?:v\d+/)?(.+?)(?:\.\w+)?$'
            match = re.search(pattern, value)
            if match:
                return match.group(1)
            return None
        # Assume it's already a public ID
        return value if value else None

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    form = QuestionAdminForm
    fieldsets = [
        (None, {
            'fields': [
                'title',
                'points',
                'ccna_level',
                'is_active'
            ]
        }),
        ('Image', {
            'fields': [
                'image',
                'cloudinary_url'
            ],
            'description': 'Upload an image file OR enter Cloudinary public ID/URL'
        }),
        ('Dates', {
            'fields': [
                'created_at',
                'updated_at'
            ],
            'classes': ['collapse']
        })
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
        'answers__explanation',
    ]
    readonly_fields = ['created_at', 'updated_at']
    inlines = [AnswerInline]

    def save_model(self, request, obj, form, change):
        cloudinary_url = form.cleaned_data.get('cloudinary_url')
        if cloudinary_url:
            # Use validated public ID from form
            obj.image = cloudinary_url
            logger.debug(f"Set image public ID for question {obj.id or 'new'}: {obj.image}")
        
        # Let CloudinaryField handle file uploads automatically
        try:
            super().save_model(request, obj, form, change)
        except ValidationError as e:
            logger.error(f"Validation error saving question {obj.id or 'new'}: {str(e)}")
            raise