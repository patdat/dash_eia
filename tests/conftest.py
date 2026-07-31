# ---------------------------------------------------------------------------
# Credential-free boundary guard — copied from the repo-restructure project.
# Do not remove. If a test fails with "Blocked a real ...", the test is missing
# a mock, not the fixture being wrong.
# ---------------------------------------------------------------------------
import pytest

try:  # botocore is absent in repos with no AWS surface
    import botocore.client as _botocore_client
except ImportError:  # pragma: no cover
    _botocore_client = None

try:
    import requests as _requests
except ImportError:  # pragma: no cover
    _requests = None


@pytest.fixture(autouse=True)
def block_network_and_aws(request, monkeypatch):
    """Fail any non-``live`` test that reaches real AWS or real HTTP.

    Two boundaries, because covering one leaves the other open:

    - ``botocore.client.BaseClient._make_api_call`` catches every route to AWS
      whether the caller built a client or a resource.
    - ``requests.Session.request`` is the chokepoint every ``requests`` helper
      funnels through (``get``/``post``/``Session.get`` all call it).

    Tests that patch these themselves are unaffected — their patch replaces the
    object before it is used. Anything marked ``live`` is exempt by design.

    This exists because it already happened: a test suite published its own
    5-row synthetic fixtures over production S3 artifacts that `mei` and the
    Power BI feeds consume.
    """
    if "live" in request.keywords:
        return

    def _deny_aws(self, operation_name, api_params):
        raise RuntimeError(
            f"Blocked a real AWS API call ({operation_name}) from a test. "
            "Mock the boundary, or mark the test @pytest.mark.live."
        )

    def _deny_http(self, method, url, *args, **kwargs):
        raise RuntimeError(
            f"Blocked a real HTTP request ({method} {url}) from a test. "
            "Mock the transport, or mark the test @pytest.mark.live."
        )

    if _botocore_client is not None:
        monkeypatch.setattr(_botocore_client.BaseClient, "_make_api_call", _deny_aws)
    if _requests is not None:
        monkeypatch.setattr(_requests.Session, "request", _deny_http)
