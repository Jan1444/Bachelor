def adjust_thermal_mass(heizlast, v, indoor_temp, outdoor_temp, delta_temp, time_interval, previous_mass_estimate,
                        c_air=1005, rho_air=1.225, c_material=840, rho_material=2300, learning_rate=0.1):
    # Thermische Masse der Luft im Raum
    thermal_mass_air = v * rho_air * c_air

    # Initiale Schätzung der thermischen Masse der Objekte
    thermal_mass_material = previous_mass_estimate

    # Gesamte thermische Masse (Luft + Objekte)
    total_thermal_mass = thermal_mass_air + thermal_mass_material

    # Berechnung der von der Heizlast zugeführten Energie
    energy_input = heizlast * time_interval

    # Berechnung der erwarteten Temperaturänderung
    expected_temp_change = energy_input / total_thermal_mass

    # Berechnung des Fehlers (Differenz zwischen erwarteter und beobachteter Temperaturänderung)
    error = expected_temp_change - delta_temp

    # Anpassung der Schätzung der thermischen Masse der Objekte
    thermal_mass_material_adjusted = thermal_mass_material - learning_rate * error * total_thermal_mass / c_material

    return thermal_mass_air, max(thermal_mass_material_adjusted, 0)  # Verhindert negative Werte


# Beispielaufruf der Funktion
air_mass, adjusted_material_mass = adjust_thermal_mass(heizlast=500, v=45, indoor_temp=20, outdoor_temp=5, delta_temp=2,
                                                       time_interval=900, previous_mass_estimate=9962)
print(f"Thermische Masse der Luft: {air_mass} kg, Angepasste thermische Masse der Objekte: {adjusted_material_mass} kg")
