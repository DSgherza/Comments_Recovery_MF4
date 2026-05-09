import numpy as np
class AdherencePerformances:
    def adherence_road(self, dictionaries, maneuver):
        corners = ["FL", "FR", "RL", "RR"]
        sample_FL = []
        sample_FR = []
        sample_RL = []
        sample_RR = []
        samples_ABS = [sample_FL, sample_FR, sample_RL, sample_RR]
        for j in range(len(corners)):
            for i in range(maneuver[2][0], maneuver[2][1] + 1):
                if dictionaries.objectives["ABSTrigger_" + corners[j]][i] > 0.5:
                    samples_ABS[j].append(i)
        overall_ABS_samples = list(set(sample_FL) & set(sample_FR) & set(sample_RL) & set(sample_RR))
        if overall_ABS_samples == []:
            adh_road = ""
        else:
            ABS_start_end = []
            mean_adh_list = []
            counter_initial = overall_ABS_samples[0]
            for i in range(1, len(overall_ABS_samples)):
                if overall_ABS_samples[i] != overall_ABS_samples[i-1] + 1:
                    counter_final = overall_ABS_samples[i-1]
                    ABS_start_end.append([counter_initial, counter_final])
                    counter_initial = overall_ABS_samples[i]
                if i == len(overall_ABS_samples) - 1:
                    counter_final = overall_ABS_samples[i]
                    ABS_start_end.append([counter_initial, counter_final])
            for i in range(len(ABS_start_end)):
                if dictionaries.time_resampled[ABS_start_end[i][1]] - dictionaries.time_resampled[ABS_start_end[i][0]] >= 0.15:
                    mean_adh_list.append(np.mean(np.mean([dictionaries.objectives["Adherence_FL"][ABS_start_end[i][0]: ABS_start_end[i][1]], dictionaries.objectives["Adherence_FR"][ABS_start_end[i][0]: ABS_start_end[i][1]], dictionaries.objectives["Adherence_RL"][ABS_start_end[i][0]: ABS_start_end[i][1]], dictionaries.objectives["Adherence_RR"][ABS_start_end[i][0]: ABS_start_end[i][1]]])))
            sum_adh = 0
            if len(mean_adh_list) > 0:
                for item in mean_adh_list:
                    sum_adh = sum_adh + item
                adh_road = sum_adh/len(mean_adh_list)
            else:
                adh_road = ""
        return adh_road

    def adherence_usage(self, dictionaries, maneuver, reference_speed):
        if "ReferenceSpeed_ms" not in dictionaries.objectives:
            reference_speed = "VehicleSpeed"
        if "Adherence_FL" in dictionaries.objectives and reference_speed + "_ms" in dictionaries.objectives:
            i = maneuver[2][0]
            try:
                while dictionaries.objectives[reference_speed + "_ms"][i] > 0.8*dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]]:
                    i += 1
                sample_initial = i
                while dictionaries.objectives[reference_speed + "_ms"][i] > 0.1*dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]]:
                    i += 1
                sample_final = i
                adh_usage = abs(np.mean(100*dictionaries.objectives["Ax"][sample_initial:sample_final]/(10*np.mean([dictionaries.objectives["Adherence_FL"][sample_initial: sample_final], dictionaries.objectives["Adherence_FR"][sample_initial: sample_final], dictionaries.objectives["Adherence_RL"][sample_initial: sample_final], dictionaries.objectives["Adherence_RR"][sample_initial: sample_final]]))))
                adh_usage_FL = abs(np.mean(100*dictionaries.objectives["Ax"][sample_initial:sample_final]/(10*np.mean(dictionaries.objectives["Adherence_FL"][sample_initial: sample_final]))))
                adh_usage_FR = abs(np.mean(100*dictionaries.objectives["Ax"][sample_initial:sample_final]/(10*np.mean(dictionaries.objectives["Adherence_FR"][sample_initial: sample_final]))))
                adh_usage_RL = abs(np.mean(100*dictionaries.objectives["Ax"][sample_initial:sample_final]/(10*np.mean(dictionaries.objectives["Adherence_RL"][sample_initial: sample_final]))))
                adh_usage_RR = abs(np.mean(100*dictionaries.objectives["Ax"][sample_initial:sample_final]/(10*np.mean(dictionaries.objectives["Adherence_RR"][sample_initial: sample_final]))))
            except IndexError:
                adh_usage = ""
                adh_usage_FL = ""
                adh_usage_FR = ""
                adh_usage_RL = ""
                adh_usage_RR = ""
        else:
            adh_usage = ""
            adh_usage_FL = ""
            adh_usage_FR = ""
            adh_usage_RL = ""
            adh_usage_RR = ""

        return adh_usage, adh_usage_FL, adh_usage_FR, adh_usage_RL, adh_usage_RR
    
    def adherence_ABS(self, dictionaries, maneuver, corner):
        if "ABSTrigger_FL" in dictionaries.objectives:
            i = 0
            try:
                while dictionaries.objectives["ABSTrigger_" + corner][maneuver[2][0]: maneuver[2][1]][i] < 0.5:
                    i += 1
                road_adh = dictionaries.objectives["Adherence_" + corner][maneuver[2][0] + i]
            except IndexError:
                road_adh = ""
        else:
            road_adh = ""
        return road_adh
    
    def max_slip_adherence(self, dictionaries, maneuver, corner, reference_speed): 
        if reference_speed + "_ms" in dictionaries.objectives:
            if "ESC_Handling" != maneuver[0]:
                for i in range(maneuver[2][0], maneuver[2][1]):
                    time_counter = maneuver[2][1]
                    if dictionaries.objectives[reference_speed + "_ms"][i] < 15/3.6:
                        time_counter = i-1
                        break
            else:
                time_counter = maneuver[2][1]
            wheel_slip_int = (dictionaries.objectives["WheelSpeed_" + corner + "_ms"][maneuver[2][0]: time_counter] - dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter])/dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter]
            wheel_slip_int = wheel_slip_int[~np.isnan(wheel_slip_int)]
            try:
                slip_max = np.min(wheel_slip_int)
                slip_mean = np.mean(wheel_slip_int)
                speed = dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter]#[abs_sign > 0.5]
                speed_at_max = speed[np.argmin(wheel_slip_int)]*3.6
            except ValueError:
                slip_max = ""
                slip_mean = ""
                speed_at_max = ""
        else:
            slip_max = ""
            slip_mean = ""
            speed_at_max = ""
        return slip_max, slip_mean, speed_at_max

    def correct_adherence_estimation(self, dictionaries, maneuver, corner):
        if "ABSTrigger_FL" in dictionaries.objectives:
            adh_high = 1.201 #per 0.6: fascia 0.8-0.5 #per 0.2 fascia 0.4-0.1, per 1: fascia 1.2-0.9
            adh_low = 0.799 #default 1.201 high, 0.799 low
            found = False
            abs_found = False
            for i in range(len(dictionaries.objectives["ABSTrigger_" + corner][maneuver[2][0]: maneuver[2][1]])):
                if dictionaries.objectives["ABSTrigger_" + corner][maneuver[2][0] + i] > 0.5:
                    start = maneuver[2][0] + i
                    abs_found = True
                    break
            time_counter = maneuver[2][1]
            if abs_found:
                if dictionaries.objectives["ABSTrigger_" + corner][maneuver[2][1]] < 0.5:
                    while dictionaries.objectives["ABSTrigger_" + corner][time_counter] < 0.5:
                        time_counter -= 1
                    end = time_counter
                else:
                    end = time_counter
                for i in range(len(dictionaries.objectives["Adherence_" + corner][start: end])):
                    if dictionaries.objectives["Adherence_" + corner][start + i] < adh_high and dictionaries.objectives["Adherence_" + corner][start + i] > adh_low:
                        adherence_delay = (dictionaries.time_resampled[start + i] - dictionaries.time_resampled[start])*1000
                        found = True
                        break
                if not found:
                    adherence_delay = "Not found"
                    correct_ext = 0
                else:
                    count = 0
                    for i in range(len(dictionaries.objectives["Adherence_" + corner][start: end])):
                        if dictionaries.objectives["Adherence_" + corner][start + i] < adh_high and dictionaries.objectives["Adherence_" + corner][start + i] > adh_low:
                            count += 1
                    correct_ext = count/len(dictionaries.objectives["Adherence_" + corner][start: end])*100
            else:
                correct_ext = ""
                adherence_delay = ""
        else:
            correct_ext = ""
            adherence_delay = ""
        return adherence_delay, correct_ext
