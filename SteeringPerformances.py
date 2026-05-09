import numpy as np

class SteeringPerformances:
    def steering_maneuver(self, maneuver: list, data: list, frequency:int, base:int):
        steering_initial_maneuver = np.mean(data[0][(maneuver[base][0] - int(round(0.5*frequency))): maneuver[base][0]])
        eff_data = data[0] - steering_initial_maneuver

        found = False
        if maneuver[base][0] + frequency <= maneuver[base][1]:
            swa_peak_1 = max(np.abs(eff_data[maneuver[base][0]: int(maneuver[base][0] + frequency)]))*np.sign(data[0][maneuver[base][0] + np.argmax(np.abs(data[0][maneuver[base][0]: int(maneuver[base][0] + frequency)]))])
            found = True
        if not found:
            swa_peak_1 = ""
 
        found = False
        if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
            swa_peak_2 = max(np.abs(eff_data[maneuver[base][0]: int(maneuver[base][0] + 2*frequency)]))*np.sign(data[0][maneuver[base][0] + np.argmax(np.abs(data[0][maneuver[base][0]: int(maneuver[base][0] + 2*frequency)]))])
            found = True
        if not found:
            swa_peak_2 = ""

        swa_peak = max(np.abs(eff_data[maneuver[base][0]: maneuver[base][1]]))*np.sign(data[0][maneuver[base][0] + np.argmax(np.abs(data[0][maneuver[base][0]: maneuver[base][1]]))])
    
        found = False
        if maneuver[base][0] + frequency <= maneuver[base][1]:
            swa_spd_peak_1 = max(np.abs(data[1][maneuver[base][0]: int(maneuver[base][0] + frequency)]))*np.sign(data[1][maneuver[base][0] + np.argmax(np.abs(data[1][maneuver[base][0]: int(maneuver[base][0] + frequency)]))])
            found = True
        if not found:
            swa_spd_peak_1 = ""
 
        found = False
        if maneuver[base][0] + 2*frequency <= maneuver[base][1]:
            swa_spd_peak_2 = max(np.abs(data[1][maneuver[base][0]: int(maneuver[base][0] + 2*frequency)]))*np.sign(data[1][maneuver[base][0] + np.argmax(np.abs(data[1][maneuver[base][0]: int(maneuver[base][0] + 2*frequency)]))])
            found = True
        if not found:
            swa_spd_peak_2 = ""

        swa_spd_peak = max(np.abs(data[1][maneuver[base][0]: maneuver[base][1]]))*np.sign(data[1][maneuver[base][0] + np.argmax(np.abs(data[1][maneuver[base][0]: maneuver[base][1]]))])
        
        return steering_initial_maneuver, swa_peak_1, swa_peak_2, abs(swa_peak), swa_spd_peak_1, swa_spd_peak_2, abs(swa_spd_peak) 