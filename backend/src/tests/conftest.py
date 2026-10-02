import pytest

@pytest.fixture(scope="session")
def api_client():
    from adapters.controllers.booking_controller import router
    # Placeholder para TestClient real
    return router

@pytest.fixture(scope="function")
def fake_repo():
    class FakeRepo:
        pass
    return FakeRepo()