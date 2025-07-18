def test_create_user(client):
    response = client.post("/users/", json={
        "strava_id": "12345",
        "google_email": "testuser@example.com",
        "strava_access_token": "access_token_abc",
        "google_access_token": "access_token_xyz"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["strava_id"] == "12345"
    assert data["google_email"] == "testuser@example.com"
    assert "id" in data


def test_get_user_by_strava_id(client):
    # First, create a user
    create_resp = client.post("/users/", json={
        "strava_id": "getuser123",
        "google_email": "fetch@example.com",
        "strava_access_token": "token_123",
        "google_access_token": "token_456"
    })
    assert create_resp.status_code == 200
    user_id = create_resp.json()["id"]

    # Now, fetch the same user by Strava ID
    fetch_resp = client.get(f"/users/strava/getuser123")
    assert fetch_resp.status_code == 200
    data = fetch_resp.json()
    assert data["id"] == user_id
    assert data["google_email"] == "fetch@example.com"