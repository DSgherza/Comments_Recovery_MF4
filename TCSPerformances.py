class TCSPerformances:

    def launch_time(self, dictionaries, maneuver, speed, reference_speed):
        i = maneuver[2][0]
        try:
            while dictionaries.objectives[reference_speed + "_ms"][i] <= speed/3.6 and i <= maneuver[2][1] + 1:
                i += 1
            if i < maneuver[2][1]:
                launch = dictionaries.time_resampled[i] - dictionaries.time_resampled[maneuver[2][0]]
            else:
                launch = ""
        except IndexError:
            launch = ""
        return launch