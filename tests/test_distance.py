from src.core.distance import haversine


def test_haversine_zero():
    assert haversine((0, 0), (0, 0)) == 0


def test_haversine_known():
    # Rough distance between São Paulo and Rio de Janeiro ~ 360 km
    d = haversine((-23.5505, -46.6333), (-22.9068, -43.1729))
    assert 340 <= d <= 380
