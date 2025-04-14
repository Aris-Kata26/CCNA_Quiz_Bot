from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField

class Question(models.Model):
    LEVEL = (
        (0, _('Any')),
        (1, _('Level 1')),  # CCNA1
        (2, _('Level 2')),  # CCNA2
        (3, _('Level 3'))   # CCNA3
    )
    
    title = models.CharField(_("title"), max_length=500)
    points = models.SmallIntegerField(_("points"), default=1)
    ccna_level = models.IntegerField(_("CCNA Level"), choices=LEVEL, default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created"), auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True, auto_now_add=False)
    image = CloudinaryField(_("image"), blank=True, null=True)

    class Meta:
        verbose_name = _("Question")
        verbose_name_plural = _("Questions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['ccna_level']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return self.title
    
    def get_original_image_url(self):
        """Returns the exact Cloudinary URL needed for Discord"""
        if not self.image:
            return None
            
        if isinstance(self.image, str) and self.image.startswith('http'):
            return self.image
            
        if hasattr(self.image, 'version'):
            return (
                f"https://res.cloudinary.com/{self.image.metadata['cloud_name']}/"
                f"image/upload/{self.image.version}/{self.image.public_id}.{self.image.format}"
            )
        return self.image.url if hasattr(self.image, 'url') else None
    
    def clean(self):
        """Validate model before saving"""
        if self.points < 0:
            raise ValidationError(_("Points cannot be negative"))
        
        if self.pk and not self.answers.filter(is_correct=True).exists():
            raise ValidationError(_("Question must have at least one correct answer"))

class Answer(models.Model):
    question = models.ForeignKey(
        Question, 
        related_name='answers', 
        on_delete=models.CASCADE, 
        verbose_name=_("Question")
    )
    answer = models.CharField(_("Answer"), max_length=500)
    is_correct = models.BooleanField(_("Correct Answer"), default=False)
    explanation = models.TextField(_("Explanation"), blank=True, null=True)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created"), auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True, auto_now_add=False)

    class Meta:
        verbose_name = _("Answer")
        verbose_name_plural = _("Answers")
        ordering = ['-created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['question', 'answer'],
                name='unique_answer_per_question'
            )
        ]
        
    def __str__(self):
        return f"{self.answer[:50]}..." if len(self.answer) > 50 else self.answer

    def clean(self):
        if (self.is_correct and 
            self.question and 
            self.question.pk and
            self.question.answers.filter(is_correct=True).exclude(pk=self.pk).exists()):
            raise ValidationError(_("Another correct answer already exists for this question"))