from urllib.request import Request, urlopen

from phistory.dummy_upstream import dummy_upstream


def test_dummy_upstream_returns_anthropic_success():
    with dummy_upstream() as base_url:
        req = Request(f"{base_url}/v1/messages", data=b'{"ok":true}', method="POST")
        with urlopen(req, timeout=5) as resp:
            assert resp.status == 200
            assert b"msg_phistory_dummy" in resp.read()
