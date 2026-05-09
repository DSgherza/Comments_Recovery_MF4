import numpy as np

class ReactionPerformance():

    def bite_time(self, dictionaries, maneuver):
        found = True
        initial_time = dictionaries.time_resampled[maneuver[2][0]]
        ax_new = dictionaries.objectives["Ax"][maneuver[2][0]: maneuver[2][1]] - dictionaries.objectives["Ax"][maneuver[2][0]]
        i = 0
        try:
            while ax_new[i] > -0.6:
                i += 1
        except IndexError:
            found = False
        if found:
            final_time = dictionaries.time_resampled[maneuver[2][0] + i]
            time = (final_time - initial_time)*1000
        else:
            time = ""
        return time

    def peak_500(self, dictionaries, maneuver):
        return np.min(dictionaries.objectives["Ax"][maneuver[2][0]: maneuver[2][0] + int(round(0.5*dictionaries.frequency))]), (dictionaries.time_resampled[maneuver[2][0] + np.argmin(dictionaries.objectives["Ax"][maneuver[2][0]: maneuver[2][0] + int(round(0.5*dictionaries.frequency))])] - dictionaries.time_resampled[maneuver[2][0]])*1000

    def lock_time(self, dictionaries, maneuver, corner, reference_speed):
        if "ABSTrigger_FL" in dictionaries.objectives:
            initial_time = dictionaries.time_resampled[maneuver[2][0]]
            i = 0
            try:
                while dictionaries.objectives["ABSTrigger_" + corner][maneuver[2][0]: maneuver[2][1]][i] < 0.5:
                    i += 1
                final_time = dictionaries.time_resampled[maneuver[2][0] + i]
                time = (final_time - initial_time)*1000
                wheel_slip = (dictionaries.objectives["WheelSpeed_" + corner + "_ms"][maneuver[2][0] + i] - dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0] + i])/dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0] + i]
            except IndexError:
                time = ""
                wheel_slip = ""
        else:
            time = ""
            wheel_slip = ""
        return time, wheel_slip