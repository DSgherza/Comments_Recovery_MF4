import numpy as np
import math

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

class YawRatePerformance:
    
    def yawrate_maneuver(self, maneuver: list, data: list, base:int, initial_radius: int, frequency: int, direction_check, yaw_start):
        if direction_check and maneuver[0] not in ["ABS_InTurn", "ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn"] and (maneuver[0] == "ABS_Braking" and abs(yaw_start) < 3):
            effective_yaw = data[1][maneuver[base][0]: maneuver[base][1]] - yaw_start
            if "ABS" in maneuver[0]:
                effective_plot = data[1][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1] + int(round(0.5*frequency, 0))] - yaw_start
            else:
                effective_plot = data[1][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1]] - yaw_start
        else:
            effective_yaw = data[1][maneuver[base][0]: maneuver[base][1]]
            if "ABS" in maneuver[0]:
                effective_plot = data[1][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1] + int(round(0.5*frequency, 0))]
            elif "TCS" in maneuver[0]:
                effective_plot = data[1][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1] + int(round(frequency, 0))]
            else:
                effective_plot = data[1][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1]]
        if maneuver[1][0] == maneuver[base][0]:
            mean_effective_yaw = data[1][maneuver[1][0]]
        else:
            mean_effective_yaw = np.mean(data[1][maneuver[1][0]: maneuver[base][0]])
        threshold = 3
        theorical_bigol_yaw = ""
        if maneuver[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn"] or (maneuver[0] == "ABS_Braking" and abs(effective_yaw[0]) > threshold and initial_radius != ""):
            theorical_yaw = ((data[0][maneuver[base][0]: maneuver[base][1]])/initial_radius)*180/math.pi
            theorical_bigol_yaw = ((data[0][maneuver[base][0] - int(round(0.5*frequency, 0)): maneuver[base][1]])/initial_radius)*180/math.pi
            if "ABS" in maneuver[0]:
                theorical_plot = ((data[0][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1] + int(round(0.5*frequency, 0))])/initial_radius)*180/math.pi
            else:
                theorical_plot = ((data[0][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1]])/initial_radius)*180/math.pi
            effective_yaw = effective_yaw - theorical_yaw
            found = False
            if maneuver[base][0] + int(round(0.5*frequency, 0)) <= maneuver[base][1]:
                if mean_effective_yaw > 0:
                    yaw_peak_05 = max(effective_yaw[0: int(round(0.5*frequency, 0))])
                    yaw_min_05 = min(effective_yaw[0: int(round(0.5*frequency, 0))])
                    yaw_peak_05, yaw_min_05 = check_left(yaw_peak_05, yaw_min_05)
                else:
                    yaw_peak_05 = min(effective_yaw[0: int(round(0.5*frequency, 0))])
                    yaw_min_05 = max(effective_yaw[0: int(round(0.5*frequency, 0))])
                    yaw_peak_05, yaw_min_05 = check_right(yaw_peak_05, yaw_min_05)
                yawrate_rms_05 = np.sqrt(1/len(effective_yaw[0: int(round(0.5*frequency, 0))])*np.sum(effective_yaw[0: int(round(0.5*frequency, 0))]**2))
                found = True
            if not found:
                yaw_peak_05 = ""
                yaw_min_05 = ""
                yawrate_rms_05 = ""
 
            found = False
            if maneuver[base][0] + frequency <= maneuver[base][1]:
                if mean_effective_yaw > 0:
                    yaw_peak_1 = max(effective_yaw[0: int(frequency)])
                    yaw_min_1 = min(effective_yaw[0: int(frequency)])
                    yaw_peak_1, yaw_min_1 = check_left(yaw_peak_1, yaw_min_1)
                else:
                    yaw_peak_1 = min(effective_yaw[0: int(frequency)])
                    yaw_min_1 = max(effective_yaw[0: int(frequency)])
                    yaw_peak_1, yaw_min_1 = check_right(yaw_peak_1, yaw_min_1)
                yawrate_rms_1 = np.sqrt(1/len(effective_yaw[0: int(frequency)])*np.sum(effective_yaw[0: int(frequency)]**2))
                found = True
            if not found:
                yaw_peak_1 = ""
                yaw_min_1 = ""
                yawrate_rms_1 = ""

            found = False
            if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
                if mean_effective_yaw > 0:
                    yaw_peak_2 = max(effective_yaw[0: int(round(2*frequency, 0))])
                    yaw_min_2 = min(effective_yaw[0: int(round(2*frequency, 0))])
                    yaw_peak_2, yaw_min_2 = check_left(yaw_peak_2, yaw_min_2)
                else:
                    yaw_peak_2 = min(effective_yaw[0: int(round(2*frequency, 0))])
                    yaw_min_2 = max(effective_yaw[0: int(round(2*frequency, 0))])
                    yaw_peak_2, yaw_min_2 = check_right(yaw_peak_2, yaw_min_2)
                yawrate_rms_2 = np.sqrt(1/len(effective_yaw[0: int(2*frequency)])*np.sum(effective_yaw[0: int(2*frequency)]**2))
                found = True
            if not found:
                yaw_peak_2 = ""
                yaw_min_2 = ""
                yawrate_rms_2 = ""
            
            found = False
            if maneuver[base][0] + 5*frequency <= maneuver[base][1]:
                if mean_effective_yaw > 0:
                    yaw_peak_5 = max(effective_yaw[0: int(5*frequency)])
                    yaw_min_5 = min(effective_yaw[0: int(5*frequency)])
                    yaw_peak_5, yaw_min_5 = check_left(yaw_peak_5, yaw_min_5)
                else:
                    yaw_peak_5 = min(effective_yaw[0: int(5*frequency)])
                    yaw_min_5 = max(effective_yaw[0: int(5*frequency)])
                    yaw_peak_5, yaw_min_5 = check_right(yaw_peak_5, yaw_min_5)

                yawrate_rms_5 = np.sqrt(1/len(effective_yaw[0: int(5*frequency)])*np.sum(effective_yaw[0: int(5*frequency)]**2))
                found = True
            if not found:
                yaw_peak_5 = ""
                yaw_min_5 = ""
                yawrate_rms_5 = ""

            if mean_effective_yaw > 0:
                yaw_max = max(effective_yaw)
                yaw_min = min(effective_yaw)
                yaw_max, yaw_min = check_left(yaw_max, yaw_min)
            else:
                yaw_max = min(effective_yaw)
                yaw_min = max(effective_yaw)
                yaw_max, yaw_min = check_right(yaw_max, yaw_min)
        elif maneuver[0] == "ESC_ConstantRadius":
            yaw_peak_05 = ""
            yaw_peak_1 = ""
            yaw_peak_2 = ""   
            yaw_peak_5 = ""
            yaw_min_05 = ""
            yaw_min_1 = ""
            yaw_min_2 = ""   
            yaw_min_5 = ""
            yawrate_rms_05 = ""
            yawrate_rms_1 = ""
            yawrate_rms_2 = ""
            yawrate_rms_5 = ""
            yawrate_rms = ""
            theorical_yaw = (data[0][maneuver[base][0]: maneuver[base][1]]/initial_radius)*180/math.pi
            theorical_plot = (data[0][maneuver[2][0] - int(round(0.5*frequency, 0)): maneuver[2][1]]/initial_radius)*180/math.pi
            effective_yaw = effective_yaw - theorical_yaw
            if mean_effective_yaw > 0:
                yaw_max = max(effective_yaw)
                yaw_min = min(effective_yaw)
                yaw_max, yaw_min = check_left(yaw_max, yaw_min)
            else:
                yaw_max = min(effective_yaw)
                yaw_min = max(effective_yaw)
                yaw_max, yaw_min = check_right(yaw_max, yaw_min)
        else:
            theorical_plot = ""
            found = False
            if maneuver[base][0] + int(round(0.5*frequency, 0)) <= maneuver[base][1]:
                yaw_peak_05 = max(effective_yaw[0: int(round(0.5*frequency, 0))])
                yaw_min_05 = min(effective_yaw[0: int(round(0.5*frequency, 0))])
                yaw_peak_05, yaw_min_05 = check_left(yaw_peak_05, yaw_min_05)
                yawrate_rms_05 = np.sqrt(1/len(effective_yaw[0: int(round(0.5*frequency, 0))])*np.sum(effective_yaw[0: int(round(0.5*frequency, 0))]**2))
                found = True
            if not found:
                yaw_peak_05 = ""
                yaw_min_05 = ""
                yawrate_rms_05 = ""
 
            found = False
            if maneuver[base][0] + frequency <= maneuver[base][1]:
                yaw_peak_1 = max(effective_yaw[0: int(frequency)])
                yaw_min_1 = min(effective_yaw[0: int(frequency)])
                yaw_peak_1, yaw_min_1 = check_left(yaw_peak_1, yaw_min_1)
                yawrate_rms_1 = np.sqrt(1/len(effective_yaw[0: int(frequency)])*np.sum(effective_yaw[0: int(frequency)]**2))
                found = True
            if not found:
                yaw_peak_1 = ""
                yaw_min_1 = ""
                yawrate_rms_1 = ""

            found = False
            if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
                yaw_peak_2 = max(effective_yaw[0: int(round(2*frequency, 0))])
                yaw_min_2 = min(effective_yaw[0: int(round(2*frequency, 0))])
                yaw_peak_2, yaw_min_2 = check_left(yaw_peak_2, yaw_min_2)
                yawrate_rms_2 = np.sqrt(1/len(effective_yaw[0: int(2*frequency)])*np.sum(effective_yaw[0: int(2*frequency)]**2))
                found = True
            if not found:
                yaw_peak_2 = ""
                yaw_min_2 = ""
                yawrate_rms_2 = ""
            
            found = False
            if maneuver[base][0] + 5*frequency <= maneuver[base][1]:
                yaw_peak_5 = max(effective_yaw[0: int(5*frequency)])
                yaw_min_5 = min(effective_yaw[0: int(5*frequency)])
                yaw_peak_5, yaw_min_5 = check_left(yaw_peak_5, yaw_min_5)
                yawrate_rms_5 = np.sqrt(1/len(effective_yaw[0: int(5*frequency)])*np.sum(effective_yaw[0: int(5*frequency)]**2))
                found = True
            if not found:
                yaw_peak_5 = ""
                yaw_min_5 = ""
                yawrate_rms_5 = ""
            yaw_max = max(effective_yaw)
            yaw_min = min(effective_yaw)
            yaw_max, yaw_min = check_left(yaw_max, yaw_min)
        delta_yaw_max = max(np.abs(effective_yaw))
        yawrate_rms = np.sqrt(1/len(effective_yaw)*np.sum(effective_yaw**2))

        return yaw_peak_05, yaw_peak_1, yaw_peak_2, yaw_peak_5, yaw_max, yaw_min_05, yaw_min_1, yaw_min_2, yaw_min_5, yaw_min, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_bigol_yaw, theorical_plot, effective_plot