from django.urls import path

from jobs.presentation.views import (
    CreateJobView,
    GetUpdateDeleteJobView, 
    ListJobsView,
    CancelJobView,
)

app_name = "jobs"

urlpatterns = [
    path("", CreateJobView.as_view(), name="create_job"),
    path("list/", ListJobsView.as_view(), name="list_jobs"),
    path("<uuid:job_id>/", GetUpdateDeleteJobView.as_view(), name="get_update_delete_job"),
    path("<uuid:job_id>/cancel/", CancelJobView.as_view(), name="cancel_job"),
]
