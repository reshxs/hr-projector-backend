def test_echo(jsonrpc_request):
    resp = jsonrpc_request(
        'echo',
        {
            'message': 'Hello, World!',
        },
        use_auth=False,
    )

    assert resp.get('result') == 'Hello, World!', resp.get('error')
