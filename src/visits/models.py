from django.db import models

# Create your models here.

class PageVisit(models.Model):
    # db - table
    #id -> hiddem -> primamry key -> autofield 1,2,3,4 and so on
    path = models.TextField(blank=True, null=True) #col
    timestamp = models.DateTimeField(auto_now_add=True) #col
