from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)  # Email is now unique
    year = models.CharField(max_length=10, choices=[("I", "I"), ("II", "II"), ("III", "III"), ("IV", "IV")])
    section = models.CharField(max_length=10)
    leetcode = models.CharField(max_length=100, unique=True)
    codechef = models.CharField(max_length=100, unique=True)
    hackerrank = models.CharField(max_length=100, unique=True)
    codeforces = models.CharField(max_length=100, unique=True)

    # Remove conflicts
    groups = models.ManyToManyField("auth.Group", related_name="customuser_set", blank=True)
    user_permissions = models.ManyToManyField("auth.Permission", related_name="customuser_set", blank=True)

    # Set email as the login field
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]  # Username is still required but not used for login

    def __str__(self):
        return self.email  # Display email instead of username
