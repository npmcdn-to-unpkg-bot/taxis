from django.db import models
from django.contrib.auth.models import User

# Create your models here.

GENDER_CHOICES = (
    ('M', 'Hombre'),
    ('F', 'Mujer'),
)

def avatar_upload_to(instance, filename):
    id = instance.user.id
    basename, file_extention = filename.split(".")
    new_filename = "%s_%s.%s" % (instance.id, basename, file_extention)
    return "user/avatar/%s/%s" % (id, new_filename)

class UserExtended(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id_document = models.CharField(max_length=20)
    blood_type = models.CharField(max_length=4, blank=True)
    birthdate = models.DateField(blank=True)
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    avatar = models.ImageField(blank=True, upload_to=avatar_upload_to)

    def __str__(self):
        return self.user.first_name
