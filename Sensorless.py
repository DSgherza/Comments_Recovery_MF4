import numpy as np

class Sensorless:

    def force_avg_and_errors(self, signals, reference_speed, corner, start):
        found = True
        avg_estimated_force = ""
        avg_measured_force = ""
        relative_force_error = ""
        ground_force_error = ""
        avg_requested_force = ""
        if "EstimatedForce_" + corner in signals.objectives:
            if "EstimatedForce_" + corner in signals.times:
                if signals.times["EstimatedForce_" + corner][1] >= start:
                    try:
                        time_counter = start
                        while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                            time_counter += 1
                        start_new = time_counter
                    except IndexError:
                        found = False
                    if found:
                        try:
                            while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                                time_counter += 1
                            target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                        except IndexError:
                            found = False
                    if found:
                        try:
                            while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                                time_counter -= 1
                            end = time_counter
                        except IndexError:
                            found = False
                    if found:
                        avg_estimated_force = np.mean(signals.objectives["EstimatedForce_" + corner][start_new: end])
            else:
                try:
                    time_counter = start
                    while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                        time_counter += 1
                    start_new = time_counter
                except IndexError:
                    found = False
                if found:
                    try:
                        while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                            time_counter += 1
                        target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                    except IndexError:
                        found = False
                if found:
                    try:
                        while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                            time_counter -= 1
                        end = time_counter
                    except IndexError:
                        found = False
                if found:
                    avg_estimated_force = np.mean(signals.objectives["EstimatedForce_" + corner][start_new: end])
        found = True
        if "MeasuredForce_" + corner in signals.objectives:
            if "MeasuredForce_" + corner in signals.times:
                if signals.times["MeasuredForce_" + corner][1] >= start:
                    try:
                        time_counter = start
                        while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                            time_counter += 1
                        start_new = time_counter
                    except IndexError:
                        found = False
                    if found:
                        try:
                            while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                                time_counter += 1
                            target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                        except IndexError:
                            found = False
                    if found:
                        try:
                            while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                                time_counter -= 1
                            end = time_counter
                        except IndexError:
                            found = False
                    if found:
                        avg_measured_force = np.mean(signals.objectives["MeasuredForce_" + corner][start_new: end])
            else:
                try:
                    time_counter = start
                    while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                        time_counter += 1
                    start_new = time_counter
                except IndexError:
                    found = False
                if found:
                    try:
                        while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                            time_counter += 1
                        target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                    except IndexError:
                        found = False
                if found:
                    try:
                        while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                            time_counter -= 1
                        end = time_counter
                    except IndexError:
                        found = False
                if found:
                    avg_measured_force = np.mean(signals.objectives["MeasuredForce_" + corner][start_new: end])
        if "RequestedForce_" + corner in signals.objectives:
            if "RequestedForce_" + corner in signals.times:
                if signals.times["RequestedForce_" + corner][1] >= start:
                    try:
                        time_counter = start
                        while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                            time_counter += 1
                        start_new = time_counter
                    except IndexError:
                        found = False
                    if found:
                        try:
                            while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                                time_counter += 1
                            target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                        except IndexError:
                            found = False
                    if found:
                        try:
                            while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                                time_counter -= 1
                            end = time_counter
                        except IndexError:
                            found = False
                    if found:
                        avg_requested_force = np.mean(signals.objectives["RequestedForce_" + corner][start_new: end])
            else:
                try:
                    time_counter = start
                    while signals.objectives[reference_speed + "_kmh"][time_counter] >= 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                        time_counter += 1
                    start_new = time_counter
                except IndexError:
                    found = False
                if found:
                    try:
                        while signals.objectives["BrakePedalPosition"][time_counter] >= 1.5:
                            time_counter += 1
                        target_speed = signals.objectives[reference_speed + "_kmh"][time_counter] + 0.1*signals.objectives[reference_speed + "_kmh"][time_counter]
                    except IndexError:
                        found = False
                if found:
                    try:
                        while signals.objectives[reference_speed + "_kmh"][time_counter] <= target_speed:
                            time_counter -= 1
                        end = time_counter
                    except IndexError:
                        found = False
                if found:
                    avg_requested_force = np.mean(signals.objectives["RequestedForce_" + corner][start_new: end])
        if avg_estimated_force != "" and avg_measured_force != "":
            relative_force_error = (avg_estimated_force - avg_measured_force)/avg_measured_force
            ground_force_error = (avg_estimated_force - avg_measured_force)/45000
        return avg_estimated_force, avg_measured_force, avg_requested_force, relative_force_error, ground_force_error

    def touch_disc_positions(self, signals, corner, start, reference_speed):
        time_counter = start
        start_new = ""
        sensorless_wear = ""
        estimated_position = ""
        measured_position = ""
        if "EstimatedDistanceTouchDiscPosition_" + corner in signals.objectives:
            if "EstimatedDistanceTouchDiscPosition_" + corner in signals.times:
                if signals.times["EstimatedDistanceTouchDiscPosition_" + corner][1] >= start:
                    try:
                        while signals.objectives["BrakePedalPosition"][time_counter] > 0.05:
                            time_counter -= 1
                        start_new = time_counter
                        sensorless_wear = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                    except IndexError:
                        pass
                    try:
                        while signals.objectives[reference_speed + "kmh"][time_counter] > 0.9*signals.objectives[reference_speed + "kmh"][start]:
                            time_counter += 1
                        estimated_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                    except IndexError:
                        pass
                    time_counter = start_new
                    if "MeasuredForce_" + corner in signals.objectives:
                        if "MeasuredForce_" + corner in signals.times:
                            if signals.times["MeasuredForce_" + corner][1] >= start:
                                try:
                                    while signals.objectives["MeasuredForce_" + corner][time_counter] < 250:
                                        time_counter += 1
                                    measured_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                                except IndexError:
                                    pass
                        else:
                            try:
                                while signals.objectives["MeasuredForce_" + corner][time_counter] < 250:
                                    time_counter += 1
                                measured_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                            except IndexError:
                                pass
            else:
                try:
                    while signals.objectives["BrakePedalPosition"][time_counter] > 0.05:
                        time_counter -= 1
                    start_new = time_counter
                    sensorless_wear = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                except IndexError:
                    pass
                try:
                    while signals.objectives[reference_speed + "_kmh"][time_counter] > 0.9*signals.objectives[reference_speed + "_kmh"][start]:
                        time_counter += 1
                    estimated_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                except IndexError:
                    pass
                time_counter = start_new
                if "MeasuredForce_" + corner in signals.objectives:
                    if "MeasuredForce_" + corner in signals.times:
                        if signals.times["MeasuredForce_" + corner][1] >= start:
                            try:
                                while signals.objectives["MeasuredForce_" + corner][time_counter] < 250:
                                    time_counter += 1
                                measured_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                            except IndexError:
                                pass
                    else:
                        try:
                            while signals.objectives["MeasuredForce_" + corner][time_counter] < 250:
                                time_counter += 1
                            measured_position = signals.objectives["EstimatedDistanceTouchDiscPosition_" + corner][time_counter]
                        except IndexError:
                            pass
        return estimated_position, measured_position, sensorless_wear, start_new