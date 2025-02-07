from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models.user import CustomUser
from .models.category import Category
from .models.template import Template
from .models.user_document import UserDocument
from .models.question import Question
from .models.answer import Answer
from .models.section import Section
from .models.option import Option

class CustomUserAdmin(UserAdmin):
    pass

@admin.register(Template)
class TemplateAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'category', 'user', 'template_file_name',
        'access_level', 'is_active'
    )

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'template', 'parent_section',
        'is_active', 'sequence_id', 'vimeo_link'
    )

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = (
        'question', 'placeholder', 'question_type',
        'parent_question', 'template', 'section', 'is_ai',
        'na_applicable', 'is_active', 'sequence_id'
    )

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'status', 'parent_category'
    )

admin.site.register(CustomUser, CustomUserAdmin)
admin.site.register(UserDocument)
admin.site.register(Answer)
admin.site.register(Option)
