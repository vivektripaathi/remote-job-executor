import uuid
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

class JobStatusChoice(models.TextChoices):
    QUEUED = "Queued", _("Queued")
    RUNNING = "Running", _("Running")
    SUCCESS = "Success", _("Success")
    FAILED = "Failed", _("Failed")
    CANCELLED = "Cancelled", _("Cancelled")


class JobPriorityChoice(models.TextChoices):
    LOW = "Low", _("Low")
    MEDIUM = "Medium", _("Medium")
    HIGH = "High", _("High")


class Job(models.Model):
    id = models.UUIDField(
        default=uuid.uuid4, editable=False, unique=True, db_index=True, primary_key=True
    )
    command = models.TextField()
    timeout = models.IntegerField(default=60)  # seconds
    priority = models.CharField(
        max_length=255,
        choices=JobPriorityChoice.choices,
        default=JobPriorityChoice.MEDIUM,
        null=False,
        blank=False,
    )
    status = models.CharField(
        max_length=255,
        choices=JobStatusChoice.choices,
        default=JobStatusChoice.QUEUED,
        null=False,
        blank=False,
    )
    parameters = models.JSONField(null=True, blank=True)
    stdout = models.TextField(null=True, blank=True)
    stderr = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    modified_at = models.DateTimeField(default=timezone.now)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    task_id = models.CharField(max_length=255, null=True, blank=True)
    remote_process_id = models.CharField(max_length=255, null=True, blank=True)


    class Meta:
        db_table = "jobs"
