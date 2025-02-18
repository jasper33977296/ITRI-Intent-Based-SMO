# main/apps/metadata_mgt/models/ApiFlowModel.py

import uuid
from django.db import models
from .ScenarioModel import Scenario

class ApiFlow(models.Model):
    api_flow_id = models.AutoField(primary_key=True)
    api_flow_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    api_flow_name = models.CharField(max_length=255)
    api_flow_description = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 外鍵連到 Scenario.scenario_uid
    f_scenario_uid = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        to_field='scenario_uid',  # 連接到 Scenario 的 scenario_uid 欄位
        db_column='f_scenario_uid',
        related_name='api_flows'
    )

    class Meta:
        db_table = 'api_flow'

    def __str__(self):
        return f"{self.api_flow_name}"
