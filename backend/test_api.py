"""Integration tests against PostgreSQL; each test rolls its data back."""
import unittest
from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.orm import Session

from .auth import password_hash, token_digest
from .database import engine, get_db
from .main import app
from .models import User, Role, LoginSession


class ApiTests(unittest.TestCase):
    def setUp(self):
        self.connection = engine.connect()
        self.transaction = self.connection.begin()
        self.db = Session(bind=self.connection, join_transaction_mode="create_savepoint")
        def override_db():
            yield self.db
        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        app.dependency_overrides.clear()
        self.db.close()
        self.transaction.rollback()
        self.connection.close()

    def account(self, role, email):
        response = self.client.post("/auth/register", json={
            "email": email, "name": "Test User", "password": "test-password-123", "role": role})
        self.assertEqual(response.status_code, 201, response.text)
        self.assertNotIn("password_hash", response.json())
        login = self.client.post("/auth/login", data={"username": email, "password": "test-password-123"})
        self.assertEqual(login.status_code, 200, login.text)
        return response.json(), {"Authorization": "Bearer " + login.json()["access_token"]}

    def test_roles_tasks_and_proposals(self):
        student, student_headers = self.account("student", "student@example.com")
        business, business_headers = self.account("business", "business@example.com")
        _, other_headers = self.account("business", "other@example.com")
        payload = dict(title="Задача", company="Компания", industry="IT", summary="Описание",
                       users="Студенты", data="CSV", deadline="2 недели", tags=["python"])
        self.assertEqual(self.client.post("/tasks", json=payload).status_code, 401)
        self.assertEqual(self.client.post("/tasks", json=payload, headers=student_headers).status_code, 403)
        self.assertEqual(self.client.post("/tasks", json={**payload, "score": 100}, headers=business_headers).status_code, 422)
        created = self.client.post("/tasks", json=payload, headers=business_headers)
        self.assertEqual(created.status_code, 201, created.text)
        task = created.json()
        self.assertEqual(task["owner_id"], business["id"])
        self.assertEqual(task["score"], 0)
        url = f"/tasks/{task['id']}"
        self.assertEqual(self.client.get(url).status_code, 200)
        proposal = {"team_name": "Команда", "message": "Предложение"}
        self.assertEqual(self.client.post(url + "/proposals", json=proposal, headers=business_headers).status_code, 403)
        result = self.client.post(url + "/proposals", json=proposal, headers=student_headers)
        self.assertEqual(result.status_code, 201, result.text)
        self.assertEqual(result.json()["student_id"], student["id"])
        self.assertEqual(self.client.get(url).json()["proposals"], 1)
        self.assertEqual(self.client.get(url + "/proposals", headers=other_headers).status_code, 403)
        self.assertEqual(len(self.client.get(url + "/proposals", headers=business_headers).json()), 1)
        self.assertTrue(any(t["id"] == task["id"] for t in self.client.get("/tasks").json()))
        self.assertEqual(self.client.get("/tasks/unknown").status_code, 404)

    def test_auth_and_admin(self):
        user, headers = self.account("student", "member@example.com")
        self.assertEqual(self.client.post("/auth/register", json={"email": "admin@example.com",
            "name": "Admin", "password": "test-password-123", "role": "admin"}).status_code, 422)
        self.assertEqual(self.client.post("/auth/register", json={"email": "MEMBER@example.com",
            "name": "Duplicate", "password": "test-password-123"}).status_code, 409)
        self.assertEqual(self.client.post("/auth/login", data={"username": "member@example.com", "password": "wrong"}).status_code, 401)
        self.assertEqual(self.client.get("/admin/users", headers=headers).status_code, 403)
        admin = User(email="admin@example.com", name="Admin", role=Role.admin,
                     password_hash=password_hash.hash("test-password-123"))
        self.db.add(admin)
        self.db.commit()
        login = self.client.post("/auth/login", data={"username": admin.email, "password": "test-password-123"})
        admin_headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        self.assertEqual(self.client.get("/admin/users", headers=admin_headers).status_code, 200)
        change = self.client.patch(f"/admin/users/{user['id']}/role", json={"role": "business"}, headers=admin_headers)
        self.assertEqual(change.status_code, 200)
        self.assertEqual(self.client.get("/auth/me", headers=headers).json()["role"], "business")
        self.assertEqual(self.client.post("/auth/logout", headers=headers).status_code, 204)
        self.assertEqual(self.client.get("/auth/me", headers=headers).status_code, 401)
        session = self.db.get(LoginSession, token_digest(login.json()["access_token"]))
        session.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
        self.db.commit()
        self.assertEqual(self.client.get("/auth/me", headers=admin_headers).status_code, 401)


if __name__ == "__main__":
    unittest.main()
