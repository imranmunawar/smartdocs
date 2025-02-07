from django.db import models

class Category(models.Model):
    
    name = models.CharField(max_length=50, help_text='Name of the category')
    status = models.BooleanField(default = True)
    parent_category = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    sequence_id = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name