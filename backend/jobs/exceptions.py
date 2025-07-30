from rest_framework import status, exceptions


class JobAlreadyExistsException(exceptions.APIException):
    code = "Job_0001"
    default_detail = "Job with same parameters already exists"
    status_code = status.HTTP_400_BAD_REQUEST


class JobDoesNotExistException(exceptions.APIException):
    code = "Job_0002" 
    default_detail = "Job with given id does not exist"
    status_code = status.HTTP_404_NOT_FOUND


class JobCannotBeCancelledException(exceptions.APIException):
    code = "Job_0003"
    default_detail = "Job cannot be cancelled in its current state"
    status_code = status.HTTP_400_BAD_REQUEST


class JobExecutionException(exceptions.APIException):
    code = "Job_0004"
    default_detail = "Job execution failed"
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR


class JobAlreadyRunningException(exceptions.APIException):
    code = "Job_0005"
    default_detail = "Job is already being processed by another worker"
    status_code = status.HTTP_409_CONFLICT
