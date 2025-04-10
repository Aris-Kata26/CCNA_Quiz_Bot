from django.db import models
from django.utils.translation import gettext as _

class Question(models.Model):
    LEVEL = (
        (0, _('Any')),
        (1, _('Level 1')),  # CCNA1
        (2, _('Level 2')),  # CCNA2
        (3, _('Level 3'))  # CCNA3
       
    )
    
    title = models.CharField(_("title"), max_length=500)
    points = models.SmallIntegerField(_("points"))
    ccna_level = models.IntegerField(_("CCNA Level"), choices=LEVEL, default=0)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created"), auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True, auto_now_add=False)
    explanation = models.TextField(_("Explanation"), blank=True, null=True)
    image = models.ImageField(_("Question Image"), upload_to='questions/images/', blank=True, null=True)

    def __str__(self):
        return self.title

class Answer(models.Model):
    question = models.ForeignKey(Question, related_name='answers', on_delete=models.CASCADE)
    answer = models.CharField(_("Answer"), max_length=500)
    is_correct = models.BooleanField(_("Correct Answer"), default=False)
    is_active = models.BooleanField(_("Is Active"), default=True)
    created_at = models.DateTimeField(_("Created"), auto_now=False, auto_now_add=True)
    updated_at = models.DateTimeField(_("Updated"), auto_now=True, auto_now_add=False)
    
    def __str__(self):
        return self.answer