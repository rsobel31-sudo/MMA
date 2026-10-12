from mma_predictor.fight_recaps import closeness, sherdog_play_by_play


def test_closeness_labels():
    herbert = [[1, "10-9 Camilo"] * 1 + ["10-9 Camilo", "10-9 Camilo"], [2, "10-9 Herbert", "10-9 Herbert", "10-9 Herbert"],
               [3, "10-9 Herbert", "10-9 Herbert", "10-9 Herbert"]]
    assert closeness(herbert, "Jai Herbert", True) == "close"
    souza = [[1, "10-9 Souza"] * 1 + ["10-9 Souza", "10-9 Souza"], [2, "10-9 Souza", "10-9 Souza", "10-9 Souza"],
             [3, "10-9 Godinez", "10-9 Godinez", "10-9 Godinez"]]
    assert closeness(souza, "Lupita Godinez", True) == "disputed"
    clear = [[r, "10-9 Smith", "10-9 Smith", "10-9 Smith"] for r in (1, 2, 3)]
    assert closeness(clear, "John Smith", True) == "clear"
    allen = [[1, "10-9 Duncan", "10-9 Duncan", "10-9 Duncan"], [2, "10-8 Allen", "10-8 Allen", "10-8 Allen"],
             [3, "10-9 Duncan", "10-9 Duncan", "10-9 Allen"], [4, "10-9 Duncan", "10-9 Duncan", "10-9 Duncan"]]
    assert closeness(allen, "Brendan Allen", False) == "from behind"
    assert closeness([], "X", True) is None


def test_sherdog_parser_splits_bouts_and_scores():
    page = ("<p>Jai Herbert (155) vs. Matheus Camilo (156) Round 1 Herbert jabs. Sherdog Scores A scores the round: 10-9 Herbert "
            "B scores the round: 10-9 Herbert C scores the round: 10-9 Camilo Round 2 More jabs. A scores the round: 10-9 Herbert The Official Result Jai Herbert def. Matheus Camilo—Unanimous Decision "
            "Ann Bee (115) vs. Cee Dee (116) Round 1 Grappling. A scores the round: 10-9 Dee</p>")
    out = sherdog_play_by_play(page, [{"a": "Jai Herbert", "b": "Matheus Camilo"}, {"a": "Ann Bee", "b": "Cee Dee"}])
    assert out["jai-herbert-matheus-camilo"]["scores"] == [[1, "10-9 Herbert", "10-9 Herbert", "10-9 Camilo"], [2, "10-9 Herbert"]]
    assert out["ann-bee-cee-dee"]["scores"] == [[1, "10-9 Dee"]]
