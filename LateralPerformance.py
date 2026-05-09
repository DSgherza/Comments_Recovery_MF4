import numpy as np

def check_left(max, min):
    if max != "":
        if max < 0: 
            max = ""
    if min != "":
        if min > 0:
            min = ""
    return max, min

def check_right(max, min):
    if max != "":
        if max > 0:
            max = ""
    if min != "":
        if min < 0:
            min = ""
    return max, min

 
class LateralPerformance:
 
    def lateral_acceleration_start(self, maneuver: list, data: np.array, base:int, frequency:int):
        
        Lateral_acc_initial_brake = np.mean(data[maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][0]])
        return Lateral_acc_initial_brake
 
    def lateral_acceleration_maneuver(self, maneuver: list, data: list, base:int, frequency:int, nominal_radius:int, ay_start, direction_check):
        theorical_bigol_ay = ""
        if direction_check and maneuver[0] not in ["ABS_InTurn", "ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn"] and (maneuver[0] == "ABS_Braking" and abs(ay_start) < 1):
            effective_ay = data[0][maneuver[base][0]: maneuver[base][1]] - ay_start
        else:
            effective_ay = data[0][maneuver[base][0]: maneuver[base][1]]
        if maneuver[1][0] == maneuver[base][0]:
            mean_effective_ay = data[0][maneuver[1][0]]
        else:
            mean_effective_ay = np.mean(data[0][maneuver[1][0]: maneuver[base][0]])
        threshold = 1

        if maneuver[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn"] or (maneuver[0] == "ABS_Braking" and abs(effective_ay[0]) > threshold):
            if nominal_radius != "":
                radius_start = nominal_radius*np.sign(ay_start)
            else:
                radius_start = int(round(np.mean(data[1][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][0]])**2/np.mean(data[0][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][0]]), 0))
            theorical_ay = data[1][maneuver[base][0]: maneuver[base][1]]**2/radius_start
            theorical_bigol_ay = data[1][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][1]]**2/radius_start
            effective_ay = effective_ay - theorical_ay
            if mean_effective_ay > 0:                
                lateral_acc_max = max(effective_ay)
                lateral_acc_min = min(effective_ay)
                lateral_acc_max, lateral_acc_min = check_left(lateral_acc_max, lateral_acc_min)
            else:
                lateral_acc_min = max(effective_ay)
                lateral_acc_max = min(effective_ay)
                lateral_acc_max, lateral_acc_min = check_right(lateral_acc_max, lateral_acc_min)
            delta_ay_max = max(np.abs(effective_ay))
            found = False
            if maneuver[base][0] + int(round(0.5*frequency, 0)) <= maneuver[base][1]:
                if mean_effective_ay > 0:
                    lateral_peak_05 = max(effective_ay[0: int(round(0.5*frequency, 0))])
                    lateral_min_05 = min(effective_ay[0: int(round(0.5*frequency, 0))])
                    lateral_peak_05, lateral_min_05 = check_left(lateral_peak_05, lateral_min_05)
                else:
                    lateral_peak_05 = min(effective_ay[0: int(round(0.5*frequency, 0))])
                    lateral_min_05 = max(effective_ay[0: int(round(0.5*frequency, 0))])
                    lateral_peak_05, lateral_min_05 = check_right(lateral_peak_05, lateral_min_05)
                found = True
            if not found:
                lateral_peak_05 = ""
                lateral_min_05 = ""
 
            found = False
            if maneuver[base][0] + frequency <= maneuver[base][1]:
                if mean_effective_ay > 0:
                    lateral_peak_1 = max(effective_ay[0: int(frequency)])
                    lateral_min_1 = min(effective_ay[0: int(frequency)])
                    lateral_peak_1, lateral_min_1 = check_left(lateral_peak_1, lateral_min_1)
                else:
                    lateral_peak_1 = min(effective_ay[0: int(frequency)])
                    lateral_min_1 = max(effective_ay[0: int(frequency)])
                    lateral_peak_1, lateral_min_1 = check_right(lateral_peak_1, lateral_min_1)
                found = True
            if not found:
                lateral_peak_1 = ""
                lateral_min_1 = ""

            found = False
            if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
                if mean_effective_ay > 0:
                    lateral_peak_2 = max(effective_ay[0: int(2*frequency)])
                    lateral_min_2 = min(effective_ay[0: int(2*frequency)])
                    lateral_peak_2, lateral_min_2 = check_left(lateral_peak_2, lateral_min_2)
                else:
                    lateral_peak_2 = min(effective_ay[0: int(2*frequency)])
                    lateral_min_2 = max(effective_ay[0: int(2*frequency)])
                    lateral_peak_2, lateral_min_2 = check_right(lateral_peak_2, lateral_min_2)
                found = True
            if not found:
                lateral_peak_2 = ""
                lateral_min_2 = ""

            found = False
            if maneuver[base][0] + 5*frequency <= maneuver[base][1]:
                if mean_effective_ay > 0:
                    lateral_peak_5 = max(effective_ay[0: int(5*frequency)])
                    lateral_min_5 = min(effective_ay[0: int(5*frequency)])
                    lateral_peak_5, lateral_min_5 = check_left(lateral_peak_5, lateral_min_5)
                else:
                    lateral_peak_5 = min(effective_ay[0: int(5*frequency)])
                    lateral_min_5 = max(effective_ay[0: int(5*frequency)])
                    lateral_peak_5, lateral_min_5 = check_right(lateral_peak_5, lateral_min_5)
                found = True
            if not found:
                lateral_peak_5 = ""
                lateral_min_5 = ""            
        elif maneuver[0] == "ESC_ConstantRadius":
            radius_list = []
            radius_start = ""
            lateral_peak_05 = ""
            lateral_peak_1 = ""
            lateral_peak_2 = ""
            lateral_peak_5 = ""
            lateral_min_05 = ""
            lateral_min_1 = ""
            lateral_min_2 = ""
            lateral_min_5 = ""
            cont = 0
            if nominal_radius != "":
                radius_start = nominal_radius*np.sign(ay_start)
            else:
                if data[1][maneuver[base][0]] < 5/3.6:
                    for i in range(maneuver[base][0], maneuver[base][1]):
                        radius_list.append(int(round(data[1][i]**2/data[0][i], 0)))
                        #radius_list.append(int(round(np.mean(data[1][i - int(round(0.5*frequency, 0)): i])/np.mean(data[0][i - int(round(0.5*frequency, 0)): i]), 0)))
                        cont += 1
                        found = False
                        if len(radius_list) >= int(round(0.5*frequency)) and abs(radius_list[cont - 1]) >= 30:
                            cfr = radius_list[cont - 1]
                            for j in range(int(round(0.5*frequency))):
                                if abs(cfr - radius_list[cont - (j+1)]) > 2:
                                    found = False
                                    break
                                else:
                                    found = True
                        if found:
                            radius_start = radius_list[cont - 1]
                            break
                        else:
                            radius_start = int(round(np.mean(data[1][maneuver[base][0]: int(round(20*frequency)) + maneuver[base][0]])**2)/np.mean(data[0][maneuver[base][0]: int(round(20*frequency)) + maneuver[base][0]]))        
                else:
                    radius_start = int(round(np.mean(data[1][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][0]])**2)/np.mean(data[0][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][0]]))            
            if radius_start != "":    
                theorical_ay = data[1][maneuver[base][0]: maneuver[base][1]]**2/radius_start
                effective_ay = effective_ay - theorical_ay
                if mean_effective_ay > 0:                
                    lateral_acc_max = max(effective_ay)
                    lateral_acc_min = min(effective_ay)
                    lateral_acc_max, lateral_acc_min = check_left(lateral_acc_max, lateral_acc_min)
                else:
                    lateral_acc_min = max(effective_ay)
                    lateral_acc_max = min(effective_ay)
                    lateral_acc_max, lateral_acc_min = check_right(lateral_acc_max, lateral_acc_min)
                delta_ay_max = max(np.abs(effective_ay))
            else:
                lateral_acc_max = ""
                lateral_acc_min = ""
                delta_ay_max = ""
        else:
            radius_start = ""               
            lateral_acc_max = max(effective_ay)
            lateral_acc_min = min(effective_ay)
            lateral_acc_max, lateral_acc_min = check_left(lateral_acc_max, lateral_acc_min)
            delta_ay_max = max(np.abs(effective_ay))
            found = False
            if maneuver[base][0] + int(round(0.5*frequency, 0)) <= maneuver[base][1]:
                lateral_peak_05 = max(effective_ay[0: int(round(0.5*frequency, 0))])
                lateral_min_05 = min(effective_ay[0: int(round(0.5*frequency, 0))])
                lateral_peak_05, lateral_min_05 = check_left(lateral_peak_05, lateral_min_05)
                found = True
            if not found:
                lateral_peak_05 = ""
                lateral_min_05 = ""
 
            found = False
            if maneuver[base][0] + frequency <= maneuver[base][1]:
                lateral_peak_1 = max(effective_ay[0: int(frequency)])
                lateral_min_1 = min(effective_ay[0: int(frequency)])
                lateral_peak_1, lateral_min_1 = check_left(lateral_peak_1, lateral_min_1)
                found = True
            if not found:
                lateral_peak_1 = ""
                lateral_min_1 = ""

            found = False
            if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
                lateral_peak_2 = max(effective_ay[0: int(2*frequency)])
                lateral_min_2 = min(effective_ay[0: int(2*frequency)])
                lateral_peak_2, lateral_min_2 = check_left(lateral_peak_2, lateral_min_2)
                found = True
            if not found:
                lateral_peak_2 = ""
                lateral_min_2 = ""

            found = False
            if maneuver[base][0] + 5*frequency <= maneuver[base][1]:
                lateral_peak_5 = max(effective_ay[0: int(5*frequency)])
                lateral_min_5 = min(effective_ay[0: int(5*frequency)])
                lateral_peak_2, lateral_min_2 = check_left(lateral_peak_2, lateral_min_2)
                found = True
            if not found:
                lateral_peak_5 = ""
                lateral_min_5 = ""            
        return lateral_peak_05, lateral_peak_1, lateral_peak_2, lateral_peak_5, lateral_min_05, lateral_min_1, lateral_min_2, lateral_min_5, lateral_acc_max, lateral_acc_min, delta_ay_max, radius_start, effective_ay, theorical_bigol_ay
 
 
    def lateral_acceleration_steady(self, maneuver:list, initial_radius, effective_ay:np.array):
        nominal_radius = [10, 15, 30, 40, 55, 60, 75, 80, 100, 150, 200, 250, 300]
        radius_nominal = ""
        check = False
        if maneuver[0] in ["ABS_InTurn", "ESC_ConstantRadius", "ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn", "ABS_Braking"] and initial_radius != "":
            min_err = 300
            for i in range(len(nominal_radius)):
                if abs(abs(initial_radius) - nominal_radius[i]) < min_err:
                    radius_counter = i
                    min_err = abs(abs(initial_radius) - nominal_radius[i])
                    check = True
            if check:
                radius_nominal = nominal_radius[radius_counter]*np.sign(initial_radius)
            else:
                radius_nominal = ""
            lateral_app_range = max(effective_ay) - min(effective_ay)
        else:
            lateral_app_range = max(effective_ay) - min(effective_ay)
        return lateral_app_range, radius_nominal
    
    def jerk_lat_max(self, dictionaries, maneuvers, reference_string_speed):
        if "ABS" in maneuvers[0]:
            time_counter = maneuvers[2][0]
            max_jerk_lat = 0
            try:
                while dictionaries.objectives[reference_string_speed + "_kmh"][time_counter] > 10:
                    if abs(dictionaries.objectives["AyDer"][time_counter]) > max_jerk_lat:
                        max_jerk_lat = abs(dictionaries.objectives["AyDer"][time_counter])
                    time_counter += 1
            except IndexError:
                max_jerk_lat = ""
        elif "ESC_PartialBrkinTurn" == maneuvers[0] or "TCS" in maneuvers[0]:
            time_counter = maneuvers[2][0]
            max_jerk_lat = 0
            while time_counter <= maneuvers[2][1]:
                if abs(dictionaries.objectives["AyDer"][time_counter]) > max_jerk_lat:
                    max_jerk_lat = abs(dictionaries.objectives["AyDer"][time_counter])
                time_counter += 1
        elif "ESC_Handling" == maneuvers[0]:
            max_jerk_lat = ""
        elif "ESC" in maneuvers[0] and "ESC_Handling" != maneuvers[0] and "ESC_PartialBrkinTurn" != maneuvers[0]:
            time_counter = maneuvers[3][0]
            max_jerk_lat = 0
            while time_counter <= maneuvers[3][1]:
                if abs(dictionaries.objectives["AyDer"][time_counter]) > max_jerk_lat:
                    max_jerk_lat = abs(dictionaries.objectives["AyDer"][time_counter])
                time_counter += 1            
        return max_jerk_lat