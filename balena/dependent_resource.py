from typing import Any, Callable, Optional, TypeVar, Generic, List
from .pine import pine
from .types import AnyObject
from .utils import merge, is_id


T = TypeVar('T')


class DependentResource(Generic[T]):
    def __init__(
            self,
            resource_name: str,
            resource_key_field: str,
            parent_resource_name: str,
            get_resource_id: Callable[[Any], int]
    ):
        self.resource_name = resource_name
        self.resource_key_field = resource_key_field
        self.parent_resource_name = parent_resource_name
        self.get_resource_id = get_resource_id

    def _get_all(self, options: AnyObject = {}) -> List[T]:
        default_orderby = {"$orderby": {}}
        default_orderby["$orderby"][self.resource_key_field] = "asc"

        return pine.get(
            {
                "resource": self.resource_name,
                "options": merge(default_orderby, options),
            }
        )

    def _get_all_by_parent(
        self, parent_param: Any, options: AnyObject = {}
    ) -> List[T]:
        parent_id = parent_param if is_id(parent_param) else self.get_resource_id(parent_param)

        get_options = {
            "$filter": {},
            "$orderby": f"{self.resource_key_field} asc",
        }
        get_options["$filter"][self.parent_resource_name] = parent_id

        return self._get_all(merge(get_options, options))

    def _get(self, parent_param: Any, key: str) -> Optional[str]:
        parent_id = parent_param if is_id(parent_param) else self.get_resource_id(parent_param)

        dollar_filter = {}
        dollar_filter[self.parent_resource_name] = parent_id
        dollar_filter[self.resource_key_field] = key

        result = pine.get(
            {
                "resource": self.resource_name,
                "options": {"$select": "value", "$filter": dollar_filter},
            }
        )

        if len(result) == 1:
            return result[0].get("value")

    def _set(self, parent_param: Any, tag_key: str, value: str) -> None:
        parent_id = parent_param if is_id(parent_param) else self.get_resource_id(parent_param)

        upsert_id = {}
        upsert_id[self.parent_resource_name] = parent_id
        upsert_id[self.resource_key_field] = tag_key

        pine.upsert(
            {
                "resource": self.resource_name,
                "id": upsert_id,
                "body": {"value": value},
            }
        )

    def _remove(self, parent_param: Any, tag_key: str) -> None:
        parent_id = parent_param if is_id(parent_param) else self.get_resource_id(parent_param)

        dollar_filter = {}
        dollar_filter[self.parent_resource_name] = parent_id
        dollar_filter[self.resource_key_field] = tag_key

        pine.delete(
            {"resource": self.resource_name, "options": {"$filter": dollar_filter}}
        )
