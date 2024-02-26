import unittest
from module.functions import calc_energy  # Stellen Sie sicher, dass Sie calc_energy korrekt importieren


class TestCalcEnergy(unittest.TestCase):

    def test_calc_energy_basic(self):
        # Test mit grundlegenden Werten
        self.assertEqual(calc_energy([100, 200, 300, 400]), 0.25)

    def test_calc_energy_with_interval(self):
        # Test mit einem spezifischen Zeitintervall
        self.assertEqual(calc_energy([100, 200, 300, 400], interval=0.5), 0.5)

    def test_calc_energy_kwh(self):
        # Test mit kWh als Ausgabe
        self.assertEqual(calc_energy([1000, 2000, 3000, 4000], kwh=True), 2.5)

    def test_calc_energy_rounding(self):
        # Test mit Rundung
        self.assertEqual(calc_energy([1234, 2345, 3456], round_=1), 1.8)

    def test_calc_energy_negative_values(self):
        # Test mit negativen Werten
        self.assertEqual(calc_energy([-100, -200, -300]), -0.150)


# Führen Sie die Tests aus
if __name__ == '__main__':
    unittest.main()
