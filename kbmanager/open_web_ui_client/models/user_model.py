from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.user_model_info_type_0 import UserModelInfoType0
    from ..models.user_settings import UserSettings


T = TypeVar("T", bound="UserModel")


@_attrs_define
class UserModel:
    """
    Attributes:
        id (str):
        name (str):
        email (str):
        profile_image_url (str):
        last_active_at (int):
        updated_at (int):
        created_at (int):
        role (Union[Unset, str]):  Default: 'pending'.
        api_key (Union[None, Unset, str]):
        settings (Union['UserSettings', None, Unset]):
        info (Union['UserModelInfoType0', None, Unset]):
        oauth_sub (Union[None, Unset, str]):
    """

    id: str
    name: str
    email: str
    profile_image_url: str
    last_active_at: int
    updated_at: int
    created_at: int
    role: Union[Unset, str] = "pending"
    api_key: Union[None, Unset, str] = UNSET
    settings: Union["UserSettings", None, Unset] = UNSET
    info: Union["UserModelInfoType0", None, Unset] = UNSET
    oauth_sub: Union[None, Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        from ..models.user_model_info_type_0 import UserModelInfoType0
        from ..models.user_settings import UserSettings

        id = self.id

        name = self.name

        email = self.email

        profile_image_url = self.profile_image_url

        last_active_at = self.last_active_at

        updated_at = self.updated_at

        created_at = self.created_at

        role = self.role

        api_key: Union[None, Unset, str]
        if isinstance(self.api_key, Unset):
            api_key = UNSET
        else:
            api_key = self.api_key

        settings: Union[None, Unset, dict[str, Any]]
        if isinstance(self.settings, Unset):
            settings = UNSET
        elif isinstance(self.settings, UserSettings):
            settings = self.settings.to_dict()
        else:
            settings = self.settings

        info: Union[None, Unset, dict[str, Any]]
        if isinstance(self.info, Unset):
            info = UNSET
        elif isinstance(self.info, UserModelInfoType0):
            info = self.info.to_dict()
        else:
            info = self.info

        oauth_sub: Union[None, Unset, str]
        if isinstance(self.oauth_sub, Unset):
            oauth_sub = UNSET
        else:
            oauth_sub = self.oauth_sub

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "email": email,
                "profile_image_url": profile_image_url,
                "last_active_at": last_active_at,
                "updated_at": updated_at,
                "created_at": created_at,
            }
        )
        if role is not UNSET:
            field_dict["role"] = role
        if api_key is not UNSET:
            field_dict["api_key"] = api_key
        if settings is not UNSET:
            field_dict["settings"] = settings
        if info is not UNSET:
            field_dict["info"] = info
        if oauth_sub is not UNSET:
            field_dict["oauth_sub"] = oauth_sub

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.user_model_info_type_0 import UserModelInfoType0
        from ..models.user_settings import UserSettings

        d = dict(src_dict)
        id = d.pop("id")

        name = d.pop("name")

        email = d.pop("email")

        profile_image_url = d.pop("profile_image_url")

        last_active_at = d.pop("last_active_at")

        updated_at = d.pop("updated_at")

        created_at = d.pop("created_at")

        role = d.pop("role", UNSET)

        def _parse_api_key(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        api_key = _parse_api_key(d.pop("api_key", UNSET))

        def _parse_settings(data: object) -> Union["UserSettings", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                settings_type_0 = UserSettings.from_dict(data)

                return settings_type_0
            except:  # noqa: E722
                pass
            return cast(Union["UserSettings", None, Unset], data)

        settings = _parse_settings(d.pop("settings", UNSET))

        def _parse_info(data: object) -> Union["UserModelInfoType0", None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                info_type_0 = UserModelInfoType0.from_dict(data)

                return info_type_0
            except:  # noqa: E722
                pass
            return cast(Union["UserModelInfoType0", None, Unset], data)

        info = _parse_info(d.pop("info", UNSET))

        def _parse_oauth_sub(data: object) -> Union[None, Unset, str]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[None, Unset, str], data)

        oauth_sub = _parse_oauth_sub(d.pop("oauth_sub", UNSET))

        user_model = cls(
            id=id,
            name=name,
            email=email,
            profile_image_url=profile_image_url,
            last_active_at=last_active_at,
            updated_at=updated_at,
            created_at=created_at,
            role=role,
            api_key=api_key,
            settings=settings,
            info=info,
            oauth_sub=oauth_sub,
        )

        user_model.additional_properties = d
        return user_model

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
