import numpy as np
import math

class LongitudinalPerformance:
    def stopping_distance_sv_norm(self, maneuvre_list, objective, v_nominal, reference_string):
        time_counter = maneuvre_list[2][0]
        found = False
        while objective.objectives[reference_string + "_ms"][time_counter] >= (5/3.6): 
            time_counter += 1
            if time_counter >= maneuvre_list[2][1]:
                break
        if time_counter < maneuvre_list[2][1]:
            found = True
            sample_v2 = time_counter
        if found:
            s_new = 0
            interesting_time = objective.time_resampled[maneuvre_list[2][0]:sample_v2]
            interesting_array = objective.objectives[reference_string + "_ms"][maneuvre_list[2][0]:sample_v2]
            for i in range(1, len(interesting_time)):
                s_new = s_new + interesting_array[i-1]*(interesting_time[i]-interesting_time[i-1])
            a = (pow(objective.objectives[reference_string + "_ms"][maneuvre_list[2][0]], 2) - pow(5/3.6, 2))/(2*s_new)
            sv_norm = pow(v_nominal/3.6, 2)/(2*a)
        else:
            sv_norm = ""
            sample_v2 = ""
        return sv_norm, sample_v2
    
    def stopping_distance_sl_v1_norm(self, v_nominal, objective, maneuvre_list, sample_v2, reference_string):
        time_counter = maneuvre_list[2][0]
        while objective.objectives[reference_string + "_ms"][time_counter] >= 0.9*v_nominal/3.6:
            time_counter += 1
        sample_v1 = time_counter
        sl = 0
        interesting_time = objective.time_resampled[sample_v1:sample_v2]
        interesting_array = objective.objectives[reference_string + "_ms"][sample_v1:sample_v2]
        for i in range(1, len(interesting_time)):
            sl = sl + interesting_array[i-1]*(interesting_time[i]-interesting_time[i-1])
        al = (pow(objective.objectives[reference_string + "_ms"][sample_v1], 2) - pow(5/3.6, 2))/(2*sl)
        slv1_norm = pow(0.9*v_nominal/3.6, 2)/(2*al)
        return slv1_norm

    def stopping_distance_sfv_v1_norm(self, sv_norm, slv1_norm):
        return sv_norm - slv1_norm
    
    def mfdd(self, initial_speed, objective, maneuvre_list, reference_string):
        time_counter = maneuvre_list[2][0]
        mfdd = 0
        sample_v08 = 0
        sample_v01 = 0
        try:
            while objective.objectives[reference_string + "_ms"][time_counter] >= 0.8*initial_speed/3.6 and initial_speed > 1:
                time_counter += 1
            sample_v08 = time_counter
        except IndexError:
            mfdd = ""
        try:
            while objective.objectives[reference_string + "_ms"][time_counter] >= 0.1*initial_speed/3.6 and initial_speed > 1:
                time_counter += 1
                if time_counter > maneuvre_list[2][1]:
                    break
            sample_v01 = time_counter
        except IndexError:
            mfdd = ""
        if mfdd == 0:
            if sample_v01 < maneuvre_list[2][1] and sample_v01 != maneuvre_list[2][0]:
                s_mfdd = 0
                interesting_time = objective.time_resampled[sample_v08:sample_v01]
                interesting_array = objective.objectives[reference_string + "_ms"][sample_v08:sample_v01]
                for i in range(1, len(interesting_time)):
                    s_mfdd = s_mfdd + interesting_array[i-1]*(interesting_time[i]-interesting_time[i-1])
                mfdd = (pow(0.8*initial_speed, 2) - pow(0.1*initial_speed, 2))/(25.92*s_mfdd)
            else:
                mfdd = ""
        return mfdd, sample_v08, sample_v01
    
    def rms_ax(self, initial_speed, objective, maneuvre_list, reference_string):
        time_counter = maneuvre_list[2][0]
        try:
            while objective.objectives[reference_string + "_ms"][time_counter] >= 0.8*initial_speed/3.6 and initial_speed > 1:
                time_counter += 1
            sample_v08 = time_counter
            while objective.objectives[reference_string + "_ms"][time_counter] >= 0.1*initial_speed/3.6 and initial_speed > 1:
                time_counter += 1
                if time_counter > maneuvre_list[2][1]:
                    break
            sample_v01 = time_counter
            if sample_v01 < maneuvre_list[2][1] and sample_v01 != maneuvre_list[2][0]:
                ax_rms = np.sqrt(1/len(objective.objectives["Ax"][sample_v08: sample_v01])*np.sum(objective.objectives["Ax"][sample_v08: sample_v01]**2))
            else:
                ax_rms = ""
        except IndexError:
            ax_rms = ""
        return ax_rms
    
    def long_dec_init_peak(self, signal, speed, mfdd):
        time_counter = 0
        found = False
        long_dec_1st_peak = ""
        while not found:
            try:
                while abs(signal[time_counter] - signal[time_counter + 1]) < 0.05:
                    time_counter += 1
                while abs(signal[time_counter] - signal[time_counter + 1]) >= 0.05:
                    time_counter += 1
            except IndexError:
                pass
                found = True
            if mfdd != "":
                if abs(signal[time_counter]) >= 0.8*abs(mfdd):
                    found = True
                    long_dec_1st_peak = signal[time_counter]
            else:
                long_dec_1st_peak = signal[time_counter]
                found = True
        return long_dec_1st_peak, signal[time_counter:-1], speed[time_counter:-1]

    def long_max_dec(self, signal, speed):
        time_counter = 0
        try:
            while speed[time_counter] <= 5/3.6:
                time_counter += 1
            while speed[time_counter] > 5/3.6:
                time_counter += 1
            sample_v5 = time_counter
            long_max_dec = np.min(signal[0:sample_v5])
            long_max_acc = np.max(signal[0:sample_v5])
        except IndexError:
            long_max_dec = np.min(signal)
            long_max_acc = np.max(signal)
        if long_max_acc < 0.1:
            long_max_acc = ""
        return long_max_dec, long_max_acc
    
    def long_min_dec(self, signal, speed, initial_speed, long_dec_first_peak):
        if long_dec_first_peak != "":
            time_counter = 0
            try:
                while speed[time_counter] > 0.1*initial_speed/3.6:
                    time_counter += 1
                sample_v01 = time_counter
                long_min_dec = np.max(signal[0:sample_v01])
            except IndexError:
                try:
                    long_min_dec = np.max(signal)
                except ValueError:
                    long_min_dec = ""
            except ValueError:
                long_min_dec = ""
        else:
            long_min_dec = ""
        return long_min_dec
    
    def ninenty_perc_ax_first_peak(self, maneuver, dictionary, ax_first_peak):
        time_counter = maneuver[2][0]
        if ax_first_peak != "":
            while abs(dictionary.objectives["Ax"][time_counter]) <= 0.9*abs(ax_first_peak):
                time_counter += 1
            ninenty = (dictionary.time_resampled[time_counter] - dictionary.time_resampled[maneuver[2][0]])*1000
        else:
            ninenty = ""
        return ninenty
    
    def accuracy_dec(self, maneuver, dictionary, pedal_type, decel_string = "SatDecelReq"):
        #controllare quale segnale va preso in considerazione come decelreq.
        #Le priorità dovrebbero essere SatDecelReq, DecelReq, BPDecelReq.
        #Controllare anche per B1.
        #Cosa fare quando decel_req è zero?
        decel = []
        if pedal_type == "SLOW" and "ABS_Trigger_FL" in dictionary.objectives:
            time_counter = maneuver[2][0]
            while time_counter <= maneuver[2][1] and (dictionary.objectives["ABSTrigger_FR"][time_counter] < 0.5 and dictionary.objectives["ABSTrigger_FL"][time_counter] < 0.5 and dictionary.objectives["ABSTrigger_RR"][time_counter] < 0.5 and dictionary.objectives["ABSTrigger_RL"][time_counter] < 0.5):
                if dictionary.objectives[decel_string][time_counter] > 0.1:
                    decel.append(abs(dictionary.objectives["Ax"][time_counter])/(dictionary.objectives[decel_string][time_counter]*9.81))
                time_counter += 1

            mean_decel = 100*np.mean(np.array(decel))
        else:
            mean_decel = ""
        return mean_decel
    
    def vibration_detector(self, amplitude, frequency, signal, times, start, end):
        time_counter = start
        peaks = []
        peaks_times = []
        peaks_type = []
        peak_find = True
        while time_counter <= end:
            while abs(signal[time_counter] - signal[time_counter + 1]) < 0.05 and time_counter <= end:
                time_counter += 1
            while abs(signal[time_counter] - signal[time_counter + 1]) >= 0.05 and time_counter <= end:
                time_counter += 1
            peaks.append(signal[time_counter])
            peaks_times.append(times[time_counter])
            if signal[time_counter - 1] - signal[time_counter] > 0:
                peaks_type.append("HIGH")
            else:
                peaks_type.append("LOW")
        try:
            for i in range(len(peaks_type)):
                if peaks_type[i] == peaks_type[i+1]:
                    peaks_type[i] = 2
                    peaks_times[i] = 2
                    peaks[i] = 2
        except IndexError:
            pass
        peaks_times = list(filter((2).__ne__, peaks_times))
        peaks_type = list(filter((2).__ne__, peaks_type))
        peaks = list(filter((2).__ne__, peaks))
        vib_dect = "False"
        if peaks_times == []:
            peak_find = False
        if peak_find:
            for i in range(4, len(peaks_times)):
                if (1/((peaks_times[i] - peaks_times[i-4])/3)) > frequency:
                    if abs(peaks[i] - peaks[i-1]) > amplitude and abs(peaks[i-1] - peaks[i-2]) > amplitude and abs(peaks[i-2] - peaks[i-3]) > amplitude and abs(peaks[i-3] - peaks[i-4]) > amplitude:
                        vib_dect = "True"
                        break
        return vib_dect
    
    def mu(self, dictionaries, maneuvers, reference_string_speed, initial_speed, let, front_act_pos_ratio_graph, rear_act_pos_ratio_graph, mu_graph):
        time_counter = maneuvers[2][0]
        final_speed = dictionaries.objectives[reference_string_speed + "_kmh"][maneuvers[2][1]]
        found = True
        try:
            while dictionaries.objectives[reference_string_speed + "_kmh"][time_counter] > 0.9*initial_speed:
                time_counter += 1
            start = time_counter
            while dictionaries.objectives[reference_string_speed + "_kmh"][time_counter] > (final_speed + 0.1*final_speed) and dictionaries.objectives[reference_string_speed + "_kmh"][time_counter] > 10:
                time_counter += 1
            end = time_counter
        except IndexError:
            found = False
        if found and not math.isnan(dictionaries.objectives["Coasting"]) and "ForceFeedback_FL" in dictionaries.objectives:
            dec = abs(dictionaries.objectives["Ax"][start:end])
            coasting = dictionaries.objectives["Coasting"]
            eff_dec = dec - coasting
            weight = dictionaries.objectives["Weight"]
            roll_rad_FA = dictionaries.objectives["RollingRadius_FA"]
            roll_rad_RA = dictionaries.objectives["RollingRadius_RA"]
            roll_rad_avg = (roll_rad_FA + roll_rad_RA)/2
            num = eff_dec*weight*roll_rad_avg
            yld = dictionaries.objectives["Yield"]
            eff_rad_FA = dictionaries.objectives["EffectiveRadius_FA"]
            eff_rad_RA = dictionaries.objectives["EffectiveRadius_RA"]
            ff_FL = dictionaries.objectives["ForceFeedback_FL"][start:end]*1000
            ff_FR = dictionaries.objectives["ForceFeedback_FR"][start:end]*1000
            ff_RL = dictionaries.objectives["ForceFeedback_RL"][start:end]*1000
            ff_RR = dictionaries.objectives["ForceFeedback_RR"][start:end]*1000
            try:
                ff_FA_avg = (ff_FL + ff_FR)/2
                ff_RA_avg = (ff_RL + ff_RR)/2
                den = 4*yld*(ff_FA_avg*eff_rad_FA + ff_RA_avg*eff_rad_RA)
                mu = np.mean(num/den)
            except ValueError:
                mu = "ACQUISITION ERROR"
        else:
            mu = ""
        if "ForceFeedback_FL" in dictionaries.objectives and "ForceFeedback_FR" in dictionaries.objectives and (mu != "" and mu != "ACQUISITION ERROR"):
            ff_FL = np.mean(dictionaries.objectives["ForceFeedback_FL"][start:end]*1000)
            ff_FR = np.mean(dictionaries.objectives["ForceFeedback_FR"][start:end]*1000)
            fr_force_ratio = ff_FL/ff_FR*100
        else:
            fr_force_ratio = "ACQUISITION ERROR"
        if "ForceFeedback_RL" in dictionaries.objectives and "ForceFeedback_RR" in dictionaries.objectives and (mu != "" and mu != "ACQUISITION ERROR"):
            ff_RL = np.mean(dictionaries.objectives["ForceFeedback_RL"][start:end]*1000)
            ff_RR = np.mean(dictionaries.objectives["ForceFeedback_RR"][start:end]*1000)
            re_force_ratio = ff_RL/ff_RR*100
        else:
            re_force_ratio = "ACQUISITION ERROR"
        if "S_FL_BBW_Act" in dictionaries.objectives and "S_FR_BBW_Act" in dictionaries.objectives and (mu != "" and mu != "ACQUISITION ERROR"):
            s_FL = np.mean(dictionaries.objectives["S_FL_BBW_Act"][start:end]*1000)
            s_FR = np.mean(dictionaries.objectives["S_FR_BBW_Act"][start:end]*1000)
            fr_pos_ratio = s_FL/s_FR*100
        else:
            fr_pos_ratio = "ACQUISITION ERROR"
        if "S_RL_BBW_Act" in dictionaries.objectives and "S_RR_BBW_Act" in dictionaries.objectives and (mu != "" and mu != "ACQUISITION ERROR"):
            s_RL = np.mean(dictionaries.objectives["S_RL_BBW_Act"][start:end]*1000)
            s_RR = np.mean(dictionaries.objectives["S_RR_BBW_Act"][start:end]*1000)
            re_pos_ratio = s_RL/s_RR*100
        else:
            re_pos_ratio = "ACQUISITION ERROR"
        if let.get() == 1:
            front_act_pos_ratio_graph.append(fr_pos_ratio)
            rear_act_pos_ratio_graph.append(re_pos_ratio)
            mu_graph.append(mu)
        return mu, fr_force_ratio, re_force_ratio, fr_pos_ratio, re_pos_ratio 
    
    def jerk_long_max(self, dictionaries, maneuvers, reference_string_speed):
        if "ABS" in maneuvers[0]:
            time_counter = maneuvers[2][0]
            max_jerk_long = 0
            jerk_rms = 0
            try:
                while dictionaries.objectives[reference_string_speed + "_kmh"][time_counter] > 10:
                    if abs(dictionaries.objectives["AxDer"][time_counter]) > max_jerk_long:
                        max_jerk_long = abs(dictionaries.objectives["AxDer"][time_counter])
                    time_counter += 1
                    jerk_rms = jerk_rms + (dictionaries.objectives["AxDer"][time_counter])**2
                try:
                    jerk_rms = np.sqrt((1/(time_counter - maneuvers[2][0]))*jerk_rms)
                except ZeroDivisionError:
                    jerk_rms = 0
            except IndexError:
                max_jerk_long = ""
                jerk_rms = ""
        elif "ESC_PartialBrkinTurn" == maneuvers[0] or "TCS" in maneuvers[0]:
            time_counter = maneuvers[2][0]
            max_jerk_long = 0
            jerk_rms = 0
            while time_counter <= maneuvers[2][1]:
                if abs(dictionaries.objectives["AxDer"][time_counter]) > max_jerk_long:
                    max_jerk_long = abs(dictionaries.objectives["AxDer"][time_counter])
                time_counter += 1
                jerk_rms = jerk_rms + (dictionaries.objectives["AxDer"][time_counter])**2
            try:
                jerk_rms = np.sqrt((1/(time_counter - maneuvers[2][0]))*jerk_rms)
            except ZeroDivisionError:
                jerk_rms = 0
        elif "ESC_Handling" == maneuvers[0]:
            max_jerk_long = ""
            jerk_rms = ""
        elif "ESC" in maneuvers[0] and "ESC_Handling" != maneuvers[0] and "ESC_PartialBrkinTurn" != maneuvers[0]:
            time_counter = maneuvers[3][0]
            max_jerk_long = 0
            jerk_rms = 0
            while time_counter <= maneuvers[3][1]:
                if abs(dictionaries.objectives["AxDer"][time_counter]) > max_jerk_long:
                    max_jerk_long = abs(dictionaries.objectives["AxDer"][time_counter])
                time_counter += 1            
                jerk_rms = jerk_rms + (dictionaries.objectives["AxDer"][time_counter])**2
            try:
                jerk_rms = np.sqrt((1/(time_counter - maneuvers[2][0]))*jerk_rms)
            except ZeroDivisionError:
                jerk_rms = 0
        return max_jerk_long, jerk_rms
    
    def ax_pos_peak(self, dictionaries, maneuvers):
        return round(max(dictionaries.objectives["Ax"][maneuvers[2][0]: maneuvers[2][1]]), 2)  

        
        



        

