# main/apps/metadata_mgt/models/ApiFlowStepModel.py

import uuid
from django.db import models
from django.db.models import JSONField
from .ApiFlowModel import ApiFlow

class ApiFlowStep(models.Model):
    api_flow_step_id = models.AutoField(primary_key=True)
    api_flow_step_uid = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    api_flow_step_name = models.CharField(max_length=255)
    api_flow_step_description = models.CharField(max_length=255, blank=True, null=True)
    endpoint = models.CharField(max_length=255, blank=True, null=True)
    method = models.CharField(max_length=10, blank=True, null=True)
    field = JSONField(blank=True, null=True)  # PostgreSQL 原生 JSON
    api_flow_step_ready = models.BooleanField(default=False, help_text="所有欄位都ready時，設為True")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # 外鍵連到 ApiFlow.api_flow_uid
    f_api_flow_uid = models.ForeignKey(
        ApiFlow,
        on_delete=models.CASCADE,
        to_field='api_flow_uid',  # 連接到 ApiFlow 的 api_flow_uid
        db_column='f_api_flow_uid',
        related_name='api_flow_steps'
    )

    class Meta:
        db_table = 'api_flow_step'

    def __str__(self):
        return f"{self.api_flow_step_name}"
