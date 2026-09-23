import os

import requests
import streamlit as st


API_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")


class ApiError(Exception):
    pass


def request(method: str, path: str, *, params: dict | None = None, json_body: dict | None = None) -> object:
    headers = {}
    token = st.session_state.get("access_token")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            params=params,
            json=json_body,
            headers=headers,
            timeout=12,
        )
    except requests.RequestException as exc:
        raise ApiError(
            "Не удаётся подключиться к backend. Запустите приложение командой `docker compose up --build`."
        ) from exc

    if response.ok:
        if response.status_code == 204 or not response.content:
            return None
        return response.json()

    try:
        detail = response.json().get("detail", "")
        if isinstance(detail, list):
            detail = "; ".join(item.get("msg", str(item)) for item in detail)
    except (ValueError, AttributeError):
        detail = ""
    raise ApiError(detail or f"Запрос завершился с кодом {response.status_code}.")
