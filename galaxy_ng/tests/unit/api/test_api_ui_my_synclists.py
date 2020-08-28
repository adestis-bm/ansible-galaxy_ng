import logging

from django.conf import settings
from rest_framework import status as http_code

from galaxy_ng.app.models import auth as auth_models
from . import base

from .synclist_base import BaseSyncListViewSet, ACCOUNT_SCOPE

log = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.DEBUG)

log.info("settings.FIXTURE_DIRS(%s scope): %s", settings.FIXTURE_DIRS)


class TestUiMySyncListViewSet(BaseSyncListViewSet):
    def setUp(self):
        super().setUp()

        log.info("self.fixtures2: %s", self.fixtures)
        log.info("settings.FIXTURE_DIRS2: %s", settings.FIXTURE_DIRS)

        self.user = auth_models.User.objects.create_user(username="test1", password="test1-secret")
        self.group = self._create_group_with_synclist_perms(
            ACCOUNT_SCOPE, "test1_group", users=[self.user]
        )
        self.user.save()
        self.group.save()

        self.user.groups.add(self.group)
        self.user.save()

        self.synclist_name = "test_synclist"
        self.synclist = self._create_synclist(
            name=self.synclist_name,
            repository=self.repo,
            upstream_repository=self.default_repo,
            groups=[self.group],
        )

        self.client.force_authenticate(user=self.user)

    def test_my_synclist_create(self):
        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [],
            "policy": "include",
            "groups": [
                {
                    "id": self.group.id,
                    "name": self.group.name,
                    "object_permissions": self.default_owner_permissions,
                },
            ],
        }

        synclists_url = base.get_current_ui_url("my-synclists-list")

        response = self.client.post(synclists_url, post_data, format="json")

        log.debug("response: %s", response)
        log.debug("response.data: %s", response.data)

        # synclist create is not allowed via my-synclist viewset
        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN, msg=response.data)

    def test_my_synclist_update(self):
        ns_name = "unittestnamespace1"
        ns = self._create_namespace(ns_name, groups=[self.group])
        ns.save()

        post_data = {
            "repository": self.repo.pulp_id,
            "collections": [],
            "namespaces": [ns_name],
            "policy": "include",
            "groups": [
                {
                    "id": self.group.id,
                    "name": self.group.name,
                    "object_permissions": self.default_owner_permissions,
                },
            ],
        }

        synclists_detail_url = base.get_current_ui_url(
            "my-synclists-detail", kwargs={"pk": self.synclist.id}
        )

        response = self.client.patch(synclists_detail_url, post_data, format="json")

        log.debug("response: %s", response)
        log.debug("response.data: %s", response.data)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertIn("repository", response.data)
        self.assertEqual(response.data["name"], self.synclist_name)
        self.assertEqual(response.data["policy"], "include")

        # Sort permission list for comparison
        response.data["groups"][0]["object_permissions"].sort()
        self.default_owner_permissions.sort()
        self.assertEquals(
            response.data["groups"],
            [
                {
                    "name": self.group.name,
                    "id": self.group.id,
                    "object_permissions": self.default_owner_permissions,
                }
            ],
        )

    def test_my_synclist_list(self):
        synclists_url = base.get_current_ui_url("my-synclists-list")
        log.debug("synclists_url: %s", synclists_url)

        response = self.client.get(synclists_url)

        log.debug("response: %s", response)
        data = response.data["data"]

        self.assertIsInstance(data, list)
        self.assertEquals(len(data), 1)
        self.assertEquals(data[0]["name"], self.synclist_name)
        self.assertEquals(data[0]["policy"], "exclude")
        self.assertEquals(data[0]["repository"], self.repo.pulp_id)

    def test_my_synclist_detail(self):
        synclists_detail_url = base.get_current_ui_url(
            "my-synclists-detail", kwargs={"pk": self.synclist.id}
        )

        log.debug("synclists_detail_url: %s", synclists_detail_url)

        response = self.client.get(synclists_detail_url)

        log.debug("response: %s", response)

        self.assertEqual(response.status_code, http_code.HTTP_200_OK)
        self.assertIn("name", response.data)
        self.assertIn("repository", response.data)
        self.assertEqual(response.data["name"], self.synclist_name)
        self.assertEqual(response.data["policy"], "exclude")
        self.assertEqual(response.data["collections"], [])
        self.assertEqual(response.data["namespaces"], [])

    def test_my_synclist_delete(self):
        synclists_detail_url = base.get_current_ui_url(
            "my-synclists-detail", kwargs={"pk": self.synclist.id}
        )

        log.debug("delete url: %s", synclists_detail_url)

        response = self.client.delete(synclists_detail_url)

        log.debug("delete response: %s", response)

        self.assertEqual(response.status_code, http_code.HTTP_403_FORBIDDEN)
