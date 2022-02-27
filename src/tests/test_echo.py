def test_echo(web_request):
    resp = web_request(
        'echo',
        {
            'message': 'Hello, World!',
        },
    )

    assert resp.get('result') == 'Hello, World!', resp.get('error')
