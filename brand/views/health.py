from django.db import connection
from django.http import JsonResponse


def healthz(request):
    """Liveness plus a real database round-trip, for load balancers and compose."""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except Exception as exc:  # noqa: BLE001 - the endpoint reports, never raises
        return JsonResponse(
            {"status": "error", "database": "unavailable", "detail": str(exc)},
            status=503,
        )
    return JsonResponse({"status": "ok", "database": "ok"})
