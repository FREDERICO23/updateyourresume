from django.db import models
from django.contrib.auth.models import User

class GeneratedResume(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    job_title = models.CharField(max_length=100)
    job_description = models.TextField(null=True)
    existing_resume =  models.TextField(null=True)
    generated_text = models.TextField(null=True)

    def __str__(self):
        return f"Generated Resume for {self.job_title}"
class GeneratedCoverLetter(models.Model):
    # user = models.ForeignKey(User, on_delete=models.CASCADE)
    generated_resume = models.ForeignKey(GeneratedResume, on_delete=models.CASCADE)
    generated_text = models.TextField()

    def __str__(self):
        return f"GeneratedCoverLetter for {self.generated_resume}"