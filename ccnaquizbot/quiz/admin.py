from django.contrib import admin
from django import forms
from django.core.exceptions import ValidationError
from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'explanation', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

class QuestionAdminForm(forms.ModelForm):
    cloudinary_url = forms.CharField(
        required=False,
        label="Full Cloudinary URL",
        help_text="Paste EXACT URL including version (https://res.cloudinary.com/aristide/image/upload/v123456/filename.jpg)",
        widget=forms.TextInput(attrs={
            'placeholder': 'https://res.cloudinary.com/aristide/image/upload/v1744625190/1.ccna2_paeviz.png'
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
            raise ValidationError("Please use either file upload OR Cloudinary URL, not both.")
        
        if cloudinary_url:
            if not cloudinary_url.startswith('https://res.cloudinary.com/aristide/'):
                raise ValidationError({
                    'cloudinary_url': "URL must be from res.cloudinary.com/aristide"
                })
            # Normalize URL to lowercase 'aristide'
            cleaned_data['cloudinary_url'] = cloudinary_url.replace(
                'res.cloudinary.com/Aristide/',
                'res.cloudinary.com/aristide/'
            )
        return cleaned_data

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
            'description': 'Upload file OR paste full Cloudinary URL with version'
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
            # Store the exact URL string if provided
            obj.image = cloudinary_url
        super().save_model(request, obj, form, change)