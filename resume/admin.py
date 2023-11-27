from django.contrib import admin
from .models import GeneratedCoverLetter, GeneratedResume

# Register your models here.
admin.site.register(GeneratedCoverLetter)
admin.site.register(GeneratedResume)