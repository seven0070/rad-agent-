from rad.tools import fetch_public_page, html_to_text, parse_ddg_html


def test_html_to_text_strips_scripts():
    html = """
    <html><head><title>T</title><style>body{}</style></head>
    <body><h1>Hello Rad</h1><p>Some <b>bold</b> text</p>
    <script>var evil = "injected";</script></body></html>
    """
    text = html_to_text(html)
    assert "Hello Rad" in text
    assert "bold" in text
    assert "evil" not in text
    assert "body{}" not in text


def test_fetch_bad_url():
    text, err = fetch_public_page("ftp://nope")
    assert text == ""
    assert err


def test_ddg_parse():
    raw = """
    <a rel="nofollow" class="result__a" href="//duckduckgo.com/l/?uddg=https%3A%2F%2Fexample.com%2Fpage">Example <b>Title</b></a>
    <a class="result__snippet" href="#">A great <i>snippet</i> here.</a>
    """
    res = parse_ddg_html(raw)
    assert len(res) == 1
    assert res[0]["url"] == "https://example.com/page"
    assert res[0]["title"] == "Example Title"
    assert "snippet" in res[0]["snippet"]
