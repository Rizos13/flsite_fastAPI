import pytest
from main import app
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_register_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/register", data={"username": "testuser", "password": "password123"})
        assert response.status_code == 303

@pytest.mark.asyncio
async def test_login_user():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", data={"username": "testuser", "password": "password123"})
        assert response.status_code == 303

@pytest.mark.asyncio
async def test_login_invalid_credentials():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/login", data={"username": "wronguser", "password": "wrongpassword"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_access_admin_tools_without_permission():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/tools")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_access_manager_tools_without_permission():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/manager/tools")
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_create_post_without_login():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/add_post", data={"name": "Test Post", "post": "This is a test post"})
        assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_post_as_user():
    async with AsyncClient(app=app, base_url="http://test") as client:

        login_response = await client.post("/login", data={"username": "testuser", "password": "password123"})
        cookies = login_response.cookies


        response = await client.post("/user/delete_post/1", cookies=cookies)
        assert response.status_code in [200, 303]

@pytest.mark.asyncio
async def test_access_denied_for_user_to_admin_tools():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/admin/tools")
        assert response.status_code == 403