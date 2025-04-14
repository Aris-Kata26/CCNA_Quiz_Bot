from django.contrib import admin
from django import forms
from .models import Question, Answer
from cloudinary.uploader import upload
import re

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'explanation', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

class QuestionAdminForm(forms.ModelForm):
    cloudinary_url = forms.CharField(
        required=False,
        label="Or enter Cloudinary public ID/URL",
        help_text="Alternative to file upload - paste either public ID (e.g., 'questions/ccna2_paeviz') or full URL",
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
        return cleaned_data

    def extract_public_id(self, url):
        """Extract public ID from Cloudinary URL"""
        pattern = r'/(?:v\d+/)?([^/\.]+)(?:/|\.|$)'
        match = re.search(pattern, url)
        return match.group(1) if match else None

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
            # If Cloudinary reference was provided
            if cloudinary_url.startswith(('http://', 'https://')):
                # Extract public ID from URL
                public_id = form.extract_public_id(cloudinary_url)
                if public_id:
                    obj.image = public_id
                else:
                    raise forms.ValidationError("Could not extract public ID from Cloudinary URL")
            else:
                # Assume it's already a public ID
                obj.image = cloudinary_url
        
        super().save_model(request, obj, form, change)