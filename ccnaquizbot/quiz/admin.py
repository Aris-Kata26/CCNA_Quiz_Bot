from django.contrib import admin
from django import forms
from .models import Question, Answer

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1
    fields = ['answer', 'is_correct', 'explanation', 'is_active']
    readonly_fields = ['created_at', 'updated_at']

class QuestionAdminForm(forms.ModelForm):
    cloudinary_url = forms.URLField(
        required=False,
        label="Or paste Cloudinary URL",
        help_text="Alternative to file upload - paste full URL (e.g., https://res.cloudinary.com/...)",
        widget=forms.URLInput(attrs={
            'placeholder': 'https://res.cloudinary.com/...'
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
            raise forms.ValidationError("Please use either file upload OR Cloudinary URL, not both.")
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
            'description': 'Upload an image file OR paste a Cloudinary URL'
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
            # If Cloudinary URL was provided, use it instead of file upload
            obj.image = cloudinary_url
        super().save_model(request, obj, form, change)