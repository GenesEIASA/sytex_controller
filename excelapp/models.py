from django.db import models

class ExcelFile(models.Model):
    file = models.FileField(upload_to='excels/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
