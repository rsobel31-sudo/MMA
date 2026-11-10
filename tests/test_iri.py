from mma_predictor.sources.common import iri_to_uri


def test_non_ascii_url_is_percent_encoded():
    assert iri_to_uri("https://en.wikipedia.org/wiki/UFC_Fight_Night:_Procházka_vs._Stirling") == \
        "https://en.wikipedia.org/wiki/UFC_Fight_Night:_Proch%C3%A1zka_vs._Stirling"


def test_ascii_and_encoded_urls_unchanged():
    u = "https://www.sherdog.com/events/A-B-1?x=1&y=%C3%A1"
    assert iri_to_uri(u) == u
