from typing import List, Optional, Union

from .. import exceptions
from ..auth import Auth
from ..balena_auth import request
from ..base_request import BaseRequest
from ..pine import pine
from ..settings import Settings
from ..types import AnyObject, ResourceKey
from ..types.models import (
    OrganizationInviteType,
    OrganizationMembershipTagType,
    OrganizationMembershipType,
    OrganizationType,
)
from ..utils import is_id, merge
from ..dependent_resource import DependentResource
from .config import Config


class Organization:
    """
    This class implements organization model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.invite = OrganizationInvite()
        self.membership = OrganizationMembership()

    def create(
        self, name: str, handle: Optional[str] = None
    ) -> OrganizationType:
        """
        Creates a new organization.

        Args:
            name (str): the name of the organization that will be created.
            handle (Optional[str]): The handle of the organization that will be created.

        Returns:
            dict: organization info.

        Examples:
            >>> balena.models.organization.create('My Org', 'test_org')
        """

        data = {"name": name}
        if handle is not None:
            data["handle"] = handle

        return pine.post({"resource": "organization", "body": data})

    def get_all(self, options: AnyObject = {}) -> List[OrganizationType]:
        """
        Get all organizations.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[OrganizationType]: list contains information of organizations.

        Examples:
            >>> balena.models.organization.get_all()
        """

        return pine.get(
            {
                "resource": "organization",
                "options": merge({"$orderby": "name asc"}, options),
            }
        )

    def get(
        self, handle_or_id: Union[str, int], options: AnyObject = {}
    ) -> OrganizationType:
        """
        Get a single organization.

        Args:
            handle_or_id (str): organization handle (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            dict: organization info.

        Raises:
            OrganizationNotFound: if organization couldn't be found.

        Examples:
            >>> balena.models.organization.get(26474)
            >>> balena.models.organization.get('myorg')
        """

        if handle_or_id is None:
            raise exceptions.InvalidParameter("handle_or_id", handle_or_id)

        org = pine.get(
            {
                "resource": "organization",
                "id": handle_or_id
                if is_id(handle_or_id)
                else {"handle": handle_or_id},
                "options": options,
            }
        )

        if org is None:
            raise exceptions.OrganizationNotFound(handle_or_id)

        return org

    def remove(self, handle_or_id: Union[str, int]) -> None:
        """
        Remove an organization.

        Args:
            handle_or_id (str): organization handle (string) or id (number).

        Examples:
            >>> balena.models.organization.remove(148003)
        """
        org_id = self.get(handle_or_id, {"$select": "id"})["id"]
        pine.delete({"resource": "organization", "id": org_id})


class OrganizationInvite:
    """
    This class implements organization invite model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.RESOURCE = "invitee__is_invited_to__organization"

    def get_all(self, options: AnyObject = {}) -> List[OrganizationInviteType]:
        """
        Get all invites.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[OrganizationInviteType]: list contains info of invites.

        Examples:
            >>> balena.models.organization.invite.get_all()
        """
        return pine.get({"resource": self.RESOURCE, "options": options})

    def get_all_by_organization(
        self, handle_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[OrganizationInviteType]:
        """
        Get all invites by organization.

        Args:
            handle_or_id (Union[str, int]): organization handle (string), or id (number).
            options (AnyObject): extra pine options to use.

        Returns:
            List[OrganizationInviteType]: list contains info of invites.

        Examples:
            >>> balena.models.organization.invite.get_all_by_organization(26474)
        """
        org_id = organization.get(handle_or_id, {"$select": "id"})["id"]
        return self.get_all(
            merge({"$filter": {"is_invited_to__organization": org_id}}, options)
        )

    def create(
        self,
        handle_or_id: Union[str, int],
        invitee: str,
        role_name: Optional[str] = None,
        message: Optional[str] = None,
    ) -> OrganizationInviteType:
        """
        Creates a new invite for an organization.

        Args:
            handle_or_id (Union[str, int]): organization handle (string), or id (number).
            invitee (str): the email/balena_username of the invitee.
            role_name (Optional[str]): the role name to be granted to the invitee.
            message (Optional[str]): the message to send along with the invite.

        Returns:
            OrganizationInviteType: organization invite.

        Examples:
            >>> balena.models.organization.invite.create(26474, 'invitee@example.org', 'member', 'Test invite')
        """

        org_id = organization.get(handle_or_id, {"$select": "id"})["id"]
        roles = None
        if role_name is not None:
            roles = pine.get(
                {
                    "resource": "organization_membership_role",
                    "options": {
                        "$top": 1,
                        "$select": ["id"],
                        "$filter": {"name": role_name},
                    },
                }
            )
        body = {
            "invitee": invitee,
            "is_invited_to__organization": org_id,
            "message": message,
        }
        if roles is not None:
            if len(roles) == 0 and role_name is not None:
                raise exceptions.BalenaOrganizationMembershipRoleNotFound(
                    role_name
                )
            body["organization_membership_role"] = roles[0].get("id")

        return pine.post({"resource": self.RESOURCE, "body": body})

    def revoke(self, invite_id: int) -> None:
        """
        Revoke an invite.

        Args:
            invite_id (int): organization invite id.

        Examples:
            >>> balena.models.organization.invite.revoke(2862)
        """

        pine.delete({"resource": self.RESOURCE, "id": invite_id})

    def accept(self, invite_token: str) -> None:
        """
        Accepts an invite.

        Args:
            invite_token (str): invitation Token - invite token.

        """
        request(method="POST", path=f"/org/v1/invitation/{invite_token}")


class OrganizationMembership:
    """
    This class implements organization membership model for balena python SDK.

    """

    def __init__(self):
        self.base_request = BaseRequest()
        self.settings = Settings()
        self.config = Config()
        self.auth = Auth()
        self.tag = OrganizationMembershipTag()
        self.RESOURCE = "organization_membership"

    def get_all(
        self, options: AnyObject = {}
    ) -> List[OrganizationMembershipType]:
        """
        Get all organization memberships.

        Args:
            options (AnyObject): extra pine options to use

        Returns:
            List[OrganizationMembershipType]: organization memberships.

        Examples:
            >>> balena.models.organization.membership.get_all()
        """

        return pine.get({"resource": self.RESOURCE, "options": options})

    def get_all_by_organization(
        self, handle_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[OrganizationMembershipType]:
        """
        Get all memberships by organization.

        Args:
            handle_or_id (Union[str, int]): organization handle (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            List[OrganizationMembershipType]: organization memberships.

        Examples:
            >>> balena.models.organization.membership.get_all_by_organization(3014)
        """

        org_id = organization.get(handle_or_id, {"$select": "id"})
        org_filter = {"$filter": {"is_member_of__organization": org_id}}
        return self.get_all(merge(org_filter, options))

    def get(self, membership_id: ResourceKey, options: AnyObject = {}):
        """
        Get a single organization membership.

        Args:
            membership_id (ResourceKey): the id (int) or an object with the unique
            `user` & `is_member_of__organization` numeric pair of the membership

        Returns:
            Organization membership.

        Examples:
            >>> balena.models.organization.membership.get(17608)
        """
        result = pine.get(
            {
                "resource": self.RESOURCE,
                "id": membership_id,  # type: ignore
                "options": options,
            }
        )

        if result is None:
            raise exceptions.OrganizationMembershipNotFound(membership_id)
        return result


class OrganizationMembershipTag(DependentResource[OrganizationMembershipTagType]):
    """
    This class implements organization membership tag model for balena python SDK.

    """

    def __init__(self):
        super(OrganizationMembershipTag, self).__init__(
            "organization_membership_tag",
            "tag_key",
            "organization_membership",
            lambda id: organization.get(id)["id"]
        )

    def get_all_by_organization(
        self, handle_or_id: Union[str, int], options: AnyObject = {}
    ) -> List[OrganizationMembershipTagType]:
        """
        Get all organization membership tags for an organization.

        Args:
            handle_or_id (Union[str, int]): organization handle (string) or id (number).
            options (AnyObject): extra pine options to use

        Returns:
            List[OrganizationMembershipTagType]: organization membership tags.

        Examples:
            >>> balena.models.organization.membership.tag.get_all_by_organization(3014)
        """
        org_id = organization.get(handle_or_id, {"$select": "id"})["id"]
        return super(OrganizationMembershipTag, self).get_all(
            merge(
                {
                    "$filter": {
                        "organization_membership": {
                            "$any": {
                                "$alias": "om",
                                "$expr": {
                                    "om": {"is_member_of__organization": org_id}
                                },
                            }
                        }
                    }
                },
                options,
            )
        )

    def get_all_by_organization_membership(
        self, membership_id: int, options: AnyObject = {}
    ) -> List[OrganizationMembershipTagType]:
        """
        Get all organization membership tags for a memberships of an organization.

        Args:
            membership_id (int): organization membership id.
            options (AnyObject): extra pine options to use

        Returns:
            list: organization membership tags.

        Examples:
            >>> balena.models.organization.membership.tag.get_all_by_organization_membership(17608)
        """

        return super(OrganizationMembershipTag, self).get_all_by_parent(
            membership_id, options
        )

    def get_all(self, options: AnyObject = {}):
        """
        Get all organization membership tags.

        Args:
            options (AnyObject): extra pine options to use


        Examples:
            >>> balena.models.organization.membership.tag.get_all()
        """

        return super(OrganizationMembershipTag, self).get_all(options)

    def get(self, membership_id: int, tag_key: str):
        """
        Get an organization membership tag.

        Args:
            membership_id: organization membership id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.organization.membership.tag.get(17608, 'mTag1')
        """

        return super(OrganizationMembershipTag, self).get(
            membership_id, tag_key
        )

    def set(self, membership_id: int, tag_key: str, value: str):
        """
        Set an organization membership tag.

        Args:
            membership_id: organization membership id.
            tag_key (str): tag key.
            value (str): tag value.

        Examples:
            >>> balena.models.organization.membership.tag.set(17608, 'mTag1', 'Python SDK')
        """

        return super(OrganizationMembershipTag, self).set(
            membership_id, tag_key, value
        )

    def remove(self, membership_id: int, tag_key: str):
        """
        Remove an organization membership tag.

        Args:
            membership_id: organization membership id.
            tag_key (str): tag key.

        Examples:
            >>> balena.models.organization.membership.tag.remove(17608, 'mTag1')
        """

        return super(OrganizationMembershipTag, self).remove(
            membership_id, tag_key
        )


organization = Organization()
