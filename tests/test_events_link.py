from mma_predictor.sources.events import link_names


def test_suffix_decides_between_relatives():
    data = {"Kai Kamaka III", "Kai Kamaka", "Andre Fili"}
    got = link_names({"Kai Kamaka III", "Andre Fili"}, data)
    assert got == {"Kai Kamaka III": "Kai Kamaka III", "Andre Fili": "Andre Fili"}
    assert "Kai Kamaka Jr." not in link_names({"Kai Kamaka Jr."}, data)  # still ambiguous: left out, not guessed
