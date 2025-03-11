from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    is_teacher = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username} - {'Mugallym' if self.is_teacher else 'Okuwçy'}"

class Test(models.Model):
    teacher = models.ForeignKey(User, on_delete=models.CASCADE)
    test_code = models.CharField(max_length=20, unique=True)
    time_limit = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.test_code

class Question(models.Model):
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    text = models.TextField()
    options = models.JSONField()
    correct_answer = models.CharField(max_length=1)

    def __str__(self):
        return self.text

class Result(models.Model):
    student_name = models.CharField(max_length=100)
    class_name = models.CharField(max_length=10)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    score = models.IntegerField()
    completed_at = models.DateTimeField(auto_now_add=True)
    duration_minutes = models.FloatField(null=True, blank=True)  # Testin tamamlanma süresi (dakika)

    def __str__(self):
        return f"{self.student_name} - {self.test.test_code}"
