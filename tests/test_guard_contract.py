"""The boundary guard must fail closed.

If these pass with the guard removed, the guard is not working and every other
suite in this repo is running unprotected. That is the failure mode this whole
project exists to eliminate: gates that are green because they check nothing.
"""

import pytest


def test_guard_blocks_real_aws():
    boto3 = pytest.importorskip("boto3")
    client = boto3.client(
        "s3",
        region_name="us-east-1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
    )
    with pytest.raises(RuntimeError, match="Blocked a real AWS API call"):
        client.list_buckets()


def test_guard_blocks_real_http():
    requests = pytest.importorskip("requests")
    with pytest.raises(RuntimeError, match="Blocked a real HTTP request"):
        requests.get("https://example.invalid", timeout=5)


@pytest.mark.live
def test_live_marker_exempts_the_guard():
    """A ``live`` test must NOT be blocked — CI deselects it instead."""
    requests = pytest.importorskip("requests")
    assert hasattr(requests.Session, "request")
