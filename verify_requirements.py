"""Verification script for OpenAPI-Compliant Model Inference Service.
Checks all 10 programmatic core requirements.
"""

import re
import sys
from pathlib import Path


def log(msg, status="INFO"):
    print(f"[{status}] {msg}")


def verify_req_1_openapi_spec(root: Path):
    """Req 1: Valid OpenAPI 3.0 specification defining contract."""
    spec_path = root / "openapi.yaml"
    assert spec_path.is_file(), "openapi.yaml not found in root"
    content = spec_path.read_text(encoding="utf-8")

    assert re.search(r"openapi:\s*3\.0\.\d+", content), "openapi must be 3.0.x"
    assert "/v1/predict:" in content, "Path /v1/predict missing in openapi.yaml"
    assert "post:" in content, "POST method missing for /v1/predict"
    assert "text" in content, "text property required in schema"
    assert "label" in content, "label property required in response"
    assert "score" in content, "score property required in response"

    try:
        import yaml
        from openapi_spec_validator import validate
        spec_dict = yaml.safe_load(content)
        validate(spec_dict)
        log("openapi.yaml strictly validated against OpenAPI 3.0 spec", "INFO")
    except ImportError:
        pass
    log("req-1-openapi-spec: PASS", "SUCCESS")


def verify_req_2_docker_compose_setup(root: Path):
    """Req 2: Docker compose orchestrating frontend proxy and backend api."""
    compose_path = root / "docker-compose.yml"
    assert compose_path.is_file(), "docker-compose.yml not found in root"
    content = compose_path.read_text(encoding="utf-8")

    assert "nginx:" in content, "nginx service missing in docker-compose.yml"
    assert "api:" in content, "api service missing in docker-compose.yml"
    assert re.search(r"8080:80", content), "Host port 8080 must be mapped to nginx port 80"
    assert "healthcheck:" in content, "healthcheck missing under api service"
    assert "service_healthy" in content, "nginx must depend on api with condition: service_healthy"
    log("req-2-docker-compose-setup: PASS", "SUCCESS")


def verify_req_3_network_isolation(root: Path):
    """Req 3: Backend API container isolated from host network."""
    compose_path = root / "docker-compose.yml"
    content = compose_path.read_text(encoding="utf-8")

    # Check api service block
    api_section_match = re.search(r"api:(.*?)(nginx:|$)", content, re.DOTALL)
    assert api_section_match, "Could not isolate api section in docker-compose.yml"
    api_section = api_section_match.group(1)

    assert "ports:" not in api_section, "api service must NOT have 'ports:' mapped to host!"
    assert "expose:" in api_section, "api service must use 'expose:' for internal communication"
    assert "8000" in api_section, "api service should expose port 8000"
    log("req-3-network-isolation: PASS", "SUCCESS")


def verify_req_4_health_endpoint(root: Path):
    """Req 4: Application exposes GET /health returning {'status': 'ok'}."""
    app_path = root / "app.py"
    assert app_path.is_file(), "app.py not found"
    content = app_path.read_text(encoding="utf-8")

    assert '/health' in content, "/health endpoint definition missing"
    assert '"status": "ok"' in content or "'status': 'ok'" in content or 'status = "ok"' in content
    log("req-4-health-endpoint: PASS", "SUCCESS")


def verify_req_5_inference_endpoint(root: Path):
    """Req 5: Backend API implements POST /v1/predict with text -> label, score."""
    app_path = root / "app.py"
    content = app_path.read_text(encoding="utf-8")

    assert '/v1/predict' in content, "/v1/predict endpoint missing"
    assert 'label' in content and 'score' in content, "label and score fields required"
    log("req-5-inference-endpoint: PASS", "SUCCESS")


def verify_req_6_input_validation(root: Path):
    """Req 6: Inference endpoint rejects missing/invalid payloads."""
    app_path = root / "app.py"
    content = app_path.read_text(encoding="utf-8")

    assert "PredictRequest" in content, "PredictRequest schema validation missing"
    assert "text: str" in content, "text: str field required in schema"
    log("req-6-input-validation: PASS", "SUCCESS")


def verify_req_7_security_headers(root: Path):
    """Req 7: Nginx reverse proxy injects X-Content-Type-Options: nosniff."""
    nginx_path = root / "nginx.conf"
    assert nginx_path.is_file(), "nginx.conf not found"
    content = nginx_path.read_text(encoding="utf-8")

    assert re.search(r"add_header\s+X-Content-Type-Options\s+[\"']?nosniff[\"']?", content, re.IGNORECASE), \
        "X-Content-Type-Options nosniff header missing in nginx.conf"
    log("req-7-security-headers: PASS", "SUCCESS")


def verify_req_8_rate_limiting(root: Path):
    """Req 8: Nginx reverse proxy defines rate limiting zone and directive."""
    nginx_path = root / "nginx.conf"
    content = nginx_path.read_text(encoding="utf-8")

    assert "limit_req_zone" in content, "limit_req_zone directive missing in nginx.conf"
    assert "limit_req" in content, "limit_req directive missing in nginx.conf"
    log("req-8-rate-limiting: PASS", "SUCCESS")


def verify_req_9_proxy_forwarding(root: Path):
    """Req 9: Nginx forwards X-Real-IP and X-Forwarded-For."""
    nginx_path = root / "nginx.conf"
    content = nginx_path.read_text(encoding="utf-8")

    assert "proxy_set_header X-Real-IP" in content, "proxy_set_header X-Real-IP missing"
    assert "proxy_set_header X-Forwarded-For" in content, "proxy_set_header X-Forwarded-For missing"
    assert "proxy_pass http://api:8000" in content, "proxy_pass http://api:8000 missing"
    log("req-9-proxy-forwarding: PASS", "SUCCESS")


def verify_req_10_nginx_config_validation(root: Path):
    """Req 10: Nginx configuration file syntax validation."""
    nginx_path = root / "nginx.conf"
    content = nginx_path.read_text(encoding="utf-8")

    open_braces = content.count("{")
    close_braces = content.count("}")
    assert open_braces == close_braces, f"Mismatched braces in nginx.conf: {open_braces} != {close_braces}"
    assert "events" in content and "http" in content and "server" in content and "location" in content
    log("req-10-nginx-config-validation: PASS", "SUCCESS")


def main():
    root = Path(__file__).resolve().parent
    print("=" * 60)
    print("Verifying OpenAPI-Compliant Model Inference Service Requirements")
    print("=" * 60)

    checks = [
        verify_req_1_openapi_spec,
        verify_req_2_docker_compose_setup,
        verify_req_3_network_isolation,
        verify_req_4_health_endpoint,
        verify_req_5_inference_endpoint,
        verify_req_6_input_validation,
        verify_req_7_security_headers,
        verify_req_8_rate_limiting,
        verify_req_9_proxy_forwarding,
        verify_req_10_nginx_config_validation,
    ]

    passed = 0
    for check in checks:
        try:
            check(root)
            passed += 1
        except Exception as e:
            log(f"{check.__name__} FAILED: {e}", "FAIL")
            sys.exit(1)

    print("=" * 60)
    print(f"All {passed}/{len(checks)} requirements verified successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
