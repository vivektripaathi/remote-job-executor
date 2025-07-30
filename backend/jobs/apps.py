from django.apps import AppConfig


class JobsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'jobs'
    inject_container = None

    def ready(self):
        from jobs.inject import JobContainer
        import jobs.presentation.views
        from jobs.domain.use_cases import (
            create_job_use_case,
            get_job_use_case,
            list_jobs_use_case,
            update_job_use_case,
            cancel_job_use_case,
            delete_job_use_case,
            execute_remote_command_use_case,
            execute_remote_command_streaming_use_case,
            kill_remote_process_use_case,
        )

        self.inject_container = JobContainer()
        self.inject_container.wire(
            modules=[
                jobs.presentation.views,
                create_job_use_case,
                get_job_use_case,
                list_jobs_use_case,
                update_job_use_case,
                cancel_job_use_case,
                delete_job_use_case,
                execute_remote_command_use_case,
                execute_remote_command_streaming_use_case,
                kill_remote_process_use_case,
            ],
        )
