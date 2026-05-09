import numpy as np
class BrakePerformance:

    def pedal_rate(self, item: list, dictionaries: dict) -> float:
        time_counter = item[2][0]
        der_list = []
        while dictionaries.objectives["BrakePedalPosition"][time_counter] < dictionaries.objectives["BrakePedalPosition"][time_counter + 5]:
            time_counter += 1
        time_counter_2 = item[2][0]
        while dictionaries.objectives["BrakePedalPosition"][time_counter_2] < dictionaries.objectives["BrakePedalPosition"][time_counter] - 0.1*dictionaries.objectives["BrakePedalPosition"][time_counter]:
            time_counter_2 += 1
            der_list.append((dictionaries.objectives["BrakePedalPosition"][time_counter_2 + 1] - dictionaries.objectives["BrakePedalPosition"][time_counter_2])/(dictionaries.time_resampled[time_counter_2 + 1] - dictionaries.time_resampled[time_counter_2]))
        der_total_array = np.array(der_list)
        try:
            pedal_rate = round(np.mean(der_total_array), 2) #miglioramento ricerca peak rate
        except ValueError:
            pedal_rate = ""
        return pedal_rate

    def pedal_type(self, pedal_rate: float) -> str:
        try:
            if pedal_rate >= 100:
                pedal_type = "SPIKE"
            elif pedal_rate == "":
                pedal_type = ""
            else:
                pedal_type = "SLOW"
        except TypeError:
            pedal_type = "SLOW"
        return pedal_type