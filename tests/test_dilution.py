from tfse.finance.dilution import dilution_reserve


def test_standard_dilution():
    # 2% dilution rate * 2x = 4% reserve
    assert abs(dilution_reserve(2.0) - 0.04) < 0.0001


def test_custom_multiplier():
    assert abs(dilution_reserve(3.0, multiplier=1.5) - 0.045) < 0.0001
