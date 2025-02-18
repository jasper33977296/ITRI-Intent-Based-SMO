# main/apps/metadata_mgt/models/ScenarioModel.py

import uuid
from django.db import models

class Scenario(models.Model):
    scenario_id = models.AutoField(primary_key=True)
    scenario_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    scenario_name = models.CharField(max_length=255)
    scenario_description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'scenario'

    def __str__(self):
        return f"{self.scenario_name}"
