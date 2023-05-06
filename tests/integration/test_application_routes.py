from typing import Dict

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.main import app

base_url = "http://127.0.0.1:8000"


@pytest.fixture(scope='session')
def client():
    with TestClient(app, base_url=base_url) as client:
        yield client


@pytest.fixture
def user_token() -> Dict[str, str]:
    return {"access_token": "your_access_token"}


def test_submit_loan_application(
        user_token: Dict[str, str],
        client: TestClient) -> None:
    # Given
    asking = 1000

    # When
    response = client.post(
        f"{base_url}/loan/application?asking={asking}",
        headers=user_token
    )

    # Then
    assert response.status_code == 200
    assert response.json()["success"] == True


def test_get_all_loan_applications(
        user_token: Dict[str, str],
        client: TestClient) -> None:
    # Given
    recent = False

    # When
    response = client.get(
        f"{base_url}/loan/application?recent={recent}",
        headers=user_token
    )

    # Then
    assert response.status_code == 200