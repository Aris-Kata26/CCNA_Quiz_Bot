from django.db import models
from django.utils.translation import gettext as _
from django.core.exceptions import ValidationError
from cloudinary.models import CloudinaryField
import logging

logger = logging.getLogger(__name__)

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
    
    def get_ccna_level_display(self):
        """Return human-readable CCNA level for serializer"""
        return dict(self.LEVEL).get(self.ccna_level, _('Unknown'))

    def get_original_image_url(self):
        """
        Returns the exact Cloudinary URL needed for Discord embeds
        Handles both manual URLs and CloudinaryField objects
        """
        if not self.image:
            return None
            
        # If image contains a full URL (manually entered in admin)
        if isinstance(self.image, str) and self.image.startswith(('http://', 'https://')):
            # Normalize URL case
            normalized_url = self.image.replace(
                'res.cloudinary.com/Aristide/',
                'res.cloudinary.com/aristide/'
            )
            return normalized_url
            
        # For CloudinaryField objects
        if hasattr(self.image, 'url'):
            # Return the versioned URL if available
            if hasattr(self.image, 'version'):
                return (
                    f"https://res.cloudinary.com/{self.image.metadata['cloud_name']}/"
                    f"image/upload/{self.image.version}/{self.image.public_id}.{self.image.format}"
                )
            return self.image.url
            
        return None

    def clean(self):
        """Validate model before saving"""
        if self.points < 0:
            raise ValidationError(_("Points cannot be negative"))
        
        # Validate image field
        if self.image:
            # If it's a string (manual URL entry)
            if isinstance(self.image, str):
                if not self.image.startswith('https://res.cloudinary.com/aristide/'):
                    raise ValidationError(_("Cloudinary URL must be from res.cloudinary.com/aristide"))
                
                # Normalize URL case
                self.image = self.image.replace(
                    'res.cloudinary.com/Aristide/',
                    'res.cloudinary.com/aristide/'
                )
            
            # For CloudinaryField objects, validate public_id
            elif hasattr(self.image, 'public_id'):
                public_id = str(self.image.public_id).strip()
                if not public_id or '/' in public_id or len(public_id) < 3:
                    raise ValidationError(_("Invalid image public ID: must be a valid Cloudinary public ID"))

        # Validate answers
        if hasattr(self, 'answers') and self.answers.exists() and not self.answers.filter(is_correct=True).exists():
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
        return f"{self.question.title[:30]}... - {self.answer[:30]}" if len(self.answer) > 30 else f"{self.question.title[:30]} - {self.answer}"

    def clean(self):
        """Validate answer before saving"""
        if self.is_correct:
            existing_correct = self.question.answers.filter(is_correct=True).exclude(pk=self.pk)
            if existing_correct.exists():
                raise ValidationError(_("Another correct answer already exists for this question"))