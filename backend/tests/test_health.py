def test_health_check_returns_running_status(client):
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "message": "RazorMind AI API is running",
    }
