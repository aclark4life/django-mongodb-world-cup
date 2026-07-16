from django.db import models

# Create your models here.
from django.db import models
from django_mongodb_backend.fields import EmbeddedModelArrayField
from django_mongodb_backend.managers import MongoManager
from django_mongodb_backend.models import EmbeddedModel


class Goal(EmbeddedModel):
    name = models.CharField(max_length=100)
    minute = models.CharField(max_length=10)     
    penalty = models.BooleanField(default=False)
    own_goal = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.minute}')"


class Match(models.Model):
    num = models.IntegerField(null=True, blank=True)        
    round = models.CharField(max_length=50)
    date = models.DateField()
    kickoff_time = models.CharField(max_length=20)           
    group = models.CharField(max_length=20, blank=True)      
    ground = models.CharField(max_length=100)
    team1 = models.CharField(max_length=100)
    team2 = models.CharField(max_length=100)
    ft_score1 = models.IntegerField(null=True, blank=True)   
    ft_score2 = models.IntegerField(null=True, blank=True)
    ht_score1 = models.IntegerField(null=True, blank=True)
    ht_score2 = models.IntegerField(null=True, blank=True)
    et_score1 = models.IntegerField(null=True, blank=True)
    et_score2 = models.IntegerField(null=True, blank=True)
    pen_score1 = models.IntegerField(null=True, blank=True)
    pen_score2 = models.IntegerField(null=True, blank=True)
    goals1 = EmbeddedModelArrayField(Goal, default=list, blank=True)
    goals2 = EmbeddedModelArrayField(Goal, default=list, blank=True)

    objects = MongoManager()

    def __str__(self):
        return f"{self.team1} vs {self.team2} ({self.round})"