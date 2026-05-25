from fastapi.testclient import TestClient


def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_department(client: TestClient):
    response = client.post(
        "/departments/",
        json={"name": "IT Dept", "parent_id": None}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "IT Dept"
    assert data["parent_id"] is None


def test_create_duplicate_name(client: TestClient):
    parent = client.post("/departments/", json={"name": "Root", "parent_id": None})
    parent_id = parent.json()["id"]
    
    client.post("/departments/", json={"name": "Child", "parent_id": parent_id})
    
    response = client.post(
        "/departments/",
        json={"name": "Child", "parent_id": parent_id}
    )
    assert response.status_code == 409  # ✅ Проверяем статус, не ловим исключение
    assert "already exists" in response.json()["detail"].lower()


def test_create_employee_validation(client: TestClient):
    dept = client.post("/departments/", json={"name": "HR", "parent_id": None})
    dept_id = dept.json()["id"]
    
    response = client.post(
        f"/departments/{dept_id}/employees",  # ✅ Без слеша
        json={"full_name": "   ", "position": "Manager"}
    )
    assert response.status_code == 422
    
    response = client.post(
        "/departments/99999/employees",
        json={"full_name": "Ivan", "position": "Manager"}
    )
    assert response.status_code == 404  # ✅ Проверяем статус


def test_tree_depth(client: TestClient):
    root = client.post("/departments/", json={"name": "Root", "parent_id": None})
    root_id = root.json()["id"]
    
    level1 = client.post("/departments/", json={"name": "L1", "parent_id": root_id})
    level1_id = level1.json()["id"]
    
    client.post("/departments/", json={"name": "L2", "parent_id": level1_id})
    
    response = client.get(f"/departments/{root_id}?depth=1")
    data = response.json()
    assert len(data["children"]) == 1
    assert data["children"][0]["department"]["name"] == "L1"
    
    response = client.get(f"/departments/{root_id}?depth=2")
    data = response.json()
    assert len(data["children"][0]["children"]) == 1


def test_cycle_prevention(client: TestClient):
    a = client.post("/departments/", json={"name": "A", "parent_id": None})
    a_id = a.json()["id"]
    
    b = client.post("/departments/", json={"name": "B", "parent_id": a_id})
    b_id = b.json()["id"]
    
    response = client.patch(f"/departments/{a_id}", json={"parent_id": b_id})
    assert response.status_code == 409  # ✅ Проверяем статус
    assert "circular" in response.json()["detail"].lower()


def test_delete_reassign(client: TestClient):
    dept_src = client.post("/departments/", json={"name": "Src", "parent_id": None})
    dept_dst = client.post("/departments/", json={"name": "Dst", "parent_id": None})
    
    src_id = dept_src.json()["id"]
    dst_id = dept_dst.json()["id"]
    
    emp = client.post(
        f"/departments/{src_id}/employees",
        json={"full_name": "Worker", "position": "Role"}
    )
    emp_id = emp.json()["id"]
    
    tree = client.get(f"/departments/{src_id}")
    assert len(tree.json()["employees"]) == 1
    
    response = client.delete(
        f"/departments/{src_id}",
        params={"mode": "reassign", "reassign_to_department_id": dst_id}
    )
    assert response.status_code == 204
    
    tree_dst = client.get(f"/departments/{dst_id}")
    employees = tree_dst.json()["employees"]
    assert len(employees) == 1
    assert employees[0]["id"] == emp_id


def test_delete_cascade(client: TestClient):
    parent = client.post("/departments/", json={"name": "Parent", "parent_id": None})
    parent_id = parent.json()["id"]
    
    child = client.post("/departments/", json={"name": "Child", "parent_id": parent_id})
    child_id = child.json()["id"]
    
    response = client.delete(f"/departments/{parent_id}?mode=cascade")
    assert response.status_code == 204
    
    response = client.get(f"/departments/{child_id}")
    assert response.status_code == 404