import numpy as np

class Overall:
    def overall_distance(time, cont, satellites = None, speed = None, control = None):
        distance = 0
        distance_control = 0
        check_control = False
        if satellites is not None and control is not None:
            velocity = speed
            for i in range(len(satellites)):
                if satellites[i] == 0:
                    cont += 1
                    velocity = control
                    check_control = True
                    break
        if satellites is not None and control is None:
            velocity = speed
        if control is not None and satellites is None:
            velocity = control
            check_control = True
        if satellites is None and speed is not None:
            pass
        for i in range(len(velocity)):
            try:
                distance = distance + velocity[i+1]*(time[i+1]-time[i])
            except IndexError:
                pass
        if check_control:
            distance_control = distance
        return distance, distance_control, cont

    def overall_time(self, maneuvers, dictionaries):
        return round(dictionaries[maneuvers[1][1]] - dictionaries[maneuvers[1][0]], 2)
    
    def intensities(self, signal, start, end):
        max_intensity = np.max(signal[start:end])
        mean_intensity = np.mean(signal[start:end])
        return max_intensity, mean_intensity