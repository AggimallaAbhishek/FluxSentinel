def extract_features(payload: dict) -> dict:
    request_rate = float(payload.get("request_rate", 0))
    payload_size = float(payload.get("payload_size", 0))

    failed_logins = float(payload.get("failed_logins", 0))
    total_logins = float(payload.get("total_logins", 0))
    if total_logins > 0:
        failed_login_ratio = failed_logins / total_logins
    else:
        failed_login_ratio = 1.0 if int(payload.get("status_code", 200)) in (401, 403) else 0.0

    unique_endpoints_count = float(payload.get("unique_endpoints_count", 1))
    time_gap_between_requests = float(payload.get("time_gap_between_requests", 0.1))

    baseline_payload_size = float(payload.get("baseline_payload_size", 512))
    if baseline_payload_size > 0:
        payload_size_anomaly = payload_size / baseline_payload_size
    else:
        payload_size_anomaly = payload_size

    return {
        "request_rate": request_rate,
        "failed_login_ratio": failed_login_ratio,
        "unique_endpoints_count": unique_endpoints_count,
        "time_gap_between_requests": time_gap_between_requests,
        "payload_size_anomaly": payload_size_anomaly,
    }
