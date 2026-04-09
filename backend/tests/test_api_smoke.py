from fastapi.testclient import TestClient

from app.main import app


def test_health_returns_ok() -> None:
    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert isinstance(payload["dataset_rows"], int)


def test_top10_endpoint_exists() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/top10")

    assert response.status_code == 200
    payload = response.json()
    assert "items" in payload


def test_top10_prices_are_sorted_ascending() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/top10?limit=10")

    assert response.status_code == 200
    payload = response.json()
    prices = [
        item["renta_mensual_con_impuestos"]
        for item in payload["items"]
        if item["renta_mensual_con_impuestos"] is not None
    ]
    assert prices == sorted(prices)


def test_search_prepago_filter_returns_only_prepago_rows() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/search?tipo_pago=prepago&page_size=20")

    assert response.status_code == 200
    payload = response.json()
    assert all(item["es_prepago"] == 1 for item in payload["items"])


def test_product_detail_returns_404_for_missing_item() -> None:
    with TestClient(app) as client:
        response = client.get("/api/v1/products/999999999")

    assert response.status_code == 404
