from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import httpx

from autotransition.library.schema import LibraryItem
from autotransition.library.schema import LibraryFile

DEFAULT_PUBLIC_LIBRARY_SITE_URL = "https://facelessdancer.com"


@dataclass
class LibraryPublishSettings:
    site_url: str = DEFAULT_PUBLIC_LIBRARY_SITE_URL
    access_token: str = ""
    refresh_token: str = ""
    public_key: str = ""
    authenticated: bool = False
    is_holder: bool = False
    is_admin: bool = False
    creator_profile: dict[str, Any] = field(default_factory=dict)

    @property
    def configured(self) -> bool:
        return bool(self.site_url.strip())

    @property
    def has_session(self) -> bool:
        return bool(self.site_url.strip() and self.access_token.strip() and self.authenticated)

    def cleared_session(self) -> "LibraryPublishSettings":
        return LibraryPublishSettings(site_url=_normalize_site_url(self.site_url))


class LibraryPublishError(RuntimeError):
    pass


def is_expired_session_error(message: str) -> bool:
    text = message.lower()
    return "refresh token revoked or expired" in text or "missing refresh token" in text or "invalid refresh token" in text


def request_wallet_nonce(settings: LibraryPublishSettings, public_key: str, timeout_seconds: float = 60.0) -> dict[str, Any]:
    if not settings.site_url.strip():
        raise LibraryPublishError("Public library site URL is not configured.")
    payload = {"publicKey": public_key.strip()}
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            return _checked_json(client.post(f"{settings.site_url.rstrip('/')}/api/auth/nonce", json=payload), "request auth nonce")
    except httpx.HTTPError as exc:
        raise LibraryPublishError(f"Could not request auth nonce: {exc}") from exc


def authenticate_wallet_signature(
    settings: LibraryPublishSettings,
    *,
    public_key: str,
    nonce: str,
    message: str,
    signature_bytes: bytes,
    timeout_seconds: float = 60.0,
) -> LibraryPublishSettings:
    if not settings.site_url.strip():
        raise LibraryPublishError("Public library site URL is not configured.")
    payload = {
        "publicKey": public_key.strip(),
        "nonce": nonce,
        "message": message,
        "signature": _base58_encode(signature_bytes),
    }
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(f"{settings.site_url.rstrip('/')}/api/auth/verify", json=payload)
            body = _checked_json(response, "verify wallet signature")
            access_token = _response_cookie(response, client, "accessToken")
            refresh_token = _response_cookie(response, client, "refreshToken")
            if not access_token or not refresh_token:
                raise LibraryPublishError("Site authentication succeeded but did not return session cookies.")
    except httpx.HTTPError as exc:
        raise LibraryPublishError(f"Could not verify wallet signature: {exc}") from exc
    return _settings_with_auth(settings, body, access_token=access_token, refresh_token=refresh_token)


def refresh_site_session(settings: LibraryPublishSettings, timeout_seconds: float = 60.0) -> LibraryPublishSettings:
    if not settings.site_url.strip():
        raise LibraryPublishError("Public library site URL is not configured.")
    if not settings.refresh_token.strip():
        raise LibraryPublishError("No site refresh token is available. Connect your wallet again.")
    try:
        with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
            response = client.post(
                f"{settings.site_url.rstrip('/')}/api/auth/refresh",
                headers={"Cookie": _cookie_header(settings)},
            )
            body = _checked_json(response, "refresh site session")
            access_token = _response_cookie(response, client, "accessToken") or settings.access_token
            refresh_token = _response_cookie(response, client, "refreshToken") or settings.refresh_token
    except httpx.HTTPError as exc:
        raise LibraryPublishError(f"Could not refresh site session: {exc}") from exc
    return _settings_with_auth(settings, body, access_token=access_token, refresh_token=refresh_token)


def logout_site_session(settings: LibraryPublishSettings, timeout_seconds: float = 30.0) -> LibraryPublishSettings:
    if settings.site_url.strip() and (settings.access_token.strip() or settings.refresh_token.strip()):
        try:
            with httpx.Client(timeout=timeout_seconds, follow_redirects=True) as client:
                client.post(
                    f"{settings.site_url.rstrip('/')}/api/auth/logout",
                    headers={"Cookie": _cookie_header(settings)},
                )
        except Exception:
            pass
    return settings.cleared_session()


class LibraryPublisher:
    def __init__(self, settings: LibraryPublishSettings, timeout_seconds: float = 120.0) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds

    def publish(self, item: LibraryItem, *, publish_public: bool = True) -> dict[str, Any]:
        if not self.settings.has_session:
            raise LibraryPublishError("Public library wallet auth is not connected.")

        api_base = self.settings.site_url.rstrip("/") + "/api/library"
        payload = _item_payload(item, publish_public=publish_public)

        with httpx.Client(timeout=self.timeout_seconds) as client:
            item_response = self._request_json(client, "POST", f"{api_base}/publish/items", json=payload, action="create public library item")
            remote_item = item_response.get("item") or {}
            remote_item_id = str(remote_item.get("id") or "")
            if not remote_item_id:
                raise LibraryPublishError("Site did not return a remote library item id.")

            self._request_json(client, "DELETE", f"{api_base}/publish/items/{remote_item_id}/files", action="replace public library files")

            uploaded_files: list[dict[str, Any]] = []
            for file_record in item.files:
                file_path = Path(file_record.path).expanduser()
                if not file_path.exists() or not file_path.is_file():
                    raise LibraryPublishError(f"File not found: {file_path}")
                with file_path.open("rb") as handle:
                    upload_response = self._request_json(
                        client,
                        "POST",
                        f"{api_base}/publish/items/{remote_item_id}/files",
                        data={
                            "role": file_record.role,
                            "metadata": json.dumps(file_record.metadata),
                        },
                        files={
                            "file": (
                                file_path.name,
                                handle,
                                file_record.mime_type or "application/octet-stream",
                            )
                        },
                        action=f"upload {file_path.name}",
                    )
                remote_item = upload_response.get("item") or remote_item
                uploaded_files = list(remote_item.get("files") or uploaded_files)

            if publish_public:
                published_response = self._request_json(
                    client,
                    "POST",
                    f"{api_base}/publish/items/{remote_item_id}/publish",
                    action="publish public library item",
                )
                remote_item = published_response.get("item") or remote_item
                uploaded_files = list(remote_item.get("files") or uploaded_files)

        return {
            "remote_item_id": remote_item_id,
            "remote_status": remote_item.get("status") or "draft",
            "remote_visibility": remote_item.get("visibility") or "private",
            "file_count": len(uploaded_files),
            "public_url": f"{self.settings.site_url.rstrip('/')}/library",
            "remote_item": remote_item,
        }

    def revoke(self, item: LibraryItem) -> dict[str, Any]:
        if not self.settings.has_session:
            raise LibraryPublishError("Public library wallet auth is not connected.")

        publish_metadata = dict(item.metadata.get("public_library") or {})
        remote_item_id = str(publish_metadata.get("remote_item_id") or "")
        if not remote_item_id:
            raise LibraryPublishError("This library item has not been published yet.")

        api_base = self.settings.site_url.rstrip("/") + "/api/library"
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = self._request_json(
                client,
                "POST",
                f"{api_base}/publish/items/{remote_item_id}/revoke",
                action="revoke public library item",
            )
        remote_item = response.get("item") or {}
        return {
            "remote_item_id": remote_item_id,
            "remote_status": remote_item.get("status") or "archived",
            "remote_visibility": remote_item.get("visibility") or "private",
            "file_count": len(list(remote_item.get("files") or [])),
            "public_url": f"{self.settings.site_url.rstrip('/')}/library",
            "remote_item": remote_item,
        }

    def _request_json(
        self,
        client: httpx.Client,
        method: str,
        url: str,
        *,
        action: str,
        retry_on_auth: bool = True,
        **kwargs: Any,
    ) -> dict[str, Any]:
        headers = dict(kwargs.pop("headers", {}))
        headers["Authorization"] = f"Bearer {self.settings.access_token.strip()}"
        response = client.request(method, url, headers=headers, **kwargs)
        if response.status_code == 401 and retry_on_auth and self.settings.refresh_token.strip():
            self.settings = refresh_site_session(self.settings, timeout_seconds=self.timeout_seconds)
            return self._request_json(client, method, url, action=action, retry_on_auth=False, **kwargs)
        return _checked_json(response, action)


class PublicLibraryClient:
    def __init__(self, settings: LibraryPublishSettings, timeout_seconds: float = 120.0) -> None:
        self.settings = settings
        self.timeout_seconds = timeout_seconds

    def list_items(self, *, kind: str | None = None, limit: int = 80) -> list[dict[str, Any]]:
        if not self.settings.site_url.strip():
            raise LibraryPublishError("Public library site URL is not configured.")
        params: dict[str, Any] = {"limit": limit}
        if kind and kind != "all":
            params["kind"] = kind
        with httpx.Client(timeout=self.timeout_seconds) as client:
            response = _checked_json(
                client.get(f"{self.settings.site_url.rstrip('/')}/api/library", params=params),
                "load public library",
            )
        return list(response.get("items") or [])

    def import_item(self, item_id: str, *, root: Path = Path("data/library/imports")) -> LibraryItem:
        if not self.settings.site_url.strip():
            raise LibraryPublishError("Public library site URL is not configured.")
        api_base = self.settings.site_url.rstrip("/")
        with httpx.Client(timeout=self.timeout_seconds, follow_redirects=True) as client:
            response = _checked_json(client.get(f"{api_base}/api/library/{item_id}"), "load public library item")
            remote = response.get("item") or {}
            files = list(remote.get("files") or [])
            if not files:
                raise LibraryPublishError("Public library item has no downloadable files.")

            local_item_id = f"imported-{item_id}"
            import_dir = root / _safe_path_part(local_item_id)
            import_dir.mkdir(parents=True, exist_ok=True)
            local_files: list[LibraryFile] = []
            for remote_file in files:
                public_url = str(remote_file.get("publicUrl") or "")
                if not public_url:
                    continue
                file_id = str(remote_file.get("id") or "file")
                original_name = str((remote_file.get("metadata") or {}).get("originalName") or Path(public_url).name or file_id)
                local_path = import_dir / f"{_safe_path_part(file_id)}-{_safe_path_part(original_name)}"
                download = client.get(public_url)
                if not download.is_success:
                    raise LibraryPublishError(f"Could not download {public_url}: HTTP {download.status_code}")
                local_path.write_bytes(download.content)
                local_files.append(
                    LibraryFile(
                        id=f"import-{file_id}",
                        role=remote_file.get("role") or "audio",
                        mime_type=remote_file.get("mimeType") or "application/octet-stream",
                        size_bytes=local_path.stat().st_size,
                        storage_provider="local",
                        path=str(local_path),
                        public_url=public_url,
                        sha256=remote_file.get("sha256") or None,
                        metadata={
                            **(remote_file.get("metadata") or {}),
                            "remote_file_id": file_id,
                            "remote_public_url": public_url,
                        },
                    )
                )

        creator = remote.get("creator") or {}
        return LibraryItem(
            id=f"imported-{item_id}",
            owner_id=remote.get("ownerId") or None,
            visibility="local",
            status="draft",
            kind=remote.get("kind") or "audio",
            title=remote.get("title") or item_id,
            description=remote.get("description") or None,
            tags=list(remote.get("tags") or []),
            files=local_files,
            metadata={
                **(remote.get("metadata") or {}),
                "imported": True,
                "category": remote.get("kind") or "audio",
                "public_library": {
                    "remote_item_id": item_id,
                    "remote_status": remote.get("status") or "",
                    "remote_visibility": remote.get("visibility") or "",
                    "public_url": f"{api_base}/library",
                },
                "creator": {
                    "display_name": creator.get("displayName") or "",
                    "creator_slug": creator.get("creatorSlug") or "",
                    "avatar_url": creator.get("avatarUrl") or "",
                    "banner_url": creator.get("bannerUrl") or "",
                },
            },
            source_lineage={
                **(remote.get("sourceLineage") or {}),
                "remote_item_id": item_id,
                "imported_from": api_base,
            },
            license=remote.get("license") or None,
            attribution=remote.get("attribution") or None,
            created_at=remote.get("createdAt") or "",
            updated_at=remote.get("updatedAt") or "",
        )


def load_publish_settings(path: Path = Path("data/library/publish-connection.json")) -> LibraryPublishSettings:
    if not path.exists():
        return LibraryPublishSettings()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return LibraryPublishSettings()
    return LibraryPublishSettings(
        site_url=_normalize_site_url(str(data.get("site_url") or DEFAULT_PUBLIC_LIBRARY_SITE_URL)),
        access_token=str(data.get("access_token") or ""),
        refresh_token=str(data.get("refresh_token") or ""),
        public_key=str(data.get("public_key") or ""),
        authenticated=bool(data.get("authenticated")),
        is_holder=bool(data.get("is_holder")),
        is_admin=bool(data.get("is_admin")),
        creator_profile=dict(data.get("creator_profile") or {}),
    )


def save_publish_settings(settings: LibraryPublishSettings, path: Path = Path("data/library/publish-connection.json")) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "site_url": _normalize_site_url(settings.site_url),
                "access_token": settings.access_token,
                "refresh_token": settings.refresh_token,
                "public_key": settings.public_key,
                "authenticated": settings.authenticated,
                "is_holder": settings.is_holder,
                "is_admin": settings.is_admin,
                "creator_profile": settings.creator_profile,
            },
            indent=2,
        ),
        encoding="utf-8",
    )


def public_settings_response(settings: LibraryPublishSettings) -> dict[str, Any]:
    return {
        "site_url": _normalize_site_url(settings.site_url),
        "authenticated": settings.authenticated,
        "public_key": settings.public_key,
        "is_holder": settings.is_holder,
        "is_admin": settings.is_admin,
        "creator_profile": settings.creator_profile,
        "configured": settings.configured,
    }


def _item_payload(item: LibraryItem, *, publish_public: bool) -> dict[str, Any]:
    metadata = dict(item.metadata)
    metadata.pop("public_library", None)
    payload: dict[str, Any] = {
        "localId": item.id,
        "visibility": "public" if publish_public else "private",
        "kind": item.kind,
        "title": item.title,
        "tags": item.tags,
        "metadata": metadata,
        "sourceLineage": {**item.source_lineage, "localId": item.id},
    }
    if item.description:
        payload["description"] = item.description
    if item.license:
        payload["license"] = item.license
    if item.attribution:
        payload["attribution"] = item.attribution
    return payload


def _checked_json(response: httpx.Response, action: str) -> dict[str, Any]:
    if response.is_success:
        return response.json()
    try:
        body = response.json()
    except Exception:
        body = {"error": response.text}
    message = body.get("error") or body.get("detail") or response.text
    raise LibraryPublishError(f"Could not {action}: {message}")


def _safe_path_part(value: str) -> str:
    clean = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in value).strip("._")
    return (clean or "file")[:140]


def _settings_with_auth(
    settings: LibraryPublishSettings,
    body: dict[str, Any],
    *,
    access_token: str,
    refresh_token: str,
) -> LibraryPublishSettings:
    creator_profile = dict(body.get("creatorProfile") or {})
    return LibraryPublishSettings(
        site_url=_normalize_site_url(settings.site_url),
        access_token=access_token,
        refresh_token=refresh_token,
        public_key=str(body.get("publicKey") or settings.public_key),
        authenticated=bool(body.get("authenticated", True)),
        is_holder=bool(body.get("isHolder")),
        is_admin=bool(body.get("isAdmin")),
        creator_profile=creator_profile,
    )


def _cookie_header(settings: LibraryPublishSettings) -> str:
    parts: list[str] = []
    if settings.access_token.strip():
        parts.append(f"accessToken={settings.access_token.strip()}")
    if settings.refresh_token.strip():
        parts.append(f"refreshToken={settings.refresh_token.strip()}")
    return "; ".join(parts)


def _response_cookie(response: httpx.Response, client: httpx.Client, name: str) -> str:
    try:
        value = response.cookies.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    try:
        value = client.cookies.get(name)
        if value:
            return str(value)
    except Exception:
        pass
    return ""


def _base58_encode(data: bytes) -> str:
    if not data:
        return ""
    alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
    number = int.from_bytes(data, "big")
    encoded = ""
    while number > 0:
        number, remainder = divmod(number, 58)
        encoded = alphabet[remainder] + encoded
    zero_prefix = 0
    for byte in data:
        if byte == 0:
            zero_prefix += 1
        else:
            break
    if not encoded:
        return "1" * zero_prefix
    return ("1" * zero_prefix) + encoded


def _normalize_site_url(value: str) -> str:
    site_url = (value or "").strip().rstrip("/")
    if not site_url:
        return DEFAULT_PUBLIC_LIBRARY_SITE_URL
    lowered = site_url.lower()
    if "localhost" in lowered or "127.0.0.1" in lowered:
        return DEFAULT_PUBLIC_LIBRARY_SITE_URL
    return site_url
