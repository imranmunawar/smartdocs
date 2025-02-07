from django.db import models
from .category import Category
from .user import CustomUser

class Template(models.Model):
    ACCESS_LEVEL_CHOICES =  [
        ('free', 'Level 0'),
        ('level-1', 'Level 1'),
        ('level-2', 'Level 2'),
        ('level-3', 'Level 3')
    ]
    name = models.CharField(max_length=300, help_text='Name of the Template')
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    user = models.ForeignKey(CustomUser, null=True, on_delete=models.SET_NULL)
    template_file_name = models.CharField(max_length=300, default=None, null=True)
    access_level = models.CharField(max_length=256, choices=ACCESS_LEVEL_CHOICES, default='free')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(db_column='created_at', blank=True, null=True)
    last_modified = models.DateTimeField(db_column='last_modified', blank=True, null=True)
    sequence_id = models.IntegerField(default=0)
    doc_placeholders = models.JSONField(default=list, blank=True, null=True)

    def __str__(self) -> str:
        return self.name

class AdminTemplate(models.Model):
    TEMPLATE_STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('review', 'Under Review'),
        ('approved', 'Approved'),
        ('published', 'Published'),
        ('archived', 'Archived')
    ]

    template_name = models.CharField(max_length=300)
    template_category = models.ForeignKey('AdminCategory', on_delete=models.CASCADE)
    template_owner = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='owned_templates'
    )
    access_level = models.CharField(max_length=256, choices=ACCESS_LEVEL_CHOICES)
    template_status = models.CharField(
        max_length=50, 
        choices=TEMPLATE_STATUS_CHOICES,
        default='draft'
    )
    is_published = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True,
        related_name='created_templates'
    )
    creation_date = models.DateTimeField(auto_now_add=True)
    last_modified_by = models.ForeignKey(
        CustomUser, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='modified_templates'
    )
    modification_date = models.DateTimeField(auto_now=True)
    admin_notes = models.TextField(blank=True)
    version_number = models.CharField(max_length=50)
    audit_history = models.JSONField(default=dict)

    class Meta:
        permissions = [
            ("can_approve_templates", "Can approve templates"),
            ("can_publish_templates", "Can publish templates"),
            ("can_archive_templates", "Can archive templates"),
        ]
        ordering = ['-modification_date']
        indexes = [
            models.Index(fields=['template_status', 'is_published']),
            models.Index(fields=['template_owner', 'creation_date'])
        ]
