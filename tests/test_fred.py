from fred import FredContent

class TestFred:
    def test_gas(self):
        f = FredContent()
        f.post_gas_prices()
        assert True

    def test_egg(self):
        f = FredContent()
        f.post_egg_prices()
        assert True        