from django.db import models
# Create your models here.
from django.db import models

class UploadedImage(models.Model):
    image = models.ImageField(upload_to='image/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
