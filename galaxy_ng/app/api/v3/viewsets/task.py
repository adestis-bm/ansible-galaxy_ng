import logging

from pulpcore.plugin import viewsets as pulp_core_viewsets

from galaxy_ng.app.api.base import LocalSettingsMixin
from galaxy_ng.app.api.v3.serializers import TaskSerializer
from galaxy_ng.app.access_control import access_policy

log = logging.getLogger(__name__)


class TaskViewSet(LocalSettingsMixin, pulp_core_viewsets.TaskViewSet):
    permission_classes = [access_policy.TaskAccessPolicy]
    serializer_class = TaskSerializer
