from typing import Any

import aiohttp

from helpers import datagouv_api_client


class ResourceNotAvailableError(Exception):
    """Raised when a resource is not available via the Tabular API."""


async def _get_session(
    session: aiohttp.ClientSession | None,
) -> tuple[aiohttp.ClientSession, bool]:
    if session is not None:
        return session, False
    new_session = aiohttp.ClientSession()
    return new_session, True


async def fetch_resource_data(
    resource_id: str,
    *,
    page: int = 1,
    page_size: int = 100,
    params: dict[str, Any] | None = None,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any]:
    """
    Fetch data for a resource via the Tabular API.
    """

    sess, owns_session = await _get_session(session)
    try:
        base_url = datagouv_api_client.tabular_api_base_url()
        url = f"{base_url}resources/{resource_id}/data/"
        query_params = {
            "page": max(page, 1),
            "page_size": max(page_size, 1),
        }
        if params:
            query_params.update(params)

        async with sess.get(
            url, params=query_params, timeout=aiohttp.ClientTimeout(total=30)
        ) as resp:
            if resp.status == 404:
                raise ResourceNotAvailableError(
                    f"Resource {resource_id} not available via Tabular API"
                )
            resp.raise_for_status()
            return await resp.json()
    finally:
        if owns_session:
            await sess.close()


async def fetch_resource_profile(
    resource_id: str,
    *,
    session: aiohttp.ClientSession | None = None,
) -> dict[str, Any]:
    """
    Fetch the profile metadata for a resource via the Tabular API.
    """

    sess, owns_session = await _get_session(session)
    try:
        base_url = datagouv_api_client.tabular_api_base_url()
        url = f"{base_url}resources/{resource_id}/profile/"
        async with sess.get(url, timeout=aiohttp.ClientTimeout(total=30)) as resp:
            if resp.status == 404:
                raise ResourceNotAvailableError(
                    f"Resource {resource_id} profile not available via Tabular API"
                )
            resp.raise_for_status()
            return await resp.json()
    finally:
        if owns_session:
            await sess.close()
