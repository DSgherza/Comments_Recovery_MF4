import pandas as pd
import numpy as np
from BrakePerfromance import BrakePerformance
from SpeedPerformance import SpeedlPerformance
from LongitudinalPerformance import LongitudinalPerformance
from LateralPerformance import LateralPerformance
from YawRatePerformance import YawRatePerformance
from SteeringPerformances import SteeringPerformances
from SlipPerformances import SlipPerformances
from AdherencePerformances import AdherencePerformances
from TCSPerformances import TCSPerformances
from SlipRepartition import SlipRepartition
from ReactionPerformance import ReactionPerformance
from FlagDetection import FlagDetection
from Overall import Overall
from Sensorless import Sensorless
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import os
from matplotlib.ticker import MultipleLocator, AutoMinorLocator
 
def dataframe_creation(parameters: list, maneuvres: list, rows: int) -> pd.DataFrame:
    return pd.DataFrame(parameters, columns = maneuvres, index = rows)
 
def time_at_sample(item: list, dictionaries: dict, base: int, sample: int):
    """ Consente di trovare il tempo a cui corrisponde un determinato campione"""
    parameter = dictionaries.time_resampled[item[base][sample]]
    return parameter
 
def property_at_sample(maneuvres: list, dictionaries: dict, property: str, base: int, sample: int) -> list:
    """ Consente di trovare una proprietà ad un determinato campione"""
    output = dictionaries.objectives[property][maneuvres[base][sample]]
    return output
 
def signal_fragment_recovery(maneuvres: list, dictionaries: dict, property: str, base: int) -> list:
    """ Consente di recuperare un pezzo di un determinato segnale, fra sample on e sample off"""
    fragment = []
    time_counter = maneuvres[base][0]
    while time_counter <= maneuvres[base][1]:
        fragment.append(dictionaries.objectives[property][time_counter])
        time_counter += 1
    fragment_array = np.array(fragment)
    return fragment_array

def integral(time: np.array, signal: np.array, start:int, end:int):
    s = 0
    interesting_time = time[start:end]
    interesting_array = signal[start:end]
    for i in range(1, len(interesting_time)):
        s = s + interesting_array[i-1]*(interesting_time[i]-interesting_time[i-1])
    return s

def zero_intersection(signal: np.array):
    zero = 0
    for i in range(len(signal)):
        try:
            if np.sign(signal[i]) != np.sign(signal[i+1]):
                zero += 1
        except IndexError:
            pass
    return zero
 
class PerformanceParameterAssigment(BrakePerformance, SpeedlPerformance, LongitudinalPerformance, LateralPerformance, YawRatePerformance, FlagDetection,
                                    SteeringPerformances, SlipPerformances, AdherencePerformances, TCSPerformances, SlipRepartition, ReactionPerformance,
                                    Overall, Sensorless):
   
    def __init__(self, maneuvres, dictionaries, check_list_slip, direction_check, target_vs_real_speed_check, target_check, let, file, saving_folder):
        parameters_list = []
        excel_bigol_list = []
        self.maneuvers_times(maneuvres, dictionaries, parameters_list, excel_bigol_list)
        pedal_type = self.brake_performance(maneuvres, dictionaries, parameters_list, excel_bigol_list)
        v_nominal, control, precise_initial_speed = self.speed_performance(maneuvres, dictionaries, parameters_list, excel_bigol_list, target_vs_real_speed_check, target_check)
        self.v_nominal = v_nominal
        self.longitudinal_performances(maneuvres, dictionaries, v_nominal, parameters_list, control, precise_initial_speed, pedal_type, excel_bigol_list, let, file, saving_folder)
        initial_radius = self.lateral_performances(maneuvres, dictionaries, parameters_list, direction_check, excel_bigol_list)
        self.yaw_rate_performance(maneuvres, dictionaries, initial_radius, parameters_list, direction_check, excel_bigol_list)
        self.steering_performances(maneuvres, dictionaries, parameters_list)
        self.dynamic_performances(dictionaries, maneuvres, parameters_list, direction_check)
        self.roll_rate(dictionaries, maneuvres, parameters_list, excel_bigol_list)
        self.TCS_performances(dictionaries, maneuvres, parameters_list)
        self.slip_repartition(maneuvres, dictionaries, check_list_slip, parameters_list)
        self.slip_performances(maneuvres, dictionaries, parameters_list)
        self.adherence_performances(dictionaries, maneuvres, parameters_list)
        self.reaction_performances(dictionaries, maneuvres, parameters_list, pedal_type)
        self.speed_estimation(maneuvres, dictionaries, parameters_list)
        self.flag_detection(dictionaries, parameters_list, maneuvres.maneuvre)
        self.sensorless_estimators(dictionaries, parameters_list, maneuvres.reference_string_speed, maneuvres.maneuvre)
        self.overall(maneuvres.maneuvre, dictionaries, maneuvres.reference_string_speed, parameters_list)
        maneuvres_list = []
        for i in range(len(maneuvres.maneuvre)):
            maneuvres_list.append(maneuvres.maneuvre[i][0])
        parameters_names = []
        for i in range(len(parameters_list)):
            parameters_names.append(parameters_list[i].pop(0))
        self.parameters_df = dataframe_creation(parameters_list, maneuvres_list, parameters_names)
        self.excel_bigol_list = excel_bigol_list

    def maneuvers_times (self, maneuvres, dictionaries, parameters_list, excel_bigol_list):
        maneuver_initial_time = ["Maneuver Initial Time"]
        maneuver_final_time = ["Maneuver Final Time"]
        maneuver_time = ["Maneuver Time"]
        cont = 0
        found = False
        for item in maneuvres.maneuvre:
            if "ABS" in item[0] or "TCS" in item[0] or "ESC_PartialBrkinTurn" == item[0] or "ESC_Handling" == item[0]:
                single_maneuver_initial_time = time_at_sample(item, dictionaries, 2, 0)
                maneuver_initial_time.append(round(single_maneuver_initial_time, 2))
                single_maneuver_final_time = time_at_sample(item, dictionaries, 2, 1)
                maneuver_final_time.append(round(single_maneuver_final_time, 2))
                maneuver_time.append(round(single_maneuver_final_time - single_maneuver_initial_time, 2))
                if "YawRate_degs" in dictionaries.objectives:
                    if "YawRate" in dictionaries.times:
                        if dictionaries.times["YawRate"][1] >= item[2][1]:
                            if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                found = True
                                excel_bigol_list.append([item[0]])
                                excel_bigol_list[cont].append(list((dictionaries.time_resampled[item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]) - dictionaries.time_resampled[item[2][0]]))
                                cont += 1
                    else:
                        if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                            found = True
                            excel_bigol_list.append([item[0]])
                            excel_bigol_list[cont].append(list((dictionaries.time_resampled[item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]) - dictionaries.time_resampled[item[2][0]]))
                            cont += 1
            else:
                single_maneuver_initial_time = time_at_sample(item, dictionaries, 3, 0)
                maneuver_initial_time.append(round(single_maneuver_initial_time, 2))
                single_maneuver_final_time = time_at_sample(item, dictionaries, 3, 1)
                maneuver_final_time.append(round(single_maneuver_final_time, 2))
                maneuver_time.append(round(single_maneuver_final_time - single_maneuver_initial_time, 2))
        if not found:
            excel_bigol_list.append([])
        for item in [maneuver_initial_time, maneuver_final_time, maneuver_time]:
            parameters_list.append(item)
 
    def brake_performance(self, maneuvres, dictionaries, parameters_list, excel_bigol_list):
        pedal_rate = ["Pedal Rate"]
        pedal_type = ["Pedal Type"]
        observer_list = [pedal_rate, pedal_type]
        cont = 0
        for item in maneuvres.maneuvre:
            if "BrakePedalPosition" in dictionaries.times:
                if dictionaries.times["BrakePedalPosition"][1] >= item[2][1]:
                    if "ABS" in item[0] or "ESC_PartialBrkinTurn" == item[0]:
                        single_pedal_rate = self.pedal_rate(item, dictionaries)
                        pedal_rate.append(single_pedal_rate)
                        pedal_type.append(self.pedal_type(single_pedal_rate))
                        if "YawRate_degs" in dictionaries.objectives:
                            if "YawRate" in dictionaries.times:
                                if dictionaries.times["YawRate"][1] >= item[2][1]:
                                    if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["BrakePedalPosition"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                            else:
                                if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["BrakePedalPosition"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                    else:      
                        for item in [pedal_rate, pedal_type]:
                            item.append("")
                else:
                    for i in range(len(observer_list)):
                        observer_list[i].append("ACQUISITION ERROR")
            else:
                if "ABS" in item[0] or "ESC_PartialBrkinTurn" == item[0]:
                    single_pedal_rate = self.pedal_rate(item, dictionaries)
                    pedal_rate.append(single_pedal_rate)
                    pedal_type.append(self.pedal_type(single_pedal_rate))
                    if "YawRate_degs" in dictionaries.objectives:
                        if "YawRate" in dictionaries.times:
                            if dictionaries.times["YawRate"][1] >= item[2][1]:
                                if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["BrakePedalPosition"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                        else:
                            if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                excel_bigol_list[cont].append(list(dictionaries.objectives["BrakePedalPosition"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                cont += 1
                else:      
                    for item in [pedal_rate, pedal_type]:
                        item.append("")
        for item in observer_list:
            parameters_list.append(item)
        return pedal_type
 
    def speed_performance(self, maneuvres, dictionaries, parameters_list, excel_bigol_list, target_vs_real_speed_check, target_check):
        v_nominal = ["Vnominal"]
        initial_speed = ["VehicleSpeed@DrivingInput"]
        final_speed = ["VehicleSpeed@End"]
        average_speed = ["Speed Avg"]
        max_speed =["Speed Max"]
        v_nominal_control = []
        precise_initial_speed = []
        i = 0
        reference_string_speed = maneuvres.reference_string_speed
        cont = 0
        for item in maneuvres.maneuvre:
            if "ESC_PartialBrkinTurn" == item[0] or "ABS" in item[0] or "TCS" in item[0]:
                nominal_speed, single_initial_speed, control = self.nominal_speed(item, dictionaries, 2, reference_string_speed[i], i)
                v_nominal.append(nominal_speed)
                initial_speed.append(round(single_initial_speed, 2))
                precise_initial_speed.append(single_initial_speed)
                v_nominal_control.append(control)
                target_vs_real_speed_check.append(control)
                target_check.append(True)
                final_speed.append(round(property_at_sample(item, dictionaries, reference_string_speed[i] + "_kmh", 2, 1), 2))
                average_speed.append("")
                max_speed.append("")
                if "YawRate_degs" in dictionaries.objectives:
                    if "YawRate" in dictionaries.times:
                        if dictionaries.times["YawRate"][1] >= item[2][1]:
                            if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                excel_bigol_list[cont].append(list(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                cont += 1
                    else:
                        if item[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                            excel_bigol_list[cont].append(list(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                            cont += 1
            elif "ESC" in item[0] and "ESC_Handling" != item[0]:
                nominal_speed, single_initial_speed, control = self.nominal_speed(item, dictionaries, 3, reference_string_speed[i], i)
                v_nominal.append(nominal_speed)
                target_vs_real_speed_check.append(control)
                target_check.append(True)
                initial_speed.append(round(single_initial_speed, 2))
                precise_initial_speed.append(single_initial_speed)
                v_nominal_control.append(control)
                final_speed.append(round(property_at_sample(item, dictionaries, reference_string_speed[i] + "_kmh", 3, 1), 2))
                average_speed.append("")
                if "ESC_ConstantRadius" == item[0]:
                    max_speed.append(round(max(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[3][0]: item[3][1]]), 2))
                else:
                    max_speed.append("")
            elif "ESC_Handling" == item[0]:
                target_vs_real_speed_check.append("")
                target_check.append(True)
                for ogg in [v_nominal, initial_speed, final_speed, precise_initial_speed, v_nominal_control]:
                    ogg.append("")
                average_speed.append(round(np.mean(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[2][0]: item[2][1]]), 2))
                max_speed.append(round(max(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[2][0]: item[2][1]]), 2))
            else:
                target_vs_real_speed_check.append("")
                target_check.append(True)
                for ogg in [v_nominal, initial_speed, final_speed, precise_initial_speed, v_nominal_control]:
                    ogg.append("")
                average_speed.append(round(np.mean(dictionaries.objectives[reference_string_speed[i] + "_kmh"][item[2][0]: item[2][1]]), 2))
                max_speed.append("")
            i += 1
        for item in [v_nominal, initial_speed, final_speed, average_speed, max_speed]:
            parameters_list.append(item)
        return v_nominal, v_nominal_control, precise_initial_speed
 
    def longitudinal_performances(self, maneuvres, dictionaries, v_nominal, parameters_list, control, initial_speed, pedal_type, excel_bigol_list, let, file, saving_folder):
        sv_norm = ["SV_norm"]
        sav_norm = ["SaV_norm"]
        sl_v1_norm = ["sLV1_norm"]
        sfv_v1_norm = ["sFV_V1_norm"]
        ax_vib = ["Ax_vibration_Flag"]
        long_dec_first_peak = ["dec_1stPeak"]
        long_dec_max = ["dec_peak"]
        mfdd = ["MFDD"]
        integral_ax_mfdd = ["Integral_abs(Ax-mfdd)"]
        rms_ax_mfdd = ["RMS_(Ax-mfdd)"]
        intersection_number = ["Zero_Intersection_(Ax-mfdd)"]
        ax_rms = ["RMS_Ax"]
        max_jerk_long = ["jerk_long_max"]
        jerk_long_rms = ["jerk_long_RMS"]
        long_dec_mean = ["Ax_avg"]
        long_dec_min = ["dec_min"] #calcolato, per ora, fino a 0.1*V0
        mfdd_ax_min_diff = ["Delta_dec_MFDD_Min"]
        diff_longitudinal_initial_peak_max = ["dec_MaxLoss_1stPeak_Min"]
        time_90_dec_initial_peak = ["TimeResponse_To90_perc_of_dec_first_peak"]
        dec_target_accuracy = ["DecelTargetAccuracy"]
        acc_peak = ["acc_peak"]
        mu = ["μ"]
        fr_act_pos_rat = ["FrontActPosRatio"]
        re_act_pos_rat = ["RearActPosRatio"]
        fr_act_for_rat = ["FrontActForceRatio"]
        re_act_for_rat = ["RearActForceRatio"]
        front_act_pos_ratio_graph = []
        rear_act_pos_ratio_graph = []
        mu_graph = []
        observer_list = [sv_norm, sav_norm, sl_v1_norm, sfv_v1_norm, mu, fr_act_pos_rat, re_act_pos_rat, fr_act_for_rat, re_act_for_rat, ax_vib, long_dec_max, acc_peak, long_dec_first_peak, ax_rms, max_jerk_long, jerk_long_rms, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, long_dec_mean, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]
        reference_string_speed = maneuvres.reference_string_speed
        i = 0
        cont = 0
        for item in maneuvres.maneuvre:
            i += 1
            if "Ax" in dictionaries.objectives:
                if "Ax" in dictionaries.times:
                    if dictionaries.times["Ax"][1] >= item[2][1]:
                        if "ABS" in item[0]:
                            acc_peak.append("")
                            single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                            if single_jerk_long_max != "":
                                max_jerk_long.append(round(single_jerk_long_max, 2))
                                jerk_long_rms.append(round(single_jerk_rms, 2))
                            else:
                                max_jerk_long.append(single_jerk_long_max)
                                jerk_long_rms.append(single_jerk_rms)
                            single_ax_rms = self.rms_ax(initial_speed[i-1], dictionaries, item, reference_string_speed[i-1])
                            single_mu, single_fr_force_ratio, single_re_force_ratio, single_fr_pos_ratio, single_re_pos_ratio = self.mu(dictionaries, item, reference_string_speed[i-1], initial_speed[i-1], let, front_act_pos_ratio_graph, rear_act_pos_ratio_graph, mu_graph)
                            ax_vib.append(self.vibration_detector(1.5, 10, dictionaries.objectives["Ax"], dictionaries.time_resampled, item[2][0], item[2][1]))
                            single_sv_norm, sample_v2 = self.stopping_distance_sv_norm(item, dictionaries, v_nominal[i], reference_string_speed[i-1])
                            if single_mu != "" and single_mu != "ACQUISITION ERROR":
                                mu.append(round(single_mu, 2))
                            else:
                                mu.append(single_mu)
                            if single_fr_force_ratio != "ACQUISITION ERROR":
                                fr_act_for_rat.append(round(single_fr_force_ratio, 2))
                            else:
                                fr_act_for_rat.append(single_fr_force_ratio)
                            if single_re_force_ratio != "ACQUISITION ERROR":
                                re_act_for_rat.append(round(single_re_force_ratio, 2))
                            else:
                                re_act_for_rat.append(single_re_force_ratio)
                            if single_fr_pos_ratio != "ACQUISITION ERROR":
                                fr_act_pos_rat.append(round(single_fr_pos_ratio, 2))
                            else:
                                fr_act_pos_rat.append(single_fr_pos_ratio)
                            if single_re_pos_ratio != "ACQUISITION ERROR":
                                re_act_pos_rat.append(round(single_re_pos_ratio, 2))
                            else:
                                re_act_pos_rat.append(single_re_pos_ratio)
                            if single_ax_rms != "":
                                ax_rms.append(round(single_ax_rms, 2))
                            else:
                                ax_rms.append(single_ax_rms)
                            if single_sv_norm != "":
                                sv_norm.append(round(single_sv_norm, 2))
                            else:
                                sv_norm.append(single_sv_norm)
                            if single_sv_norm != "" and control[i-1]:
                                sav_norm.append(round(single_sv_norm, 2))
                                single_sl_v1_norm = self.stopping_distance_sl_v1_norm(v_nominal[i], dictionaries, item, sample_v2, reference_string_speed[i-1])
                                sl_v1_norm.append(round(single_sl_v1_norm, 2))
                                sfv_v1_norm.append(round(self.stopping_distance_sfv_v1_norm(single_sv_norm, single_sl_v1_norm), 2))
                            else:
                                sav_norm.append("")
                                sl_v1_norm.append("")
                                sfv_v1_norm.append("")
                            tuple_results = self.mfdd(initial_speed[i-1], dictionaries, item, reference_string_speed[i-1])
                            single_mfdd = tuple_results[0]
                            start_mfdd = tuple_results[1]
                            end_mfdd = tuple_results[2]   
                            ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 2)
                            if single_mfdd != "":
                                ax_minus_mfdd = dictionaries.objectives["Ax"] + single_mfdd
                                abs_ax_minus_mfdd = abs(ax_minus_mfdd)
                                single_integral_ax_mfdd = integral(dictionaries.time_resampled, abs_ax_minus_mfdd, start_mfdd, end_mfdd)
                                single_rms_ax_mfdd = np.sqrt(1/len(ax_minus_mfdd[start_mfdd: end_mfdd])*np.sum(ax_minus_mfdd[start_mfdd: end_mfdd]**2))
                                single_zero_intersection = zero_intersection(ax_minus_mfdd)
                            else:
                                single_integral_ax_mfdd = ""
                                single_rms_ax_mfdd = ""
                                single_zero_intersection = ""
                            speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 2)
                            single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                            long_dec_max.append(round(single_long_dec_max, 2))
                            long_dec_mean.append(round(np.mean(ax_fragment), 2))
                            single_long_dec_first_peak, ax_1st_peak_fragment, ax_1st_peak_speed_fragment = self.long_dec_init_peak(ax_fragment, speed_fragment, single_mfdd)
                            single_long_dec_min = self.long_min_dec(ax_1st_peak_fragment, ax_1st_peak_speed_fragment, initial_speed[i-1], single_long_dec_first_peak)
                            if single_long_dec_min != "":
                                long_dec_min.append(round(single_long_dec_min, 2))
                            else:
                                long_dec_min.append("")
                            if single_mfdd != "" and single_long_dec_min != "":
                                mfdd_ax_min_diff.append(round(single_mfdd - abs(single_long_dec_min), 2))
                            else:
                                mfdd_ax_min_diff.append("")
                            if single_long_dec_min != "":
                                diff_longitudinal_initial_peak_max.append(round(abs(single_long_dec_first_peak)-abs(single_long_dec_min), 2))
                            else:
                                diff_longitudinal_initial_peak_max.append("")
                            if single_long_dec_first_peak != "":
                                time_90_dec_initial_peak.append(round(self.ninenty_perc_ax_first_peak(item, dictionaries, single_long_dec_first_peak), 0))
                            else:
                                time_90_dec_initial_peak.append("")
                            try:
                                dec_target_accuracy.append(round(self.accuracy_dec(item, dictionaries, pedal_type[i], maneuvres.reference_string_decel), 0))
                            except TypeError:
                                dec_target_accuracy.append("")
                            try:
                                long_dec_first_peak.append(round(single_long_dec_first_peak, 2))
                            except TypeError:
                                long_dec_first_peak.append("")
                            try:
                                mfdd.append(round(single_mfdd, 2))
                            except TypeError:
                                mfdd.append("")
                            try:
                                integral_ax_mfdd.append(round(single_integral_ax_mfdd, 2))
                            except TypeError:
                                integral_ax_mfdd.append("")
                            try:
                                rms_ax_mfdd.append(round(single_rms_ax_mfdd, 2))
                            except TypeError:
                                rms_ax_mfdd.append("")
                            try:
                                intersection_number.append(round(single_zero_intersection, 2))
                            except TypeError:
                                intersection_number.append("")
                            if "YawRate_degs" in dictionaries.objectives:
                                if "YawRate" in dictionaries.times:
                                    if dictionaries.times["YawRate"][1] >= item[2][1]:
                                        if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                            excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                            cont += 1
                                else:
                                    if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                        elif "ESC" in item[0]:
                            for param in [sv_norm, sav_norm, sl_v1_norm, sfv_v1_norm, ax_vib, long_dec_first_peak, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, ax_rms, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]:
                                param.append("")
                            if item[0] == "ESC_PartialBrkinTurn":
                                single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                                if single_jerk_long_max != "":
                                    max_jerk_long.append(round(single_jerk_long_max, 2))
                                    jerk_long_rms.append(round(single_jerk_rms, 2))
                                else:
                                    max_jerk_long.append(single_jerk_long_max)
                                    jerk_long_rms.append(single_jerk_rms)
                                single_mu, single_fr_force_ratio, single_re_force_ratio, single_fr_pos_ratio, single_re_pos_ratio = self.mu(dictionaries, item, reference_string_speed[i-1], initial_speed[i-1], let, front_act_pos_ratio_graph, rear_act_pos_ratio_graph, mu_graph)
                                if single_mu != "" and single_mu != "ACQUISITION ERROR":
                                    mu.append(round(single_mu, 2))
                                else:
                                    mu.append(single_mu)
                                if single_fr_force_ratio != "ACQUISITION ERROR":
                                    fr_act_for_rat.append(round(single_fr_force_ratio, 2))
                                else:
                                    fr_act_for_rat.append(single_fr_force_ratio)
                                if single_re_force_ratio != "ACQUISITION ERROR":
                                    re_act_for_rat.append(round(single_re_force_ratio, 2))
                                else:
                                    re_act_for_rat.append(single_re_force_ratio)
                                if single_fr_pos_ratio != "ACQUISITION ERROR":
                                    fr_act_pos_rat.append(round(single_fr_pos_ratio, 2))
                                else:
                                    fr_act_pos_rat.append(single_fr_pos_ratio)
                                if single_re_pos_ratio != "ACQUISITION ERROR":
                                    re_act_pos_rat.append(round(single_re_pos_ratio, 2))
                                else:
                                    re_act_pos_rat.append(single_re_pos_ratio)
                                ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 2)
                                speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 2)
                                single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                                long_dec_max.append(round(single_long_dec_max, 2))
                                if single_long_acc_max != "":
                                    acc_peak.append(round(single_long_acc_max, 2))
                                long_dec_mean.append(round(np.mean(ax_fragment), 2))
                                if "YawRate_degs" in dictionaries.objectives:
                                    if "YawRate" in dictionaries.times:
                                        if dictionaries.times["YawRate"][1] >= item[2][1]:
                                            excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                            cont += 1
                                    else:
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                            else:
                                if item[0] != "ESC_Handling":
                                    single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                                    if single_jerk_long_max != "":
                                        max_jerk_long.append(round(single_jerk_long_max, 2))
                                        jerk_long_rms.append(round(single_jerk_rms, 2))
                                    else:
                                        max_jerk_long.append(single_jerk_long_max)
                                        jerk_long_rms.append(single_jerk_rms)                                    
                                    ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 3)
                                    speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 3)
                                    single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                                    long_dec_max.append(round(single_long_dec_max, 2))
                                    if single_long_acc_max != "":
                                        acc_peak.append(round(single_long_acc_max, 2))
                                    else:
                                        acc_peak.append("")
                                    long_dec_mean.append(round(np.mean(ax_fragment), 2))
                                    mu.append("")
                                    fr_act_for_rat.append("")
                                    re_act_for_rat.append("")
                                    fr_act_pos_rat.append("")
                                    re_act_pos_rat.append("")
                                else:
                                    for param in [long_dec_max, long_dec_mean, mu, fr_act_for_rat, re_act_for_rat, fr_act_pos_rat, re_act_pos_rat, max_jerk_long]:
                                        param.append("")        
                                    acc_peak.append(self.ax_pos_peak(dictionaries, item))
                        else:
                            for ogg in [sv_norm, sav_norm, sl_v1_norm, sfv_v1_norm, mu, fr_act_for_rat, re_act_for_rat, fr_act_pos_rat, re_act_pos_rat, ax_vib, long_dec_max, acc_peak, long_dec_first_peak, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, ax_rms, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]:
                                ogg.append("")
                            long_dec_mean.append(round(np.mean(dictionaries.objectives["Ax"][item[2][0]: item[2][1]]), 2))
                            single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                            if single_jerk_long_max != "":
                                max_jerk_long.append(round(single_jerk_long_max, 2))
                                jerk_long_rms.append(round(single_jerk_rms, 2))
                            else:
                                max_jerk_long.append(single_jerk_long_max)
                                jerk_long_rms.append(single_jerk_rms)
                    else:
                        for i in range(len(observer_list)):
                            observer_list[i].append("ACQUISITION ERROR")
                else:
                    if "ABS" in item[0]:
                        acc_peak.append("")
                        single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                        if single_jerk_long_max != "":
                            max_jerk_long.append(round(single_jerk_long_max, 2))
                            jerk_long_rms.append(round(single_jerk_rms, 2))
                        else:
                            max_jerk_long.append(single_jerk_long_max)
                            jerk_long_rms.append(single_jerk_rms)
                        single_mu, single_fr_force_ratio, single_re_force_ratio, single_fr_pos_ratio, single_re_pos_ratio = self.mu(dictionaries, item, reference_string_speed[i-1], initial_speed[i-1], let, front_act_pos_ratio_graph, rear_act_pos_ratio_graph, mu_graph)
                        single_ax_rms = self.rms_ax(initial_speed[i-1], dictionaries, item, reference_string_speed[i-1])
                        if single_ax_rms != "":
                            ax_rms.append(round(single_ax_rms, 2))
                        else:
                            ax_rms.append(single_ax_rms)            
                        if single_mu != "" and single_mu != "ACQUISITION ERROR":
                            mu.append(round(single_mu, 2))
                        else:
                            mu.append(single_mu)
                        if single_fr_force_ratio != "ACQUISITION ERROR":
                            fr_act_for_rat.append(round(single_fr_force_ratio, 2))
                        else:
                            fr_act_for_rat.append(single_fr_force_ratio)
                        if single_re_force_ratio != "ACQUISITION ERROR":
                            re_act_for_rat.append(round(single_re_force_ratio, 2))
                        else:
                            re_act_for_rat.append(single_re_force_ratio)
                        if single_fr_pos_ratio != "ACQUISITION ERROR":
                            fr_act_pos_rat.append(round(single_fr_pos_ratio, 2))
                        else:
                            fr_act_pos_rat.append(single_fr_pos_ratio)
                        if single_re_pos_ratio != "ACQUISITION ERROR":
                            re_act_pos_rat.append(round(single_re_pos_ratio, 2))
                        else:
                            re_act_pos_rat.append(single_re_pos_ratio)
                        ax_vib.append(self.vibration_detector(1.5, 10, dictionaries.objectives["Ax"], dictionaries.time_resampled, item[2][0], item[2][1]))
                        single_sv_norm, sample_v2 = self.stopping_distance_sv_norm(item, dictionaries, v_nominal[i], reference_string_speed[i-1])
                        if single_sv_norm != "":
                            sv_norm.append(round(single_sv_norm, 2))
                        else:
                            sv_norm.append(single_sv_norm)
                        if single_sv_norm != "" and control[i-1]:
                            sav_norm.append(round(single_sv_norm, 2))
                            single_sl_v1_norm = self.stopping_distance_sl_v1_norm(v_nominal[i], dictionaries, item, sample_v2, reference_string_speed[i-1])
                            sl_v1_norm.append(round(single_sl_v1_norm, 2))
                            sfv_v1_norm.append(round(self.stopping_distance_sfv_v1_norm(single_sv_norm, single_sl_v1_norm), 2))
                        else:
                            sav_norm.append("")
                            sl_v1_norm.append("")
                            sfv_v1_norm.append("")
                        tuple_results = self.mfdd(initial_speed[i-1], dictionaries, item, reference_string_speed[i-1])
                        single_mfdd = tuple_results[0]
                        start_mfdd = tuple_results[1]
                        end_mfdd = tuple_results[2]   
                        ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 2)
                        if single_mfdd != "":
                            ax_minus_mfdd = dictionaries.objectives["Ax"] + single_mfdd
                            abs_ax_minus_mfdd = abs(ax_minus_mfdd)
                            single_integral_ax_mfdd = integral(dictionaries.time_resampled, abs_ax_minus_mfdd, start_mfdd, end_mfdd)
                            single_rms_ax_mfdd = np.sqrt(1/len(ax_minus_mfdd[start_mfdd: end_mfdd])*np.sum(ax_minus_mfdd[start_mfdd: end_mfdd]**2))
                            single_zero_intersection = zero_intersection(ax_minus_mfdd)
                        else:
                            single_integral_ax_mfdd = ""
                            single_rms_ax_mfdd = ""
                            single_zero_intersection = ""
                        speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 2)
                        single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                        long_dec_max.append(round(single_long_dec_max, 2))
                        long_dec_mean.append(round(np.mean(ax_fragment), 2))
                        single_long_dec_first_peak, ax_1st_peak_fragment, ax_1st_peak_speed_fragment = self.long_dec_init_peak(ax_fragment, speed_fragment, single_mfdd)
                        single_long_dec_min = self.long_min_dec(ax_1st_peak_fragment, ax_1st_peak_speed_fragment, initial_speed[i-1], single_long_dec_first_peak)
                        if single_long_dec_min != "":
                            long_dec_min.append(round(single_long_dec_min, 2))
                        else:
                            long_dec_min.append("")
                        if single_mfdd != "" and single_long_dec_min != "":
                            mfdd_ax_min_diff.append(round(single_mfdd - abs(single_long_dec_min), 2))
                        else:
                            mfdd_ax_min_diff.append("")
                        if single_long_dec_min != "":
                            diff_longitudinal_initial_peak_max.append(round(abs(single_long_dec_first_peak)-abs(single_long_dec_min), 2))
                        else:
                            diff_longitudinal_initial_peak_max.append("")
                        if single_long_dec_first_peak != "":
                            time_90_dec_initial_peak.append(round(self.ninenty_perc_ax_first_peak(item, dictionaries, single_long_dec_first_peak), 0))
                        else:
                            time_90_dec_initial_peak.append("")
                        try:
                            dec_target_accuracy.append(round(self.accuracy_dec(item, dictionaries, pedal_type[i], maneuvres.reference_string_decel), 0))
                        except TypeError:
                            dec_target_accuracy.append("")
                        try:
                            long_dec_first_peak.append(round(single_long_dec_first_peak, 2))
                        except TypeError:
                            long_dec_first_peak.append("")
                        try:
                            mfdd.append(round(single_mfdd, 2))
                        except TypeError:
                            mfdd.append("")
                        try:
                            integral_ax_mfdd.append(round(single_integral_ax_mfdd, 2))
                        except TypeError:
                            integral_ax_mfdd.append("")
                        try:
                            rms_ax_mfdd.append(round(single_rms_ax_mfdd, 2))
                        except TypeError:
                            rms_ax_mfdd.append("")
                        try:
                            intersection_number.append(round(single_zero_intersection, 2))
                        except TypeError:
                            intersection_number.append("")
                        if "YawRate_degs" in dictionaries.objectives:
                            if "YawRate" in dictionaries.times:
                                if dictionaries.times["YawRate"][1] >= item[2][1]:
                                    if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                            else:
                                if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                    elif "ESC" in item[0]:
                        for param in [sv_norm, sav_norm, sl_v1_norm, sfv_v1_norm, ax_vib, long_dec_first_peak, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, ax_rms, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]:
                            param.append("")
                        if item[0] == "ESC_PartialBrkinTurn":
                            single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                            if single_jerk_long_max != "":
                                max_jerk_long.append(round(single_jerk_long_max, 2))
                                jerk_long_rms.append(round(single_jerk_rms, 2))
                            else:
                                max_jerk_long.append(single_jerk_long_max)
                                jerk_long_rms.append(single_jerk_rms)
                            single_mu, single_fr_force_ratio, single_re_force_ratio, single_fr_pos_ratio, single_re_pos_ratio = self.mu(dictionaries, item, reference_string_speed[i-1], initial_speed[i-1], let, front_act_pos_ratio_graph, rear_act_pos_ratio_graph, mu_graph)
                            if single_mu != "" and single_mu != "ACQUISITION ERROR":
                                mu.append(round(single_mu, 2))
                            else:
                                mu.append(single_mu)
                            if single_fr_force_ratio != "ACQUISITION ERROR":
                                fr_act_for_rat.append(round(single_fr_force_ratio, 2))
                            else:
                                fr_act_for_rat.append(single_fr_force_ratio)
                            if single_re_force_ratio != "ACQUISITION ERROR":
                                re_act_for_rat.append(round(single_re_force_ratio, 2))
                            else:
                                re_act_for_rat.append(single_re_force_ratio)
                            if single_fr_pos_ratio != "ACQUISITION ERROR":
                                fr_act_pos_rat.append(round(single_fr_pos_ratio, 2))
                            else:
                                fr_act_pos_rat.append(single_fr_pos_ratio)
                            if single_re_pos_ratio != "ACQUISITION ERROR":
                                re_act_pos_rat.append(round(single_re_pos_ratio, 2))
                            else:
                                re_act_pos_rat.append(single_re_pos_ratio)
                            ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 2)
                            speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 2)
                            single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                            long_dec_max.append(round(single_long_dec_max, 2))
                            if single_long_acc_max != "":
                                acc_peak.append(round(single_long_acc_max, 2))
                            long_dec_mean.append(round(np.mean(ax_fragment), 2))
                            if "YawRate_degs" in dictionaries.objectives:
                                if "YawRate" in dictionaries.times:
                                    if dictionaries.times["YawRate"][1] >= item[2][1]:
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                                else:
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["Ax"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                        else:
                            if item[0] != "ESC_Handling":
                                single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                                if single_jerk_long_max != "":
                                    max_jerk_long.append(round(single_jerk_long_max, 2))
                                    jerk_long_rms.append(round(single_jerk_rms, 2))
                                else:
                                    max_jerk_long.append(single_jerk_long_max)
                                    jerk_long_rms.append(single_jerk_rms)
                                ax_fragment = signal_fragment_recovery(item, dictionaries, "Ax", 3)
                                speed_fragment = signal_fragment_recovery(item, dictionaries, reference_string_speed[i-1] + "_ms", 3)
                                single_long_dec_max, single_long_acc_max = self.long_max_dec(ax_fragment, speed_fragment)
                                long_dec_max.append(round(single_long_dec_max, 2))
                                if single_long_acc_max != "":
                                    acc_peak.append(round(single_long_acc_max, 2))
                                else:
                                    acc_peak.append("")
                                long_dec_mean.append(round(np.mean(ax_fragment), 2))
                                mu.append("")
                                fr_act_for_rat.append("")
                                re_act_for_rat.append("")
                                fr_act_pos_rat.append("")
                                re_act_pos_rat.append("")
                            else:
                                for param in [long_dec_max, long_dec_mean, mu, fr_act_for_rat, re_act_for_rat, fr_act_pos_rat, re_act_pos_rat, max_jerk_long]:
                                    param.append("")        
                                acc_peak.append(self.ax_pos_peak(dictionaries, item))
                    else:
                        for ogg in [sv_norm, sav_norm, sl_v1_norm, sfv_v1_norm, mu, fr_act_for_rat, re_act_for_rat, fr_act_pos_rat, re_act_pos_rat, ax_vib, long_dec_max, acc_peak, long_dec_first_peak, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, ax_rms, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]:
                            ogg.append("")
                        long_dec_mean.append(round(np.mean(dictionaries.objectives["Ax"][item[2][0]: item[2][1]]), 2))
                        single_jerk_long_max, single_jerk_rms = self.jerk_long_max(dictionaries, item, reference_string_speed[i-1])
                        if single_jerk_long_max != "":
                            max_jerk_long.append(round(single_jerk_long_max, 2))
                            jerk_long_rms.append(round(single_jerk_rms, 2))
                        else:
                            max_jerk_long.append(single_jerk_long_max)
                            jerk_long_rms.append(single_jerk_rms)
            else:
                if "ABS" in item[0]:
                    single_sv_norm, sample_v2 = self.stopping_distance_sv_norm(item, dictionaries, v_nominal[i], reference_string_speed[i-1])
                    if single_sv_norm != "":
                        sv_norm.append(round(single_sv_norm, 2))
                    else:
                        sv_norm.append(single_sv_norm)
                    if single_sv_norm != "" and control[i-1]:
                        sav_norm.append(round(single_sv_norm, 2))
                        single_sl_v1_norm = self.stopping_distance_sl_v1_norm(v_nominal[i], dictionaries, item, sample_v2, reference_string_speed[i-1])
                        sl_v1_norm.append(round(single_sl_v1_norm, 2))
                        sfv_v1_norm.append(round(self.stopping_distance_sfv_v1_norm(single_sv_norm, single_sl_v1_norm), 2))
                    else:
                        sav_norm.append("")
                        sl_v1_norm.append("")
                        sfv_v1_norm.append("")
                else:
                    sav_norm.append("")
                    sl_v1_norm.append("")
                    sfv_v1_norm.append("")
                    sv_norm.append("")
                observer_list_short = [mu, fr_act_pos_rat, re_act_pos_rat, fr_act_for_rat, re_act_for_rat, ax_vib, long_dec_max, acc_peak, long_dec_first_peak, ax_rms, max_jerk_long, jerk_long_rms, mfdd, integral_ax_mfdd, rms_ax_mfdd, intersection_number, long_dec_mean, long_dec_min, mfdd_ax_min_diff, diff_longitudinal_initial_peak_max, time_90_dec_initial_peak, dec_target_accuracy]
                for l in range(len(observer_list_short)):
                    observer_list_short[l].append("ACQUISITION ERROR")
        if let.get() == 1:
            n_braking = []
            for i in range(len(front_act_pos_ratio_graph)):
                n_braking.append(i+1)
            fig, axes = plt.subplots(2, figsize = (15,10))
            axes[0].scatter(n_braking, front_act_pos_ratio_graph, color = "black", s = 10)
            axes[0].plot(n_braking, [95]*len(n_braking), linestyle='--', color='red')
            axes[0].plot(n_braking, [105]*len(n_braking), linestyle='--', color='red')
            axes[0].set_ylabel("Front Actuator Position Ratio FL/FR [%]", color = "black")
            axes[0].set_ylim(70,130)
            axes[0].set_xlim(1,100)
            axes[0].set_xlabel("Stop n°")
            axes[0].fill_between(n_braking, 95,105, alpha = 0.2, facecolor = "green")
            axes[0].xaxis.set_major_locator(MultipleLocator(2))
            axes[0].xaxis.set_minor_locator(AutoMinorLocator(2))
            axes[0].yaxis.set_major_locator(MultipleLocator(10))
            axes[0].yaxis.set_minor_locator(MultipleLocator(5))
            axes[0].grid(which='major', linestyle=(0, (5, 10)), linewidth=1)
            axes[0].grid(which='minor', linestyle=(0, (5, 10)), linewidth=0.5)
            axes[1].scatter(n_braking, rear_act_pos_ratio_graph, color = "black", s = 10)
            axes[1].plot(n_braking, [95]*len(n_braking), linestyle='--', color='red')
            axes[1].plot(n_braking, [105]*len(n_braking), linestyle='--', color='red')
            axes[1].set_ylabel("Rear Actuator Position Ratio RL/RR [%]", color = "black")
            axes[1].set_ylim(70,130)
            axes[1].set_xlim(1,100)
            axes[1].set_xlabel("Stop n°")
            axes[1].xaxis.set_major_locator(MultipleLocator(2))
            axes[1].xaxis.set_minor_locator(AutoMinorLocator(2))
            axes[1].yaxis.set_major_locator(MultipleLocator(10))
            axes[1].yaxis.set_minor_locator(MultipleLocator(5))
            axes[1].grid(which='major', linestyle=(0, (5, 10)), linewidth=1)
            axes[1].grid(which='minor', linestyle=(0, (5, 10)), linewidth=0.5)
            axes[1].fill_between(n_braking, 95,105, alpha = 0.2, facecolor = "green")
            file = file.split('/')[-1][:-4]
            image_path = saving_folder + "\\Figures"
            figure_name = file + '_Ratio.png'
            fig.tight_layout()
            if not os.path.isdir(image_path):
                os.makedirs(image_path)
            plt.savefig(image_path + '\\' + figure_name, bbox_inches='tight')
            fig, axes = plt.subplots(figsize = (15,10))
            axes.scatter(n_braking, mu_graph, color = "black", s = 10)
            axes.set_ylabel("Friction coefficient μ []", color = "black")
            axes.set_ylim(0.2,0.5)
            axes.set_xlim(1,100)
            axes.set_xlabel("Stop n°")
            axes.xaxis.set_major_locator(MultipleLocator(2))
            axes.xaxis.set_minor_locator(AutoMinorLocator(2))
            axes.yaxis.set_major_locator(MultipleLocator(0.05))
            axes.yaxis.set_minor_locator(MultipleLocator(0.025))
            axes.grid(which='major', linestyle=(0, (5, 10)), linewidth=1)
            axes.grid(which='minor', linestyle=(0, (5, 10)), linewidth=0.5)
            figure_name = file + '_Mu.png'
            fig.tight_layout()
            if not os.path.isdir(image_path):
                os.makedirs(image_path)
            plt.savefig(image_path + '\\' + figure_name, bbox_inches='tight')
        for item in observer_list:
            parameters_list.append(item)
 
    def lateral_performances(self, maneuvres, dictionaries, parameters_list, direction_check, excel_bigol_list):
        lateral_initial_brake = ['Ay @ DrivingInput']
        lateral_acc_peak_0_05s = ["Ay_Overshoot_05s"]
        lateral_acc_peak_0_1s = ["Ay_Overshoot_1s"]
        lateral_acc_peak_0_2s = ["Ay_Overshoot_2s"]
        lateral_acc_peak_0_5s = ["Ay_Overshoot_5s"]
        lateral_acc_min_0_05s = ["Ay_Undershoot_05s"]
        lateral_acc_min_0_1s = ["Ay_Undershoot_1s"]
        lateral_acc_min_0_2s = ["Ay_Undershoot_2s"]
        lateral_acc_min_0_5s = ["Ay_Undershoot_5s"]
        lateral_acc_peak = ["Ay_Max_Overshoot (+sx)"]
        lateral_acc_min = ["Ay_Max_Undershoot (+sx)"]
        Lateral_dec_app_range = ["Ay_Bandwidth"]
        delta_acc_max = ["Delta_Ay_Max"]
        max_jerk_lat = ["jerk_lat_max"]
        starting_radius = ["Radius @ DrivingInput (+sx)"]
        nominal_radius = ["Radius_Nominal (+sx)"]
        initial_radius = []
        observer_list = [lateral_initial_brake, lateral_acc_peak_0_05s, lateral_acc_peak_0_1s, lateral_acc_peak_0_2s, lateral_acc_peak_0_5s, lateral_acc_peak, lateral_acc_min_0_05s, lateral_acc_min_0_1s, lateral_acc_min_0_2s, lateral_acc_min_0_5s, lateral_acc_min, delta_acc_max, Lateral_dec_app_range, max_jerk_lat, starting_radius, nominal_radius]
        reference_string_speed = maneuvres.reference_string_speed
        j = 0
        cont = 0
        for manoeuvre in maneuvres.maneuvre:
            if "Ay" in dictionaries.objectives:
                if "Ay" in dictionaries.times:  
                    if dictionaries.times["Ay"][1] >= manoeuvre[2][1]:
                        if "ESC" in manoeuvre[0] and "ESC_PartialBrkinTurn" != manoeuvre[0] and "ESC_Handling" != manoeuvre[0]:
                            single_max_jerk_lat = self.jerk_lat_max(dictionaries, manoeuvre, reference_string_speed[j])
                            lateral_acc_start = self.lateral_acceleration_start(maneuver = manoeuvre, data = dictionaries.objectives['Ay'], base = 3, frequency = dictionaries.frequency)
                            peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, min_0_05s, min_0_1s, min_0_2s, min_0_5s, max_acc, min_acc, delta_ay_max, radius_initial, effective_ay, theorical_ay = self.lateral_acceleration_maneuver(maneuver = manoeuvre, data = [dictionaries.objectives['Ay'], dictionaries.objectives[reference_string_speed[j] + "_ms"]], base = 3, frequency = dictionaries.frequency, nominal_radius = dictionaries.target_radius[j], ay_start = lateral_acc_start, direction_check = direction_check)
                            Lateral_range, radius_nominal = self.lateral_acceleration_steady(maneuver = manoeuvre, initial_radius=radius_initial, effective_ay = effective_ay)
                            initial_radius.append(radius_initial)
                        elif "ESC_Handling" == manoeuvre[0]:
                            for item in [lateral_acc_peak_0_05s, lateral_acc_peak_0_1s, lateral_acc_peak_0_2s, lateral_acc_peak_0_5s, lateral_acc_peak, lateral_acc_min, max_jerk_lat, lateral_initial_brake, lateral_acc_min_0_05s, lateral_acc_min_0_1s, lateral_acc_min_0_2s, lateral_acc_min_0_5s, Lateral_dec_app_range, delta_acc_max, starting_radius, nominal_radius]:
                                item.append("")
                            initial_radius.append("")
                        else:
                            single_max_jerk_lat = self.jerk_lat_max(dictionaries, manoeuvre, reference_string_speed[j])
                            lateral_acc_start = self.lateral_acceleration_start(maneuver = manoeuvre, data = dictionaries.objectives['Ay'], base = 2, frequency = dictionaries.frequency)
                            peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, min_0_05s, min_0_1s, min_0_2s, min_0_5s, max_acc, min_acc, delta_ay_max, radius_initial, effective_ay, theorical_ay = self.lateral_acceleration_maneuver(maneuver = manoeuvre, data = [dictionaries.objectives['Ay'], dictionaries.objectives[reference_string_speed[j] + "_ms"]], base = 2, frequency = dictionaries.frequency, nominal_radius = dictionaries.target_radius[j], ay_start = lateral_acc_start, direction_check = direction_check)
                            Lateral_range, radius_nominal = self.lateral_acceleration_steady(maneuver = manoeuvre, initial_radius = radius_initial, effective_ay = effective_ay)
                            initial_radius.append(radius_initial)
                            if "YawRate_degs" in dictionaries.objectives:
                                if "YawRate" in dictionaries.times:
                                    if dictionaries.times["YawRate"][1] >= manoeuvre[2][1]:
                                        if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                                            excel_bigol_list[cont].append(list(dictionaries.objectives["Ay"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                                            excel_bigol_list[cont].append(list(theorical_ay))
                                            cont += 1
                                else:
                                    if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ay"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                                        excel_bigol_list[cont].append(list(theorical_ay))
                                        cont += 1
                        if manoeuvre[0] != "ESC_Handling":
                            peak_list = [lateral_acc_start, peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, max_acc, min_0_05s, min_0_1s, min_0_2s, min_0_5s, min_acc, delta_ay_max, Lateral_range, single_max_jerk_lat, radius_initial, radius_nominal]    
                            for i in range(len(observer_list)):
                                if peak_list[i] != "" and peak_list[i] != True and peak_list[i] != False:
                                    observer_list[i].append(round(peak_list[i], 2))
                                else:
                                    observer_list[i].append(peak_list[i])    
                    else:
                        for i in range(len(observer_list)):
                            observer_list[i].append("ACQUISITION ERROR")
                else:
                    if "ESC" in manoeuvre[0] and "ESC_PartialBrkinTurn" != manoeuvre[0] and "ESC_Handling" != manoeuvre[0]:
                        single_max_jerk_lat = self.jerk_lat_max(dictionaries, manoeuvre, reference_string_speed[j])
                        lateral_acc_start = self.lateral_acceleration_start(maneuver = manoeuvre, data = dictionaries.objectives['Ay'], base = 3, frequency = dictionaries.frequency)
                        peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, min_0_05s, min_0_1s, min_0_2s, min_0_5s, max_acc, min_acc, delta_ay_max, radius_initial, effective_ay, theorical_ay = self.lateral_acceleration_maneuver(maneuver = manoeuvre, data = [dictionaries.objectives['Ay'], dictionaries.objectives[reference_string_speed[j] + "_ms"]], base = 3, frequency = dictionaries.frequency, nominal_radius = dictionaries.target_radius[j], ay_start = lateral_acc_start, direction_check = direction_check)
                        Lateral_range, radius_nominal = self.lateral_acceleration_steady(maneuver = manoeuvre, initial_radius=radius_initial, effective_ay = effective_ay)
                        initial_radius.append(radius_initial)
                    elif "ESC_Handling" == manoeuvre[0]:
                        for item in [lateral_acc_peak_0_05s, lateral_acc_peak_0_1s, lateral_acc_peak_0_2s, lateral_acc_peak_0_5s, lateral_acc_peak, lateral_acc_min, lateral_initial_brake, max_jerk_lat, lateral_acc_min_0_05s, lateral_acc_min_0_1s, lateral_acc_min_0_2s, lateral_acc_min_0_5s, Lateral_dec_app_range, delta_acc_max, starting_radius, nominal_radius]:
                            item.append("")
                        initial_radius.append("")
                    else:
                        single_max_jerk_lat = self.jerk_lat_max(dictionaries, manoeuvre, reference_string_speed[j])
                        lateral_acc_start = self.lateral_acceleration_start(maneuver = manoeuvre, data = dictionaries.objectives['Ay'], base = 2, frequency = dictionaries.frequency)
                        peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, min_0_05s, min_0_1s, min_0_2s, min_0_5s, max_acc, min_acc, delta_ay_max, radius_initial, effective_ay, theorical_ay = self.lateral_acceleration_maneuver(maneuver = manoeuvre, data = [dictionaries.objectives['Ay'], dictionaries.objectives[reference_string_speed[j] + "_ms"]], base = 2, frequency = dictionaries.frequency, nominal_radius = dictionaries.target_radius[j], ay_start = lateral_acc_start, direction_check = direction_check)
                        Lateral_range, radius_nominal = self.lateral_acceleration_steady(maneuver = manoeuvre, initial_radius = radius_initial, effective_ay = effective_ay)
                        initial_radius.append(radius_initial)
                        if "YawRate_degs" in dictionaries.objectives:
                                if "YawRate" in dictionaries.times:
                                    if dictionaries.times["YawRate"][1] >= manoeuvre[2][1]:
                                        if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                                            excel_bigol_list[cont].append(list(dictionaries.objectives["Ay"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                                            excel_bigol_list[cont].append(list(theorical_ay))
                                            cont += 1
                                else:
                                    if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["Ay"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                                        excel_bigol_list[cont].append(list(theorical_ay))
                                        cont += 1
                    if manoeuvre[0] != "ESC_Handling":
                        peak_list = [lateral_acc_start, peak_0_05s, peak_0_1s, peak_0_2s, peak_0_5s, max_acc, min_0_05s, min_0_1s, min_0_2s, min_0_5s, min_acc, delta_ay_max, Lateral_range, single_max_jerk_lat, radius_initial, radius_nominal]    
                        for i in range(len(observer_list)):
                            if peak_list[i] != "" and peak_list[i] != True and peak_list[i] != False:
                                observer_list[i].append(round(peak_list[i], 2))
                            else:
                                observer_list[i].append(peak_list[i])    
            else:
                for i in range(len(observer_list)):
                    observer_list[i].append("ACQUISITION ERROR")
            j += 1

        for indexes in observer_list:
            parameters_list.append(indexes)
        return initial_radius
 
    def yaw_rate_performance(self, maneuvres, dictionaries, initial_radius, parameters_list, direction_check, excel_bigol_list):
        yaw_rate_initial_braking = ['YawRate @ DrivingInput']
        #yaw_rate_mean = ['yaw_rate_mean']
        yaw_rate_peak_0_05s = ['YawRate_Overshoot_05']
        yaw_rate_peak_0_1s = ['YawRate_Overshoot_1']
        yaw_rate_peak_0_2s = ['YawRate_Overshoot_2']
        yaw_rate_peak_0_5s = ['YawRate_Overshoot_5']
        yaw_rate_min_0_05s = ['YawRate_Undershoot_05']
        yaw_rate_min_0_1s = ['YawRate_Undershoot_1']
        yaw_rate_min_0_2s = ['YawRate_Undershoot_2']
        yaw_rate_min_0_5s = ['YawRate_Undershoot_5']
        yaw_rate_peak = ['YawRate_Max_Overshoot (+sx)']
        yaw_rate_min = ['YawRate_Max_Undershoot (+sx)']
        yaw_rate_app_range = ['YawRate_Bandwidth']
        max_delta_yaw = ["Delta_Yaw_Max"]
        yaw_rate_rms_0_05s = ['Yaw_RMS_05']
        yaw_rate_rms_0_1s = ['Yaw_RMS_1']
        yaw_rate_rms_0_2s = ['Yaw_RMS_2']
        yaw_rate_rms_0_5s = ['Yaw_RMS_5']
        yaw_rate_rms = ['Yaw_RMS']
        reference_string_speed = maneuvres.reference_string_speed
        observer_list = [yaw_rate_initial_braking, yaw_rate_peak_0_05s, yaw_rate_peak_0_1s, yaw_rate_peak_0_2s, yaw_rate_peak_0_5s, yaw_rate_peak, yaw_rate_min_0_05s, yaw_rate_min_0_1s, yaw_rate_min_0_2s, yaw_rate_min_0_5s, yaw_rate_min, max_delta_yaw, yaw_rate_app_range, yaw_rate_rms_0_05s, yaw_rate_rms_0_1s, yaw_rate_rms_0_2s, yaw_rate_rms_0_5s, yaw_rate_rms]
        j = 0
        cont = 0
        for manoeuvre in maneuvres.maneuvre:
            if "YawRate_degs" in dictionaries.objectives and initial_radius != []:
                if "YawRate" in dictionaries.times:
                    if dictionaries.times["YawRate"][1] >= manoeuvre[2][1]:
                        if "ESC" in manoeuvre[0] and "ESC_PartialBrkinTurn" != manoeuvre[0] and "ESC_Handling" != manoeuvre[0]:
                            lateral_yaw_start = np.mean(dictionaries.objectives["YawRate_degs"][manoeuvre[3][0] - int(round(0.5*dictionaries.frequency, 0)):manoeuvre[3][0]])
                            yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_yaw, theorical_plot, effective_plot = self.yawrate_maneuver(maneuver= manoeuvre, data= [dictionaries.objectives[reference_string_speed[j] + "_ms"], dictionaries.objectives['YawRate_degs']], base = 3, initial_radius = initial_radius[j], frequency = dictionaries.frequency, direction_check = direction_check, yaw_start = lateral_yaw_start)
                            app_range = max(effective_yaw) - min(effective_yaw)
                            if "Theorical_Yaw_degs" in dictionaries.objectives:
                                dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                                dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                            else:
                                dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                                dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                        elif "ESC_Handling" == manoeuvre[0]:
                            for item in [yaw_rate_initial_braking, yaw_rate_peak_0_05s, yaw_rate_peak_0_1s, yaw_rate_peak_0_2s, yaw_rate_peak_0_5s, yaw_rate_min_0_05s, yaw_rate_min_0_1s, yaw_rate_min_0_2s, yaw_rate_min_0_5s, yaw_rate_peak, yaw_rate_min, max_delta_yaw, yaw_rate_app_range, yaw_rate_rms_0_05s, yaw_rate_rms_0_1s, yaw_rate_rms_0_2s, yaw_rate_rms_0_5s, yaw_rate_rms]:
                                item.append("")
                            if "Theorical_Yaw_degs" in dictionaries.objectives:
                                dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                                dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                            else:
                                dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                                dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                        else:
                            lateral_yaw_start = np.mean(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0] - int(round(0.5*dictionaries.frequency, 0)):manoeuvre[2][0]])
                            yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_yaw, theorical_plot, effective_plot = self.yawrate_maneuver(maneuver= manoeuvre, data = [dictionaries.objectives[reference_string_speed[j] + "_ms"], dictionaries.objectives['YawRate_degs']], base = 2, initial_radius = initial_radius[j], frequency = dictionaries.frequency, direction_check = direction_check, yaw_start = lateral_yaw_start)
                            app_range = max(effective_yaw) - min(effective_yaw)
                            if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                                excel_bigol_list[cont].append(list(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                                excel_bigol_list[cont].append(list(theorical_yaw))
                                cont += 1
                            if "Theorical_Yaw_degs" in dictionaries.objectives:
                                if isinstance(theorical_yaw, str) and theorical_yaw == "":
                                    dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                                else:
                                    dictionaries.objectives["Theorical_Yaw_degs"].append(theorical_plot)
                                dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                            else:
                                if isinstance(theorical_yaw, str) and theorical_yaw == "":
                                    dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                                else:
                                    dictionaries.objectives["Theorical_Yaw_degs"] = [theorical_plot]
                                dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                        if manoeuvre[0] != "ESC_Handling":    
                            peak_list = [lateral_yaw_start, yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, app_range, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms]
                            for i in range(len(observer_list)):
                                if peak_list[i] != "" and peak_list[i] != True and peak_list[i] != False:
                                    observer_list[i].append(round(peak_list[i], 2))
                                else:
                                    observer_list[i].append(peak_list[i])
                    else:
                        for i in range(len(observer_list)):
                            observer_list[i].append("ACQUISITION ERROR")
                else:
                    if "ESC" in manoeuvre[0] and "ESC_PartialBrkinTurn" != manoeuvre[0] and "ESC_Handling" != manoeuvre[0]:
                        lateral_yaw_start = np.mean(dictionaries.objectives["YawRate_degs"][manoeuvre[3][0] - int(round(0.5*dictionaries.frequency, 0)):manoeuvre[3][0]])
                        yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_yaw, theorical_plot, effective_plot = self.yawrate_maneuver(maneuver= manoeuvre, data= [dictionaries.objectives[reference_string_speed[j] + "_ms"], dictionaries.objectives['YawRate_degs']], base = 3, initial_radius = initial_radius[j], frequency = dictionaries.frequency, direction_check = direction_check, yaw_start = lateral_yaw_start)
                        app_range = max(effective_yaw) - min(effective_yaw)
                        if "Theorical_Yaw_degs" in dictionaries.objectives:
                            dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                            dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                        else:
                            dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                            dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                    elif "ESC_Handling" == manoeuvre[0]:
                        yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_yaw, theorical_plot, effective_plot = self.yawrate_maneuver(maneuver= manoeuvre, data= [dictionaries.objectives[reference_string_speed[j] + "_ms"], dictionaries.objectives['YawRate_degs']], base = 2, initial_radius = initial_radius[j], frequency = dictionaries.frequency, direction_check = direction_check, yaw_start = 0)
                        for item in [yaw_rate_initial_braking, yaw_rate_peak_0_05s, yaw_rate_peak_0_1s, yaw_rate_peak_0_2s, yaw_rate_peak_0_5s, yaw_rate_min_0_05s, yaw_rate_min_0_1s, yaw_rate_min_0_2s, yaw_rate_min_0_5s, yaw_rate_peak, yaw_rate_min, max_delta_yaw, yaw_rate_app_range, yaw_rate_rms_0_05s, yaw_rate_rms_0_1s, yaw_rate_rms_0_2s, yaw_rate_rms_0_5s, yaw_rate_rms]:
                            item.append("")
                            if "Theorical_Yaw_degs" in dictionaries.objectives:
                                dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                                dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                            else:
                                dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                                dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                    else:
                        lateral_yaw_start = np.mean(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0] - int(round(0.5*dictionaries.frequency, 0)):manoeuvre[2][0]])
                        yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, effective_yaw, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms, theorical_yaw, theorical_plot, effective_plot = self.yawrate_maneuver(maneuver= manoeuvre, data = [dictionaries.objectives[reference_string_speed[j] + "_ms"], dictionaries.objectives['YawRate_degs']], base = 2, initial_radius = initial_radius[j], frequency = dictionaries.frequency, direction_check = direction_check, yaw_start = lateral_yaw_start)
                        app_range = max(effective_yaw) - min(effective_yaw)
                        if manoeuvre[0] in ["ABS_InTurn", "ESC_PartialBrkinTurn"] or (manoeuvre[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0]]) > 3):
                            excel_bigol_list[cont].append(list(dictionaries.objectives["YawRate_degs"][manoeuvre[2][0] - int(0.5*dictionaries.frequency): manoeuvre[2][1]]))
                            excel_bigol_list[cont].append(list(theorical_yaw))
                            cont += 1          
                        if "Theorical_Yaw_degs" in dictionaries.objectives:
                            if isinstance(theorical_yaw, str) and theorical_yaw == "":
                                dictionaries.objectives["Theorical_Yaw_degs"].append(np.array([np.nan]*len(effective_plot)))
                            else:
                                dictionaries.objectives["Theorical_Yaw_degs"].append(theorical_plot)
                            dictionaries.objectives["Effective_Yaw_degs"].append(effective_plot)
                        else:
                            if isinstance(theorical_yaw, str) and theorical_yaw == "":
                                dictionaries.objectives["Theorical_Yaw_degs"] = [np.array([np.nan]*len(effective_plot))]
                            else:
                                dictionaries.objectives["Theorical_Yaw_degs"] = [theorical_plot]
                            dictionaries.objectives["Effective_Yaw_degs"] = [effective_plot]
                    if manoeuvre[0] != "ESC_Handling":    
                        peak_list = [lateral_yaw_start, yawrate_peak_05, yawrate_peak_1, yawrate_peak_2, yawrate_peak_5, yawrate_max, yawrate_min_05, yawrate_min_1, yawrate_min_2, yawrate_min_5, min_yaw, delta_yaw_max, app_range, yawrate_rms_05, yawrate_rms_1, yawrate_rms_2, yawrate_rms_5, yawrate_rms]
                        for i in range(len(observer_list)):
                            if peak_list[i] != "" and peak_list[i] != True and peak_list[i] != False:
                                observer_list[i].append(round(peak_list[i], 2))
                            else:
                                observer_list[i].append(peak_list[i])
            else:
                for i in range(len(observer_list)):
                    observer_list[i].append("ACQUISITION ERROR")
            j += 1
 
        for indexes in observer_list:
            parameters_list.append(indexes)
 
    def steering_performances(self, maneuvres, dictionaries, parameters_list):
        steering_initial_maneuver = ['SWA @ DrivingInput']
        steering_peak = ["SWA_Peak (vs SWA @DrivingInput)"]
        steering_peak_1 = ["SWA_Peak_1 (vs SWA @DrivingInput)"]
        steering_peak_2 = ["SWA_Peak_2 (vs SWA @DrivingInput)"]
        steering_spd_peak = ["SWA_spd_Peak"]
        steering_spd_peak_1 = ['SWA_spd_Peak_1']
        steering_spd_peak_2 = ['SWA_spd_Peak_2']
        observer_list = [steering_initial_maneuver, steering_peak, steering_peak_1, steering_peak_2, steering_spd_peak, steering_spd_peak_1, steering_spd_peak_2]
        for manoeuvre in maneuvres.maneuvre:
            if "SteeringAngle_deg" in dictionaries.objectives:
                if "SteeringAngle" in dictionaries.times:
                    if dictionaries.times["SteeringAngle"][1] >= manoeuvre[2][1]:
                        if manoeuvre[0] == "ESC_Handling":
                            for item in [steering_initial_maneuver, steering_peak, steering_peak_1, steering_peak_2, steering_spd_peak, steering_spd_peak_1, steering_spd_peak_2]:
                                item.append("")
                        else:
                            if "ESC" in manoeuvre[0] and manoeuvre[0] != "ESC_PartialBrkinTurn":
                                steering_start, swa_peak_1, swa_peak_2, swa_peak, swa_spd_peak_1, swa_spd_peak_2, swa_spd_peak = self.steering_maneuver(maneuver = manoeuvre,
                                data = [dictionaries.objectives['SteeringAngle_deg'], dictionaries.objectives["SteeringAngleDer_degs"]], frequency = dictionaries.frequency, base = 3)
                            else:
                                steering_start, swa_peak_1, swa_peak_2, swa_peak, swa_spd_peak_1, swa_spd_peak_2, swa_spd_peak = self.steering_maneuver(maneuver = manoeuvre,
                                data = [dictionaries.objectives['SteeringAngle_deg'], dictionaries.objectives["SteeringAngleDer_degs"]], frequency = dictionaries.frequency, base = 2)
                            peak_list = [steering_start, swa_peak, swa_peak_1, swa_peak_2, swa_spd_peak, swa_spd_peak_1, swa_spd_peak_2]  
                            for i in range(len(observer_list)):
                                if peak_list[i] != "":
                                    observer_list[i].append(round(peak_list[i], 2))
                                else:
                                    observer_list[i].append(peak_list[i])
                    else:
                        for i in range(len(observer_list)):
                            observer_list[i].append("ACQUISITION ERROR")                       
                else:
                    if manoeuvre[0] == "ESC_Handling":
                        for item in [steering_initial_maneuver, steering_peak, steering_peak_1, steering_peak_2, steering_spd_peak, steering_spd_peak_1, steering_spd_peak_2]:
                            item.append("")
                    else:
                        if "ESC" in manoeuvre[0] and manoeuvre[0] != "ESC_PartialBrkinTurn":
                            steering_start, swa_peak_1, swa_peak_2, swa_peak, swa_spd_peak_1, swa_spd_peak_2, swa_spd_peak = self.steering_maneuver(maneuver = manoeuvre,
                            data = [dictionaries.objectives['SteeringAngle_deg'], dictionaries.objectives["SteeringAngleDer_degs"]], frequency = dictionaries.frequency, base = 3)
                        else:
                            steering_start, swa_peak_1, swa_peak_2, swa_peak, swa_spd_peak_1, swa_spd_peak_2, swa_spd_peak = self.steering_maneuver(maneuver = manoeuvre,
                            data = [dictionaries.objectives['SteeringAngle_deg'], dictionaries.objectives["SteeringAngleDer_degs"]], frequency = dictionaries.frequency, base = 2)
                        peak_list = [steering_start, swa_peak, swa_peak_1, swa_peak_2, swa_spd_peak, swa_spd_peak_1, swa_spd_peak_2]  
                        for i in range(len(observer_list)):
                            if peak_list[i] != "":
                                observer_list[i].append(round(peak_list[i], 2))
                            else:
                                observer_list[i].append(peak_list[i])
            else:
                for i in range(len(observer_list)):
                    observer_list[i].append("ACQUISITION ERROR")  

        for indexes in observer_list:
            parameters_list.append(indexes)

    def slip_repartition(self, maneuvers, dictionaries, wheel_slip_check, parameters_list):
        time_perc_slip_pos = ["TimePerc_SlipRatioPositive"]
        time_perc_slip_neg = ["TimePerc_SlipRatioNegative"]
        reference_string_speed = maneuvers.reference_string_speed
        observer_list = [time_perc_slip_pos, time_perc_slip_neg]
        channels = ["ABSTrigger_FL", "ABSTrigger_FR", "ABSTrigger_RL", "ABSTrigger_RR", "WheelSpeed_FL", "WheelSpeed_FR", "WheelSpeed_RL", "WheelSpeed_RR", "WheelSlip_FL", "WheelSlip_FR"]
        k = 0
        for item in maneuvers.maneuvre:
            if maneuvers.reference_string_speed[k] + "_ms" in dictionaries.objectives:
                if maneuvers.reference_string_speed[k] in dictionaries.times:
                    if dictionaries.times[maneuvers.reference_string_speed[k]][1] > item[2][1]:        
                        abs_fl_flag = True
                        abs_fr_flag = True
                        abs_rl_flag = True
                        abs_rr_flag = True
                        speed_fl_flag = True
                        speed_fr_flag = True
                        speed_rl_flag = True
                        speed_rr_flag = True
                        slip_fl_flag = True
                        slip_fr_flag = True
                        level_1 = True
                        level_2 = True
                        level_3 = True
                        level_4 = True
                        flags = [abs_fl_flag, abs_fr_flag, abs_rl_flag, abs_rr_flag, speed_fl_flag, speed_fr_flag, slip_fl_flag, slip_fr_flag, speed_rl_flag, speed_rr_flag]
                        for i in range(len(channels)):
                            if i in [0, 1, 2, 3, 8, 9]:
                                if channels[i] in dictionaries.objectives:  
                                    if channels[i] in dictionaries.times:
                                        if dictionaries.times[channels[i]][1] < item[2][1]:
                                            flags[i] = False
                                else:
                                    flags[i] = False
                            else:
                                if channels[i] + "_ms" in dictionaries.objectives:  
                                    if channels[i] in dictionaries.times:
                                        if dictionaries.times[channels[i]][1] < item[2][1]:
                                            flags[i] = False
                                else:
                                    flags[i] = False

                        for i in range(4):
                            if not flags[i]:
                                level_1 = False
                        for i in range(4, 6):
                            if not flags[i]:
                                level_2 = False
                        for i in range(6, 8):
                            if not flags[i]:
                                level_3 = False  
                        for i in range(8, 10):
                            if not flags[i]:
                                level_4 = False     

                        if ("ESC_PartialBrkinTurn" == item[0] or "ABS" in item[0]) and level_1:
                            time_perc_slip_ratio_neg, time_perc_slip_ratio_pos = self.time_slip_ratio(item, dictionaries, reference_string_speed[k], wheel_slip_check, level_2, level_3, level_4)
                            peak_list = [time_perc_slip_ratio_pos, time_perc_slip_ratio_neg]
                            for j in range(len(observer_list)):
                                if peak_list[j] != "ACQUISITION ERROR" and peak_list[j] != "" and peak_list[j] != "N/A":
                                    observer_list[j].append(round(peak_list[j]))
                                else:
                                    observer_list[j].append(peak_list[j])
                        else:
                            if not level_1:
                                wheel_slip_check.append(False)
                                for item in observer_list:
                                    item.append("N/A")
                            else:
                                wheel_slip_check.append(False)
                                for item in observer_list:
                                    item.append("")
                    else:
                        for item in observer_list:
                            wheel_slip_check.append(False)
                            item.append("ACQUISITION ERROR")
                else:
                    abs_fl_flag = True
                    abs_fr_flag = True
                    abs_rl_flag = True
                    abs_rr_flag = True
                    speed_fl_flag = True
                    speed_fr_flag = True
                    speed_rl_flag = True
                    speed_rr_flag = True
                    slip_fl_flag = True
                    slip_fr_flag = True
                    level_1 = True
                    level_2 = True
                    level_3 = True
                    level_4 = True
                    flags = [abs_fl_flag, abs_fr_flag, abs_rl_flag, abs_rr_flag, speed_fl_flag, speed_fr_flag, slip_fl_flag, slip_fr_flag, speed_rl_flag, speed_rr_flag]
                    for i in range(len(channels)):
                        if i in [0, 1, 2, 3, 8, 9]:
                            if channels[i] in dictionaries.objectives:  
                                if channels[i] in dictionaries.times:
                                    if dictionaries.times[channels[i]][1] < item[2][1]:
                                        flags[i] = False
                            else:
                                flags[i] = False
                        else:
                            if channels[i] + "_ms" in dictionaries.objectives:  
                                if channels[i] in dictionaries.times:
                                    if dictionaries.times[channels[i]][1] < item[2][1]:
                                        flags[i] = False
                            else:
                                flags[i] = False
                    
                    for i in range(4):
                        if not flags[i]:
                            level_1 = False
                    for i in range(4, 6):
                        if not flags[i]:
                            level_2 = False
                    for i in range(6, 8):
                        if not flags[i]:
                            level_3 = False  
                    for i in range(8, 10):
                        if not flags[i]:
                            level_4 = False     

                    if ("ESC_PartialBrkinTurn" == item[0] or "ABS" in item[0]) and level_1:
                        time_perc_slip_ratio_neg, time_perc_slip_ratio_pos = self.time_slip_ratio(item, dictionaries, reference_string_speed[k], wheel_slip_check, level_2, level_3, level_4)
                        peak_list = [time_perc_slip_ratio_pos, time_perc_slip_ratio_neg]
                        for j in range(len(observer_list)):
                            if peak_list[j] != "ACQUISITION ERROR" and peak_list[j] != "" and peak_list[j] != "N/A":
                                observer_list[j].append(round(peak_list[j]))
                            else:
                                observer_list[j].append(peak_list[j])
                    else:
                        if not level_1:
                            wheel_slip_check.append(False)
                            for item in observer_list:
                                item.append("N/A")
                        else:
                            wheel_slip_check.append(False)
                            for item in observer_list:
                                item.append("")
            else:
                for item in observer_list:
                    wheel_slip_check.append(False)
                    item.append("ACQUISITION ERROR")
            k += 1


        for indexes in observer_list:
            parameters_list.append(indexes)

    def speed_estimation(self, maneuvers, dictionaries, parameters_list):
        speed_accuracy_avg_FA = ["Veh_spd_accur_avg_10kph_FA"]
        speed_accuracy_avg_RA = ["Veh_spd_accur_avg_10kph_RA"]
        speed_accuracy_avg_abs_FA = ["Veh_spd_accur_avg_abs_10kph_FA"]
        speed_accuracy_avg_abs_RA = ["Veh_spd_accur_avg_abs_10kph_RA"]
        observer_list = [speed_accuracy_avg_FA, speed_accuracy_avg_RA, speed_accuracy_avg_abs_FA, speed_accuracy_avg_abs_RA]
        i = 0
        for item in maneuvers.maneuvre:
            speed_control_FA = False
            speed_control_RA = False
            reference_control = False
            if "VehicleSpeed_FA_ms" in dictionaries.objectives:
                if "VehicleSpeed_FA" in dictionaries.times:
                    if dictionaries.times["VehicleSpeed_FA"][1] > item[2][1]:
                        speed_control_FA = True
                else:
                    speed_control_FA = True
            else:
                accuracy_avg_abs_FA = ""
                accuracy_avg_FA = ""
            
            if "VehicleSpeed_ms" in dictionaries.objectives:
                if "VehicleSpeed" in dictionaries.times:
                    if dictionaries.times["VehicleSpeed"][1] > item[2][1]:
                        speed_control_RA = True
                else:
                    speed_control_RA = True
            else:
                accuracy_avg_abs_RA = ""
                accuracy_avg_RA = ""

            if maneuvers.reference_string_speed[i] + "_ms" in dictionaries.objectives:
                if maneuvers.reference_string_speed[i] in dictionaries.times:
                    if dictionaries.times[maneuvers.reference_string_speed[i]][1] > item[2][1]:
                        reference_control = True
                else:
                    reference_control = True

            if speed_control_FA and reference_control:
                accuracy_avg_FA, accuracy_avg_abs_FA = self.speed_accuracy(dictionaries, item, maneuvers.reference_string_speed[i], "_FA")
            else:
                if reference_control:
                    pass
                else:
                    accuracy_avg_abs_FA = "ACQUISITION ERROR"
                    accuracy_avg_FA = "ACQUISITION ERROR"
            if speed_control_RA and reference_control:
                accuracy_avg_RA, accuracy_avg_abs_RA = self.speed_accuracy(dictionaries, item, maneuvers.reference_string_speed[i], "")
            else:
                if reference_control:
                    pass
                else:
                    accuracy_avg_abs_RA = "ACQUISITION ERROR"
                    accuracy_avg_RA = "ACQUISITION ERROR"            
            peak_list = [accuracy_avg_FA, accuracy_avg_RA, accuracy_avg_abs_FA, accuracy_avg_abs_RA]
            for j in range(len(observer_list)):
                if peak_list[j] != "" and peak_list[j] != "ACQUISITION ERROR":
                    observer_list[j].append(round(peak_list[j], 2))
                else:
                    observer_list[j].append(peak_list[j])
            i += 1
        for indexes in observer_list:
            parameters_list.append(indexes)
 
    def slip_performances(self, maneuvers, dictionaries, parameters_list):
        slip_target_accuracy_FL = ["Sliptarget_accur_avg_FL"]
        slip_target_accuracy_FR = ["Sliptarget_accur_avg_FR"]
        slip_target_accuracy_RL = ["Sliptarget_accur_avg_RL"]
        slip_target_accuracy_RR = ["Sliptarget_accur_avg_RR"]
        slip_control_accuracy_FL = ["Slipcontrol_accuracy_FL"]
        slip_control_accuracy_FR = ["Slipcontrol_accuracy_FR"]
        slip_control_accuracy_RL = ["Slipcontrol_accuracy_RL"]
        slip_control_accuracy_RR = ["Slipcontrol_accuracy_RR"]
        reference_string_speed = maneuvers.reference_string_speed
        speed_control = False
        trigger_control = False
        observer_list = [slip_target_accuracy_FL, slip_target_accuracy_FR, slip_target_accuracy_RL, slip_target_accuracy_RR, slip_control_accuracy_FL, slip_control_accuracy_FR, slip_control_accuracy_RL, slip_control_accuracy_RR]
        i = 0
        for item in maneuvers.maneuvre:
            if maneuvers.reference_string_speed[i] + "_ms" in dictionaries.objectives and "ABSTrigger_FL" in dictionaries.objectives:
                if maneuvers.reference_string_speed[i] in dictionaries.times or "ABSTrigger_FL" in dictionaries.times:
                    if maneuvers.reference_string_speed[i] in dictionaries.times:
                        if dictionaries.times[maneuvers.reference_string_speed[i]][1] > item[2][1]:
                            speed_control = True
                    if "ABSTrigger_FL" in dictionaries.times:
                        if dictionaries.times["ABSTrigger_FL"][1] > item[2][1]:
                            trigger_control = True            
                    if speed_control and trigger_control > item[2][1]:
                        if "ABS" in item[0]:
                            accuracy_FL, slip_difference_FL, check_abs_FL, time_int_FL, vbox_speed_FL, slip_setpoint_FL = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "FL")
                            accuracy_FR, slip_difference_FR, check_abs_FR, time_int_FR, vbox_speed_FR, slip_setpoint_FR = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "FR")
                            accuracy_RL, slip_difference_RL, check_abs_RL, time_int_RL, vbox_speed_RL, slip_setpoint_RL = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "RL")
                            accuracy_RR, slip_difference_RR, check_abs_RR, time_int_RR, vbox_speed_RR, slip_setpoint_RR = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "RR")
                            if check_abs_FL:
                                control_FL = self.slip_control_accuracy(slip_difference_FL, time_int_FL, vbox_speed_FL, slip_setpoint_FL)
                                if control_FL != "":
                                    control_FL = round(control_FL, 2)
                            else:
                                control_FL = ""
                            if check_abs_FR:
                                control_FR = self.slip_control_accuracy(slip_difference_FR, time_int_FR, vbox_speed_FR, slip_setpoint_FR)
                                if control_FR != "":
                                    control_FR = round(control_FR, 2)
                            else:
                                control_FR = ""
                            if check_abs_RL:
                                control_RL = self.slip_control_accuracy(slip_difference_RL, time_int_RL, vbox_speed_RL, slip_setpoint_RL)
                                if control_RL != "":
                                    control_RL = round(control_RL, 2)
                            else:
                                control_RL = ""
                            if check_abs_RR:    
                                control_RR = self.slip_control_accuracy(slip_difference_RR, time_int_RR, vbox_speed_RR, slip_setpoint_RR)
                                if control_RR != "":
                                    control_RR = round(control_RR, 2)
                            else:
                                control_RR = ""
                            peak_list = [accuracy_FL, accuracy_FR, accuracy_RL, accuracy_RR, control_FL, control_FR, control_RL, control_RR]
                            for j in range(len(observer_list)):
                                if peak_list[j] != "N/A" and peak_list[j] != "":
                                    observer_list[j].append(round(peak_list[j], 2))
                                else:
                                    observer_list[j].append(peak_list[j])
                        else:
                            for item in observer_list:
                                item.append("")
                    else:
                        for item in observer_list:
                            item.append("ACQUISITION ERROR")
                else:
                    if "ABS" in item[0]:
                        accuracy_FL, slip_difference_FL, check_abs_FL, time_int_FL, vbox_speed_FL, slip_setpoint_FL = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "FL")
                        accuracy_FR, slip_difference_FR, check_abs_FR, time_int_FR, vbox_speed_FR, slip_setpoint_FR = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "FR")
                        accuracy_RL, slip_difference_RL, check_abs_RL, time_int_RL, vbox_speed_RL, slip_setpoint_RL = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "RL")
                        accuracy_RR, slip_difference_RR, check_abs_RR, time_int_RR, vbox_speed_RR, slip_setpoint_RR = self.slip_target_accuracy(item, dictionaries, reference_string_speed[i], "RR")
                        if check_abs_FL:
                            control_FL = self.slip_control_accuracy(slip_difference_FL, time_int_FL, vbox_speed_FL, slip_setpoint_FL)
                            if control_FL != "":
                                control_FL = round(control_FL, 2)
                        else:
                            control_FL = ""
                        if check_abs_FR:
                            control_FR = self.slip_control_accuracy(slip_difference_FR, time_int_FR, vbox_speed_FR, slip_setpoint_FR)
                            if control_FR != "":
                                control_FR = round(control_FR, 2)
                        else:
                            control_FR = ""
                        if check_abs_RL:
                            control_RL = self.slip_control_accuracy(slip_difference_RL, time_int_RL, vbox_speed_RL, slip_setpoint_RL)
                            if control_RL != "":
                                control_RL = round(control_RL, 2)
                        else:
                            control_RL = ""
                        if check_abs_RR:    
                            control_RR = self.slip_control_accuracy(slip_difference_RR, time_int_RR, vbox_speed_RR, slip_setpoint_RR)
                            if control_RR != "":
                                control_RR = round(control_RR, 2)
                        else:
                            control_RR = ""
                        peak_list = [accuracy_FL, accuracy_FR, accuracy_RL, accuracy_RR, control_FL, control_FR, control_RL, control_RR]
                        for j in range(len(observer_list)):
                            if peak_list[j] != "N/A" and peak_list[j] != "":
                                observer_list[j].append(round(peak_list[j], 2))
                            else:
                                observer_list[j].append(peak_list[j])
                    else:
                        for item in observer_list:
                            item.append("")
            else:
                if maneuvers.reference_string_speed[i] + "_ms" in dictionaries.objectives:
                    for item in observer_list:
                        item.append("N/A")
                else:
                    for item in observer_list:
                        item.append("ACQUISITION ERROR")       
        for indexes in observer_list:
            parameters_list.append(indexes)

    def adherence_performances(self, dictionaries, maneuvers, parameters_list):
        adh_road = ["Adh_Road"]
        adh_usage = ["Adh_Usage"]
        adh_usage_FL = ["Adh_Usage_FL"]
        adh_usage_FR = ["Adh_Usage_FR"]
        adh_usage_RL = ["Adh_Usage_RL"]
        adh_usage_RR = ["Adh_Usage_RR"]
        road_adh_start_FL = ["RoadAdherenceStartFL"]
        road_adh_start_FR = ["RoadAdherenceStartFR"]
        road_adh_start_RL = ["RoadAdherenceStartRL"]
        road_adh_start_RR = ["RoadAdherenceStartRR"]
        slip_max_FL = ["SlipMax_FL"]
        slip_mean_FL = ["SlipMean_FL"]
        speed_at_max_slip_FL = ["VelocityAtMaxSlipFL"]
        slip_max_FR = ["SlipMax_FR"]
        slip_mean_FR = ["SlipMean_FR"]
        speed_at_max_slip_FR = ["VelocityAtMaxSlipFR"]
        slip_max_RL = ["SlipMax_RL"]
        slip_mean_RL = ["SlipMean_RL"]
        speed_at_max_slip_RL = ["VelocityAtMaxSlipRL"]
        slip_max_RR = ["SlipMax_RR"]
        slip_mean_RR = ["SlipMean_RR"]
        speed_at_max_slip_RR = ["VelocityAtMaxSlipRR"]
        adherencedelay_FL = ["AdherenceDelay_FL"]
        adherencedelay_FR = ["AdherenceDelay_FR"]
        adherencedelay_RL = ["AdherenceDelay_RL"]
        adherencedelay_RR = ["AdherenceDelay_RR"]
        correct_adherence_FL = ["Perc. of correct extimation FL"]
        correct_adherence_FR = ["Perc. of correct extimation FR"]
        correct_adherence_RL = ["Perc. of correct extimation RL"]
        correct_adherence_RR = ["Perc. of correct extimation RR"]
        reference_string_speed = maneuvers.reference_string_speed
        channels_check = ["Adherence_FL", "Adherence_FR", "Adherence_RL", "Adherence_RR", "ABSTrigger_FL", "ABSTrigger_FR", "ABSTrigger_RL", "ABSTrigger_RR", "Ax"]
        observer_list = [adh_road, adh_usage, adh_usage_FL, adh_usage_FR, adh_usage_RL, adh_usage_RR, road_adh_start_FL, road_adh_start_FR, road_adh_start_RL, road_adh_start_RR, slip_max_FL, slip_mean_FL, speed_at_max_slip_FL, slip_max_FR, slip_mean_FR, speed_at_max_slip_FR, slip_max_RL, slip_mean_RL, speed_at_max_slip_RL, slip_max_RR, slip_mean_RR, speed_at_max_slip_RR, adherencedelay_FL, adherencedelay_FR, adherencedelay_RL, adherencedelay_RR, correct_adherence_FL, correct_adherence_FR, correct_adherence_RL, correct_adherence_RR]
        k = 0
        for item in maneuvers.maneuvre:
            flag_1 = True
            flag_2 = True
            flag_3 = True
            flag_4 = True
            flag_5 = True
            flag_6 = True
            flag_7 = True
            flag_8 = True
            flag_9 = True
            flags = [flag_1, flag_2, flag_3, flag_4, flag_5, flag_6, flag_7, flag_8, flag_9]
            for i in range(len(channels_check)):
                if channels_check[i] in dictionaries.objectives:
                    if channels_check[i] in dictionaries.times:
                        if dictionaries.times[channels_check[i]][1] < item[2][1]:
                            flags[i] = False
                else:
                    flags[i] = False
            if "ABS" in item[0]:
                flag_road_adh = True
                for ogg in flags:
                    if not ogg:
                        flag_road_adh = False
                        break
                if flag_road_adh:
                    road_adh = self.adherence_road(dictionaries, item)
                else:
                    road_adh = "N/A"
                flag_adh_usage = True
                for i in range(4):
                    if not flags[i]:
                        flag_adh_usage = False
                        break
                if not flags[-1]:
                    flag_adh_usage = False
                if flag_adh_usage:
                    usage_adh, usage_adh_FL, usage_adh_FR, usage_adh_RL, usage_adh_RR = self.adherence_usage(dictionaries, item, reference_string_speed[k])
                else:
                    usage_adh = "N/A"
                    usage_adh_FL = "N/A"
                    usage_adh_FR = "N/A"
                    usage_adh_RL = "N/A"
                    usage_adh_RR = "N/A"
                if flag_road_adh:
                    adh_road_FL = self.adherence_ABS(dictionaries, item, "FL")
                    adh_road_FR = self.adherence_ABS(dictionaries, item, "FR")
                    adh_road_RL = self.adherence_ABS(dictionaries, item, "RL")
                    adh_road_RR = self.adherence_ABS(dictionaries, item, "RR")
                else:
                    adh_road_FL = "N/A"
                    adh_road_FR = "N/A"
                    adh_road_RL = "N/A"
                    adh_road_RR = "N/A"
                max_slip_FL = "ACQUISITION ERROR"
                max_slip_FR = "ACQUISITION ERROR"
                max_slip_RL = "ACQUISITION ERROR"
                max_slip_RR = "ACQUISITION ERROR"
                mean_slip_FL = "ACQUISITION ERROR"
                mean_slip_FR = "ACQUISITION ERROR"
                mean_slip_RL = "ACQUISITION ERROR"
                mean_slip_RR = "ACQUISITION ERROR"
                velocity_at_max_slip_FL = "ACQUISITION ERROR"
                velocity_at_max_slip_FR = "ACQUISITION ERROR"
                velocity_at_max_slip_RL = "ACQUISITION ERROR"
                velocity_at_max_slip_RR = "ACQUISITION ERROR"
                if reference_string_speed[k] == "ReferenceSpeed" or reference_string_speed[k] == "RawSpeed" or reference_string_speed[k] == "OpticalSpeed":
                    if "WheelSpeed_FL_ms" in dictionaries.objectives:
                        if "WheelSpeed_FL" in dictionaries.times:
                            if dictionaries.times["WheelSpeed_FL"][1] > item[2][1]:
                                max_slip_FL, mean_slip_FL, velocity_at_max_slip_FL = self.max_slip_adherence(dictionaries, item, "FL", reference_string_speed[k])
                                max_slip_FR, mean_slip_FR, velocity_at_max_slip_FR = self.max_slip_adherence(dictionaries, item, "FR", reference_string_speed[k])
                                max_slip_RL, mean_slip_RL, velocity_at_max_slip_RL = self.max_slip_adherence(dictionaries, item, "RL", reference_string_speed[k])
                                max_slip_RR, mean_slip_RR, velocity_at_max_slip_RR = self.max_slip_adherence(dictionaries, item, "RR", reference_string_speed[k])
                        else:
                            max_slip_FL, mean_slip_FL, velocity_at_max_slip_FL = self.max_slip_adherence(dictionaries, item, "FL", reference_string_speed[k])
                            max_slip_FR, mean_slip_FR, velocity_at_max_slip_FR = self.max_slip_adherence(dictionaries, item, "FR", reference_string_speed[k])
                            max_slip_RL, mean_slip_RL, velocity_at_max_slip_RL = self.max_slip_adherence(dictionaries, item, "RL", reference_string_speed[k])
                            max_slip_RR, mean_slip_RR, velocity_at_max_slip_RR = self.max_slip_adherence(dictionaries, item, "RR", reference_string_speed[k])
                if flag_road_adh:
                    adherence_delay_FL, correct_estimation_FL = self.correct_adherence_estimation(dictionaries, item, "FL")
                    adherence_delay_FR, correct_estimation_FR = self.correct_adherence_estimation(dictionaries, item, "FR")
                    adherence_delay_RL, correct_estimation_RL = self.correct_adherence_estimation(dictionaries, item, "RL")
                    adherence_delay_RR, correct_estimation_RR = self.correct_adherence_estimation(dictionaries, item, "RR")
                else:
                    adherence_delay_FL = "N/A"
                    correct_estimation_FL = "N/A"
                    adherence_delay_FR = "N/A"
                    correct_estimation_FR = "N/A"
                    adherence_delay_RL = "N/A"
                    correct_estimation_RL = "N/A"
                    adherence_delay_RR = "N/A"
                    correct_estimation_RR = "N/A"
                peak_list = [road_adh, usage_adh, usage_adh_FL, usage_adh_FR, usage_adh_RL, usage_adh_RR, adh_road_FL, adh_road_FR, adh_road_RL, adh_road_RR, max_slip_FL, mean_slip_FL, velocity_at_max_slip_FL, max_slip_FR, mean_slip_FR, velocity_at_max_slip_FR, max_slip_RL, mean_slip_RL, velocity_at_max_slip_RL, max_slip_RR, mean_slip_RR, velocity_at_max_slip_RR, adherence_delay_FL, adherence_delay_FR, adherence_delay_RL, adherence_delay_RR, correct_estimation_FL, correct_estimation_FR, correct_estimation_RL, correct_estimation_RR]
                for j in range(len(observer_list)):
                    if peak_list[j] != "N/A" and peak_list[j] != "" and peak_list[j] != "Not found" and peak_list[j] != "ACQUISITION ERROR":
                        observer_list[j].append(round(peak_list[j], 2))
                    else:
                        observer_list[j].append(peak_list[j])
            elif "ESC_Handling" == item[0]:
                max_slip_FL = "ACQUISITION ERROR"
                max_slip_FR = "ACQUISITION ERROR"
                max_slip_RL = "ACQUISITION ERROR"
                max_slip_RR = "ACQUISITION ERROR"
                velocity_at_max_slip_FL = "ACQUISITION ERROR"
                velocity_at_max_slip_FR = "ACQUISITION ERROR"
                velocity_at_max_slip_RL = "ACQUISITION ERROR"
                velocity_at_max_slip_RR = "ACQUISITION ERROR"
                if reference_string_speed[k] == "ReferenceSpeed" or reference_string_speed[k] == "RawSpeed" or reference_string_speed[k] == "OpticalSpeed":
                    if "WheelSpeed_FL_ms" in dictionaries.objectives:
                        if "WheelSpeed_FL" in dictionaries.times:
                            if dictionaries.times["WheelSpeed_FL"][1] > item[2][1]:
                                max_slip_FL, mean_slip_FL, velocity_at_max_slip_FL = self.max_slip_adherence(dictionaries, item, "FL", reference_string_speed[k])
                                max_slip_FR, mean_slip_FR, velocity_at_max_slip_FR = self.max_slip_adherence(dictionaries, item, "FR", reference_string_speed[k])
                                max_slip_RL, mean_slip_RL, velocity_at_max_slip_RL = self.max_slip_adherence(dictionaries, item, "RL", reference_string_speed[k])
                                max_slip_RR, mean_slip_RR, velocity_at_max_slip_RR = self.max_slip_adherence(dictionaries, item, "RR", reference_string_speed[k])
                        else:
                            max_slip_FL, mean_slip_FL, velocity_at_max_slip_FL = self.max_slip_adherence(dictionaries, item, "FL", reference_string_speed[k])
                            max_slip_FR, mean_slip_FR, velocity_at_max_slip_FR = self.max_slip_adherence(dictionaries, item, "FR", reference_string_speed[k])
                            max_slip_RL, mean_slip_RL, velocity_at_max_slip_RL = self.max_slip_adherence(dictionaries, item, "RL", reference_string_speed[k])
                            max_slip_RR, mean_slip_RR, velocity_at_max_slip_RR = self.max_slip_adherence(dictionaries, item, "RR", reference_string_speed[k])
                for ogg in [adh_road, adh_usage, adh_usage_FL, adh_usage_FR, adh_usage_RL, adh_usage_RR, road_adh_start_FL, road_adh_start_FR, road_adh_start_RL, road_adh_start_RR, slip_mean_FL, slip_mean_FR, slip_mean_RL, slip_mean_RR, adherencedelay_FL, adherencedelay_FR, adherencedelay_RL, adherencedelay_RR, correct_adherence_FL, correct_adherence_FR, correct_adherence_RL, correct_adherence_RR]:
                    ogg.append("")
                if type(max_slip_FL) != str:
                    slip_max_FL.append(round(max_slip_FL, 2))
                else:
                    slip_max_FL.append(max_slip_FL)
                if type(max_slip_FR) != str:
                    slip_max_FR.append(round(max_slip_FR, 2))
                else:
                    slip_max_FR.append(max_slip_FR)
                if type(max_slip_RL) != str:
                    slip_max_RL.append(round(max_slip_RL, 2))
                else:
                    slip_max_RL.append(max_slip_RL)
                if type(max_slip_RR) != str:
                    slip_max_RR.append(round(max_slip_RR, 2))
                else:
                    slip_max_RR.append(max_slip_RR)
                if type(velocity_at_max_slip_FL) != str:
                    speed_at_max_slip_FL.append(round(velocity_at_max_slip_FL, 2))
                else:
                    speed_at_max_slip_FL.append(velocity_at_max_slip_FL)
                if type(velocity_at_max_slip_FR) != str:
                    speed_at_max_slip_FR.append(round(velocity_at_max_slip_FR, 2))
                else:
                    speed_at_max_slip_FR.append(velocity_at_max_slip_FR)
                if type(velocity_at_max_slip_RL) != str:
                    speed_at_max_slip_RL.append(round(velocity_at_max_slip_RL, 2))
                else:
                    speed_at_max_slip_RL.append(velocity_at_max_slip_RL)
                if type(velocity_at_max_slip_RR) != str:
                    speed_at_max_slip_RR.append(round(velocity_at_max_slip_RR, 2))
                else:
                    speed_at_max_slip_RR.append(velocity_at_max_slip_RR)
            else:
                for ogg in observer_list:
                    ogg.append("")
            k += 1
        for indexes in observer_list:
            parameters_list.append(indexes)

    def reaction_performances(self, dictionaries, maneuvers, parameters_list, pedal_type):
        time_bite = ["Time_bite"]
        ax_peak_500 = ["Ax_Peak_500ms"]
        time_peak_500 = ["Time_peak_500ms"]
        time_to_lock_FL = ["TimeToLock_FL"]
        time_to_lock_FR = ["TimeToLock_FR"]
        time_to_lock_RL = ["TimeToLock_RL"]
        time_to_lock_RR = ["TimeToLock_RR"]
        wheelslip_at_lock_FL = ["WheelSlipLock_FL"]
        wheelslip_at_lock_FR = ["WheelSlipLock_FR"]
        wheelslip_at_lock_RL = ["WheelSlipLock_RL"]
        wheelslip_at_lock_RR = ["WheelSlipLock_RR"]
        observer_list = [time_bite, ax_peak_500, time_peak_500, time_to_lock_FL, time_to_lock_FR, time_to_lock_RL, time_to_lock_RR, wheelslip_at_lock_FL, wheelslip_at_lock_FR, wheelslip_at_lock_RL, wheelslip_at_lock_RR]
        i = 0
        for item in maneuvers.maneuvre:
            i += 1
            flag_speed = True
            if maneuvers.reference_string_speed[i-1] + "_ms" in dictionaries.objectives:
                if maneuvers.reference_string_speed[i-1] in dictionaries.times:
                    if dictionaries.times[maneuvers.reference_string_speed[i-1]][1] < item[2][1]:
                        flag_speed = False
            else:
                flag_speed = False
            channels_check = ["WheelSpeed_FL", "WheelSpeed_FR", "WheelSpeed_RL", "WheelSpeed_RR", "ABSTrigger_FL", "ABSTrigger_FR", "ABSTrigger_RL", "ABSTrigger_RR", "Ax"]
            flag_1 = True
            flag_2 = True
            flag_3 = True
            flag_4 = True
            flag_5 = True
            flag_6 = True
            flag_7 = True
            flag_8 = True
            flag_9 = True
            flags = [flag_1, flag_2, flag_3, flag_4, flag_5, flag_6, flag_7, flag_8, flag_9]
            flag_lock = True
            for j in range(len(channels_check)):
                if j < 4:
                    if channels_check[j] + "_ms" in dictionaries.objectives:
                        if channels_check[j] in dictionaries.times:
                            if dictionaries.times[channels_check[j]][1] < item[2][1]:
                                flags[j] = False
                    else:
                        flags[j] = False
                else:
                    if channels_check[j] in dictionaries.objectives:
                        if channels_check[j] in dictionaries.times:
                            if dictionaries.times[channels_check[j]][1] < item[2][1]:
                                flags[j] = False
                    else:
                        flags[j] = False
            for j in range(8):
                if not flags[j]:
                    flag_lock = False
                    break
            if "ABS" in item[0]:
                if flags[-1]:
                    bite_timing = self.bite_time(dictionaries, item)
                    peak_ax_500, peak_time_500 = self.peak_500(dictionaries, item)
                else:
                    bite_timing = "ACQUISITION ERROR"
                    peak_ax_500 = "ACQUISITION ERROR"
                    peak_time_500 = "ACQUISITION ERROR"
                if pedal_type[i] == "SPIKE" and flag_lock and flag_speed:
                    lock_time_FL, wheelslip_lock_FL = self.lock_time(dictionaries, item, "FL", maneuvers.reference_string_speed[i-1])
                    lock_time_FR, wheelslip_lock_FR = self.lock_time(dictionaries, item, "FR", maneuvers.reference_string_speed[i-1])
                    lock_time_RL, wheelslip_lock_RL = self.lock_time(dictionaries, item, "RL", maneuvers.reference_string_speed[i-1])
                    lock_time_RR, wheelslip_lock_RR = self.lock_time(dictionaries, item, "RR", maneuvers.reference_string_speed[i-1])
                else:
                    if not flag_lock or not flag_speed:
                        lock_time_FL = "N/A"
                        wheelslip_lock_FL = "N/A"
                        lock_time_FR = "N/A"
                        wheelslip_lock_FR = "N/A"
                        lock_time_RL = "N/A"
                        wheelslip_lock_RL = "N/A"
                        lock_time_RR = "N/A"
                        wheelslip_lock_RR = "N/A"
                    else:
                        lock_time_FL = ""
                        wheelslip_lock_FL = ""
                        lock_time_FR = ""
                        wheelslip_lock_FR = ""
                        lock_time_RL = ""
                        wheelslip_lock_RL = ""
                        lock_time_RR = ""
                        wheelslip_lock_RR = ""
                peak_list = [bite_timing, peak_ax_500, peak_time_500, lock_time_FL, lock_time_FR, lock_time_RL, lock_time_RR, wheelslip_lock_FL, wheelslip_lock_FR, wheelslip_lock_RL, wheelslip_lock_RR]
                for j in range(len(observer_list)):
                    if peak_list[j] != "N/A" and peak_list[j] != "" and peak_list[j] != "ACQUISITION ERROR":
                        observer_list[j].append(round(peak_list[j], 2))
                    else:
                        observer_list[j].append(peak_list[j])
            else:
                for item in observer_list:
                    item.append("")
        for indexes in observer_list:
            parameters_list.append(indexes)
 
    def TCS_performances(self, dictionaries, maneuvers, parameters_list):
        launch_time_0_5kph = ["launch_time_0_5kph"]
        launch_time_0_15kph = ["launch_time_0_15kph"]
        launch_time_0_30kph = ["launch_time_0_30kph"]
        launch_time_0_50kph = ["launch_time_0_50kph"]
        launch_time_0_100kph = ["launch_time_0_100kph"]
        reference_string_speed = maneuvers.reference_string_speed
        observers_list = [launch_time_0_5kph, launch_time_0_15kph, launch_time_0_30kph, launch_time_0_50kph, launch_time_0_100kph]
        i = 0
        for item in maneuvers.maneuvre:
            if "TCS" in item[0]:
                launch_0_5 = self.launch_time(dictionaries, item, 5, reference_string_speed[i])
                launch_0_15 = self.launch_time(dictionaries, item, 15, reference_string_speed[i])
                launch_0_30 = self.launch_time(dictionaries, item, 30, reference_string_speed[i])
                launch_0_50 = self.launch_time(dictionaries, item, 50, reference_string_speed[i])
                launch_0_100 = self.launch_time(dictionaries, item, 100, reference_string_speed[i])
                peak_list = [launch_0_5, launch_0_15, launch_0_30, launch_0_50, launch_0_100]
                for j in range(len(observers_list)):
                    if peak_list[j] != "N/A" and peak_list[j] != "":
                        observers_list[j].append(round(peak_list[j], 2))
                    else:
                        observers_list[j].append(peak_list[j])
            else:
                for obj in observers_list:
                    obj.append("")
            i += 1
        for indexes in observers_list:
            parameters_list.append(indexes)

    def roll_rate(self, dictionaries, maneuver, parameters_list, excel_bigol_list):
        roll_rate_max = ["Delta_RollRate_Max"]
        roll_rate_bandwidth = ["RollRate_Bandwidth"]
        roll_rate_rms = ["RollRate_RMS"]
        observer_list = [roll_rate_max, roll_rate_bandwidth, roll_rate_rms]
        cont = 0
        for item in maneuver.maneuvre:
            if "ESC" in item[0] and "ESC_PartialBrkinTurn" != item[0] and "ESC_Handling" != item[0]:
                start = item[3][0]
                end = item[3][1]
            else:
                start = item[2][0]
                end = item[2][1]
            if "RollRate_degs" in dictionaries.objectives:
                if "RollRate" in dictionaries.times:
                    if dictionaries.times["RollRate"][1] >= end:
                        single_roll_rate_max = max(abs(dictionaries.objectives["RollRate_degs"][start:end]))
                        single_roll_rate_bandwidth = max(dictionaries.objectives["RollRate_degs"][start:end]) - min(dictionaries.objectives["RollRate_degs"][start:end])
                        single_roll_rate_rms = np.sqrt(1/len(dictionaries.objectives["RollRate_degs"][start:end])*np.sum(dictionaries.objectives["RollRate_degs"][start:end]**2))
                        peak_list = [single_roll_rate_max, single_roll_rate_bandwidth, single_roll_rate_rms]
                        if "YawRate_degs" in dictionaries.objectives:
                            if "YawRate" in dictionaries.times:
                                if dictionaries.times["YawRate"][1] >= item[2][1]:
                                    if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                        excel_bigol_list[cont].append(list(dictionaries.objectives["RollRate_degs"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                        cont += 1
                            else:
                                if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["RollRate_degs"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                        for i in range(len(observer_list)):
                            observer_list[i].append(round(peak_list[i], 2))
                    else:
                        for i in range(len(observer_list)):
                            observer_list[i].append("ACQUISITION ERROR")
                else:
                    single_roll_rate_max = max(abs(dictionaries.objectives["RollRate_degs"][start:end]))
                    single_roll_rate_bandwidth = max(dictionaries.objectives["RollRate_degs"][start:end]) - min(dictionaries.objectives["RollRate_degs"][start:end])
                    single_roll_rate_rms = np.sqrt(1/len(dictionaries.objectives["RollRate_degs"][start:end])*np.sum(dictionaries.objectives["RollRate_degs"][start:end]**2))
                    peak_list = [single_roll_rate_max, single_roll_rate_bandwidth, single_roll_rate_rms]
                    if "YawRate_degs" in dictionaries.objectives:
                        if "YawRate" in dictionaries.times:
                            if dictionaries.times["YawRate"][1] >= item[2][1]:
                                if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                    excel_bigol_list[cont].append(list(dictionaries.objectives["RollRate_degs"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                    cont += 1
                        else:
                            if item[0] == "ABS_InTurn" or (item[0] == "ABS_Braking" and abs(dictionaries.objectives["YawRate_degs"][item[2][0]]) > 3):
                                excel_bigol_list[cont].append(list(dictionaries.objectives["RollRate_degs"][item[2][0] - int(0.5*dictionaries.frequency): item[2][1]]))
                                cont += 1
                    for i in range(len(observer_list)):
                        observer_list[i].append(round(peak_list[i], 2))            
            else:
                for i in range(len(observer_list)):
                    observer_list[i].append("")
 
        for indexes in observer_list:
            parameters_list.append(indexes)

    def dynamic_performances(self, dictionaries, maneuver, parameters_list, direction_check):
        beta_max = ["Max_Beta"]
        bsa_max = ["Max_BSA"]
        bsaa_max = ["Max_BSAA"]
        bsae_max = ["Max_BSAE"]
        speed_beta_max = ["Speed@Max_Beta"]
        time_beta_max = ["Time@Max_Beta"]
        speed_bsa_max = ["Time@Max_BSA"]
        speed_bsaa_max = ["Time@Max_BSAA"]
        speed_bsae_max = ["Time@Max_BSAE"]
        bsa_beta_max = ["BSA@Max_Beta"]
        bsae_beta_max = ["BSAE@Max_Beta"]
        bsaa_beta_max = ["BSAA@Max_Beta"]
        int_bsa_beta = ["Integral BSA-Beta"]
        int_bsae_beta = ["Integral BSAE-Beta"]
        int_bsaa_beta = ["Integral BSAA-Beta"]
        rmse_bsa_beta = ["RMSE_BSA_Beta"]
        rmse_bsaa_beta = ["RMSE_BSAA_Beta"]
        rmse_bsae_beta = ["RMSE_BSAE_Beta"]
        max_under_bsa = ["Max_Underestimate_BSA"]
        max_under_bsaa = ["Max_Underestimate_BSAA"]
        max_under_bsae = ["Max_Underestimate_BSAE"]
        max_over_bsa = ["Max_Overestimate_BSA"]
        max_over_bsaa = ["Max_Overestimate_BSAA"]
        max_over_bsae = ["Max_Overestimate_BSAE"]
        bsaa_coherence = ["BSAA_Coherence"]
        bsae_coherence = ["BSAE_Coherence"]
        bsa_coherence = ["BSA_Coherence"]
        observer_list = [beta_max, speed_beta_max, time_beta_max, bsaa_max, speed_bsaa_max, bsaa_beta_max, bsae_max, speed_bsae_max, bsae_beta_max, bsa_max, speed_bsa_max, bsa_beta_max, int_bsaa_beta, int_bsae_beta, int_bsa_beta, rmse_bsaa_beta, rmse_bsae_beta, rmse_bsa_beta, max_under_bsaa, max_under_bsae, max_under_bsa, max_over_bsaa, max_over_bsae, max_over_bsa, bsaa_coherence, bsae_coherence, bsa_coherence]
        max_beta = ""
        speed_max_beta = ""
        max_bsa = ""
        speed_max_bsa = ""
        bsa_max_beta = ""
        max_bsae = ""
        speed_max_bsae = ""
        bsae_max_beta = ""
        max_bsaa = ""
        speed_max_bsaa = ""
        time_max_beta = ""
        bsaa_max_beta = ""
        int_bsa = ""
        int_bsaa = ""
        int_bsae = ""
        rmse_bsa = ""
        rmse_bsaa = ""
        rmse_bsae = ""
        under_bsa = ""
        under_bsaa = ""
        under_bsae = ""
        over_bsa = ""
        over_bsaa = ""
        over_bsae = ""
        coherence_bsaa = ""
        coherence_bsae = ""
        coherence_bsa = ""
        reference_string_speed = maneuver.reference_string_speed
        k = 0
        for item in maneuver.maneuvre:
            if "SideSlipAngle_deg" in dictionaries.objectives or "BSAAngle_deg" in dictionaries.objectives or "BSEAngle_deg" in dictionaries.objectives or "BodySlipAngle_deg" in dictionaries.objectives:
                flag_1 = True
                flag_2 = True
                flag_3 = True
                flag_4 = True
                if "SideSlipAngle_deg" in dictionaries.objectives:
                    if "SideSlipAngle" in dictionaries.times:
                        if dictionaries.times["SideSlipAngle"][1] < item[2][1]:
                            flag_1 = False
                else:
                    flag_1 = False
                if "BSAAngle_deg" in dictionaries.objectives:
                    if "BSAAngle" in dictionaries.times:
                        if dictionaries.times["BSAAngle"][1] < item[2][1]:
                            flag_2 = False
                else:
                    flag_2 = False
                if "BSEAngle_deg" in dictionaries.objectives:
                    if "BSEAngle" in dictionaries.times:
                        if dictionaries.times["BSEAngle"][1] < item[2][1]:
                            flag_3 = False
                else:
                    flag_3 = False
                if "BodySlipAngle_deg" in dictionaries.objectives:
                    if "BodySlipAngle" in dictionaries.times:
                        if dictionaries.times["BodySlipAngle"][1] < item[2][1]:
                            flag_4 = False
                else:
                    flag_4 = False
                
                if item[0] in ["ABS_Chessboard", "ABS_LaneChange", "ABS_MuSplit", "ABS_NegativeMuJump", "ABS_NegativeMuSplitJump", "ABS_PositiveMuJump", 
                                   "ABS_PositiveMuSplitJump", "ABS_StoppingDistance", "ABS_DoubleMuJump", "ESC_StepSteer", "ESC_RampSteer", "ESC_LaneChange",
                                   "ESC_Slalom"]:
                    beta = np.array([])
                    if direction_check and item[0] in ["ESC_StepSteer", "ESC_RampSteer", "ESC_LaneChange", "ESC_Slalom"]:
                        speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                        interesting_time = dictionaries.time_resampled[item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                        if flag_1:
                            beta = dictionaries.objectives["SideSlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                            if beta.size > 0:
                                start_beta = np.mean(dictionaries.objectives["SideSlipAngle_deg"][item[3][0] - int(round(0.5*dictionaries.frequency)):item[3][0]])
                                beta = beta - start_beta
                                max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                speed_max_beta = speed[np.argmax(abs(beta))]
                                time_max_beta = interesting_time[np.argmax(abs(beta))]
                        if flag_2:
                            if beta.size > 0:
                                bsaa = dictionaries.objectives["BSAAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                start_bsaa = np.mean(dictionaries.objectives["BSAAngle_deg"][item[3][0] - int(round(0.5*dictionaries.frequency)):item[3][0]])
                                bsaa = bsaa - start_bsaa
                                max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                if flag_1:
                                    bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                    bsaa_beta = bsaa - beta
                                    under_bsaa = min(bsaa_beta)
                                    over_bsaa = max(bsaa_beta)
                                    int_bsaa = 0
                                    rmse_bsaa = 0
                                    count_bsaa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                            count_bsaa.append(1)
                                    rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                    coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                        if flag_3:
                            if beta.size > 0:
                                bsae = dictionaries.objectives["BSEAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                start_bsae = np.mean(dictionaries.objectives["BSEAngle_deg"][item[3][0] - int(round(0.5*dictionaries.frequency)):item[3][0]])
                                bsae = bsae - start_bsae
                                max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                if flag_1:
                                    bsae_max_beta = bsae[np.argmax(abs(beta))]
                                    bsae_beta = bsae - beta
                                    under_bsae = min(bsae_beta)
                                    over_bsae = max(bsae_beta)
                                    int_bsae = 0
                                    rmse_bsae = 0
                                    count_bsae = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsae = rmse_bsae + (bsae[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsae[i]) and abs(beta[i]) > 1:
                                            count_bsae.append(1)
                                    rmse_bsae = (rmse_bsae/len(beta))**(1/2)
                                    coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                        if flag_4:
                            if beta.size > 0:
                                bsa = dictionaries.objectives["BodySlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                start_bsa = np.mean(dictionaries.objectives["BodySlipAngle_deg"][item[3][0] - int(round(0.5*dictionaries.frequency)):item[3][0]])
                                bsa = bsa - start_bsa
                                max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                if flag_1:
                                    bsa_max_beta = bsa[np.argmax(abs(beta))]
                                    bsa_beta = bsa - beta
                                    under_bsa = min(bsa_beta)
                                    over_bsa = max(bsa_beta)
                                    int_bsa = 0
                                    rmse_bsa = 0
                                    count_bsa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsa[i]) and abs(beta[i]) > 1:
                                            count_bsa.append(1)
                                    rmse_bsa = (rmse_bsa/len(beta))**(1/2)        
                                    coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)
                    else:
                        if item[0] in ["ESC_StepSteer", "ESC_RampSteer", "ESC_LaneChange", "ESC_Slalom"]:
                            interesting_time = dictionaries.time_resampled[item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                            speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                            if flag_1:
                                beta = dictionaries.objectives["SideSlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                if beta.size > 0:
                                    max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                    speed_max_beta = speed[np.argmax(abs(beta))]
                                    time_max_beta = interesting_time[np.argmax(abs(beta))]
                            if flag_2:
                                if beta.size > 0:
                                    bsaa = dictionaries.objectives["BSAAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                    max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                    speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                    if flag_1:
                                        bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                        bsaa_beta = bsaa - beta
                                        under_bsaa = min(bsaa_beta)
                                        over_bsaa = max(bsaa_beta)
                                        int_bsaa = 0
                                        rmse_bsaa = 0
                                        count_bsaa = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                                count_bsaa.append(1)
                                        rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                        coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                            if flag_3:
                                if beta.size > 0:
                                    bsae = dictionaries.objectives["BSEAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                    max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                    speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                    if flag_1:
                                        bsae_max_beta = bsae[np.argmax(abs(beta))]
                                        bsae_beta = bsae - beta
                                        under_bsae = min(bsae_beta)
                                        over_bsae = max(bsae_beta)
                                        int_bsae = 0
                                        rmse_bsae = 0
                                        count_bsae = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsae = rmse_bsae + (bsae[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsae[i]) and abs(beta[i]) > 1:
                                                count_bsae.append(1)
                                        rmse_bsae = (rmse_bsae/len(beta))**(1/2)        
                                        coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                            if flag_4:
                                if beta.size > 0:
                                    bsa = dictionaries.objectives["BodySlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                    max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                    speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                    if flag_1:
                                        bsa_max_beta = bsa[np.argmax(abs(beta))]
                                        bsa_beta = bsa - beta
                                        under_bsa = min(bsa_beta)
                                        over_bsa = max(bsa_beta)
                                        int_bsa = 0
                                        rmse_bsa = 0
                                        count_bsa = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                                count_bsa.append(1)
                                        rmse_bsa = (rmse_bsa/len(beta))**(1/2)
                                        coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)

                    if direction_check and item[0] in ["ABS_Chessboard", "ABS_LaneChange", "ABS_MuSplit", "ABS_NegativeMuJump", "ABS_NegativeMuSplitJump", 
                                                            "ABS_PositiveMuJump", "ABS_PositiveMuSplitJump", "ABS_StoppingDistance", "ABS_DoubleMuJump"]:
                        speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                        interesting_time = dictionaries.time_resampled[item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                        if flag_1:
                            beta = dictionaries.objectives["SideSlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                            if beta.size > 0:
                                start_beta = np.mean(dictionaries.objectives["SideSlipAngle_deg"][item[2][0] - int(round(0.5*dictionaries.frequency)):item[2][0]])
                                beta = beta - start_beta
                                max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                time_max_beta = interesting_time[np.argmax(abs(beta))]
                                speed_max_beta = speed[np.argmax(abs(beta))]
                        if flag_2:
                            if beta.size > 0:
                                bsaa = dictionaries.objectives["BSAAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                start_bsaa = np.mean(dictionaries.objectives["BSAAngle_deg"][item[2][0] - int(round(0.5*dictionaries.frequency)):item[2][0]])
                                bsaa = bsaa - start_bsaa
                                max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                if flag_1:
                                    bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                    bsaa_beta = bsaa - beta
                                    under_bsaa = min(bsaa_beta)
                                    over_bsaa = max(bsaa_beta)
                                    int_bsaa = 0
                                    rmse_bsaa = 0
                                    count_bsaa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                            count_bsaa.append(1)
                                    rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                    coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                        if flag_3:
                            if beta.size > 0:
                                bsae = dictionaries.objectives["BSEAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                start_bsae = np.mean(dictionaries.objectives["BSEAngle_deg"][item[2][0] - int(round(0.5*dictionaries.frequency)):item[2][0]])
                                bsae = bsae - start_bsae
                                max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                if flag_1:
                                    bsae_max_beta = bsae[np.argmax(abs(beta))]
                                    bsae_beta = bsae - beta
                                    under_bsae = min(bsae_beta)
                                    over_bsae = max(bsae_beta)
                                    int_bsae = 0
                                    rmse_bsae = 0
                                    count_bsae = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsae = rmse_bsae + (bsae[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsae[i]):
                                            count_bsae.append(1)
                                    rmse_bsae = (rmse_bsae/len(beta))**(1/2)
                                    coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                        if flag_4:
                            if beta.size > 0:
                                bsa = dictionaries.objectives["BodySlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                start_bsa = np.mean(dictionaries.objectives["BodySlipAngle_deg"][item[2][0] - int(round(0.5*dictionaries.frequency)):item[2][0]])
                                bsa = bsa - start_bsa
                                max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                if flag_1:
                                    bsa_max_beta = bsa[np.argmax(abs(beta))]
                                    bsa_beta = bsa - beta
                                    under_bsa = min(bsa_beta)
                                    over_bsa = max(bsa_beta)    
                                    int_bsa = 0
                                    rmse_bsa = 0
                                    count_bsa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsa[i]) and abs(beta[i]) > 1:
                                            count_bsa.append(1)
                                    rmse_bsa = (rmse_bsa/len(beta))**(1/2)
                                    coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)
                    else:
                        if item[0] in ["ABS_Chessboard", "ABS_LaneChange", "ABS_MuSplit", "ABS_NegativeMuJump", "ABS_NegativeMuSplitJump", "ABS_PositiveMuJump", 
                                   "ABS_PositiveMuSplitJump", "ABS_StoppingDistance", "ABS_DoubleMuJump"]:
                            speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                            interesting_time = dictionaries.time_resampled[item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                            if flag_1:
                                beta = dictionaries.objectives["SideSlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                if beta.size > 0:
                                    max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                    speed_max_beta = speed[np.argmax(abs(beta))]
                                    time_max_beta = interesting_time[np.argmax(abs(beta))]
                            if flag_2:
                                if beta.size > 0:
                                    bsaa = dictionaries.objectives["BSAAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                    max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                    speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                    if flag_1:
                                        bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                        bsaa_beta = bsaa - beta
                                        under_bsaa = min(bsaa_beta)
                                        over_bsaa = max(bsaa_beta)
                                        int_bsaa = 0
                                        rmse_bsaa = 0
                                        count_bsaa = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                                count_bsaa.append(1)
                                        rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                        coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                            if flag_3:
                                if beta.size > 0:
                                    bsae = dictionaries.objectives["BSEAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                    max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                    speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                    if flag_1:
                                        bsae_max_beta = bsae[np.argmax(abs(beta))]
                                        bsae_beta = bsae - beta
                                        under_bsae = min(bsae_beta)
                                        over_bsae = max(bsae_beta)
                                        int_bsae = 0
                                        rmse_bsae = 0
                                        count_bsae = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsae = rmse_bsae + (bsaa[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsae[i]) and abs(beta[i]) > 1:
                                                count_bsae.append(1)
                                    rmse_bsae = (rmse_bsae/len(beta))**(1/2)
                                    coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                            if flag_4:
                                if beta.size > 0:
                                    bsa = dictionaries.objectives["BodySlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                    max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                    speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                    if flag_1:
                                        bsa_max_beta = bsa[np.argmax(abs(beta))]
                                        bsa_beta = bsa - beta
                                        under_bsa = min(bsa_beta)
                                        over_bsa = max(bsa_beta)
                                        int_bsa = 0
                                        rmse_bsa = 0
                                        count_bsa = []
                                        for i in range(1, len(interesting_time)):
                                            int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                            rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                            if np.sign(beta[i]) != np.sign(bsa[i]) and abs(beta[i]) > 1:
                                                count_bsa.append(1)
                                    rmse_bsa = (rmse_bsa/len(beta))**(1/2)
                                    coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)

                else:
                    beta = np.array([])
                    if "ESC" in item[0] and item[0] != "ESC_PartialBrkinTurn" and item[0] != "ESC_Handling":
                        speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                        interesting_time = dictionaries.time_resampled[item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                        if flag_1:
                            beta = dictionaries.objectives["SideSlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                            if beta.size > 0:
                                max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                speed_max_beta = speed[np.argmax(abs(beta))]
                                time_max_beta = interesting_time[np.argmax(abs(beta))]
                        if flag_2:
                            if beta.size > 0:
                                bsaa = dictionaries.objectives["BSAAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                if flag_1:
                                    bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                    bsaa_beta = bsaa - beta
                                    under_bsaa = min(bsaa_beta)
                                    over_bsaa = max(bsaa_beta)
                                    int_bsaa = 0
                                    rmse_bsaa = 0
                                    count_bsaa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                            count_bsaa.append(1)
                                    rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                    coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                        if flag_3:
                            if beta.size > 0:
                                bsae = dictionaries.objectives["BSEAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                if flag_1:
                                    bsae_max_beta = bsae[np.argmax(abs(beta))]
                                    bsae_beta = bsae - beta
                                    under_bsae = min(bsae_beta)
                                    over_bsae = max(bsae_beta)   
                                    int_bsae = 0
                                    rmse_bsae = 0
                                    count_bsae = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsae = rmse_bsae + (bsae[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsae[i]) and abs(beta[i]) > 1:
                                            count_bsae.append(1)
                                    rmse_bsae = (rmse_bsae/len(beta))**(1/2)
                                    coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                        if flag_4:
                            if beta.size > 0:
                                bsa = dictionaries.objectives["BodySlipAngle_deg"][item[3][0]:item[3][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[3][0]:item[3][1]] > 25]
                                max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                if flag_1:
                                    bsa_max_beta = bsa[np.argmax(abs(beta))]
                                    bsa_beta = bsa - beta
                                    under_bsa = min(bsa_beta)
                                    over_bsa = max(bsa_beta)
                                    int_bsa = 0
                                    rmse_bsa = 0
                                    count_bsa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsa[i]) and abs(beta[i]) > 1:
                                            count_bsa.append(1)
                                    rmse_bsa = (rmse_bsa/len(beta))**(1/2)
                                    coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)
                    else:
                        speed = dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                        interesting_time = dictionaries.time_resampled[item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                        if flag_1:
                            beta = dictionaries.objectives["SideSlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                            if beta.size > 0:
                                max_beta = max(abs(beta))*np.sign(beta[np.argmax(abs(beta))])
                                speed_max_beta = speed[np.argmax(abs(beta))]
                                time_max_beta = interesting_time[np.argmax(abs(beta))]
                        if flag_2:
                            if beta.size > 0:
                                bsaa = dictionaries.objectives["BSAAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                max_bsaa = max(abs(bsaa))*np.sign(bsaa[np.argmax(abs(bsaa))])
                                speed_max_bsaa = interesting_time[np.argmax(abs(bsaa))]
                                if flag_1:
                                    bsaa_max_beta = bsaa[np.argmax(abs(beta))]
                                    bsaa_beta = bsaa - beta
                                    under_bsaa = min(bsaa_beta)
                                    over_bsaa = max(bsaa_beta)
                                    int_bsaa = 0
                                    rmse_bsaa = 0
                                    count_bsaa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsaa = int_bsaa + bsaa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsaa = rmse_bsaa + (bsaa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsaa[i]) and abs(beta[i]) > 1:
                                            count_bsaa.append(1)
                                    rmse_bsaa = (rmse_bsaa/len(beta))**(1/2)
                                    coherence_bsaa = 100 - (len(count_bsaa)/len(interesting_time)*100)
                        if flag_3:
                            if beta.size > 0:
                                bsae = dictionaries.objectives["BSEAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                max_bsae = max(abs(bsae))*np.sign(bsae[np.argmax(abs(bsae))])
                                speed_max_bsae = interesting_time[np.argmax(abs(bsae))]
                                if flag_1:
                                    bsae_max_beta = bsae[np.argmax(abs(beta))]
                                    bsae_beta = bsae - beta
                                    under_bsae = min(bsae_beta)
                                    over_bsae = max(bsae_beta)
                                    int_bsae = 0
                                    rmse_bsae = 0
                                    count_bsae = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsae = int_bsae + bsae_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsae = rmse_bsae + (bsae[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsae[i]) and abs(beta[i]) > 1:
                                            count_bsae.append(1)
                                    rmse_bsae = (rmse_bsae/len(beta))**(1/2)
                                    coherence_bsae = 100 - (len(count_bsae)/len(interesting_time)*100)
                        if flag_4:
                            if beta.size > 0:
                                bsa = dictionaries.objectives["BodySlipAngle_deg"][item[2][0]:item[2][1]][dictionaries.objectives[reference_string_speed[k] + "_kmh"][item[2][0]:item[2][1]] > 25]
                                max_bsa = max(abs(bsa))*np.sign(bsa[np.argmax(abs(bsa))])
                                speed_max_bsa = interesting_time[np.argmax(abs(bsa))]
                                if flag_1:
                                    bsa_max_beta = bsa[np.argmax(abs(beta))]
                                    bsa_beta = bsa - beta
                                    under_bsa = min(bsa_beta)
                                    over_bsa = max(bsa_beta)
                                    int_bsa = 0
                                    rmse_bsa = 0
                                    count_bsa = []
                                    for i in range(1, len(interesting_time)):
                                        int_bsa = int_bsa + bsa_beta[i-1]*(interesting_time[i]-interesting_time[i-1])
                                        rmse_bsa = rmse_bsa + (bsa[i] - beta[i])**2
                                        if np.sign(beta[i]) != np.sign(bsa[i]) and abs(beta[i]) > 1:
                                            count_bsa.append(1)
                                    rmse_bsa = (rmse_bsa/len(beta))**(1/2)
                                    coherence_bsa = 100 - (len(count_bsa)/len(interesting_time)*100)
                peak_list = [max_beta, speed_max_beta, time_max_beta, max_bsaa, speed_max_bsaa, bsaa_max_beta, max_bsae, speed_max_bsae, bsae_max_beta, max_bsa, speed_max_bsa, bsa_max_beta, int_bsaa, int_bsae, int_bsa, rmse_bsaa, rmse_bsae, rmse_bsa, under_bsaa, under_bsae, under_bsa, over_bsaa, over_bsae, over_bsa, coherence_bsaa, coherence_bsae, coherence_bsa]
                i = 0
                for obj in observer_list:
                    if peak_list[i] != "":
                        obj.append(round(peak_list[i], 2))
                    else:
                        obj.append(peak_list[i])
                    i += 1
            else:
                i = 0
                peak_list = [max_beta, speed_max_beta, time_max_beta, max_bsaa, speed_max_bsaa, bsaa_max_beta, max_bsae, speed_max_bsae, bsae_max_beta, max_bsa, speed_max_bsa, bsa_max_beta, int_bsaa, int_bsae, int_bsa, rmse_bsaa, rmse_bsae, rmse_bsa, under_bsaa, under_bsae, under_bsa, over_bsaa, over_bsae, over_bsa, coherence_bsaa, coherence_bsae, coherence_bsa]
                for obj in observer_list:
                    obj.append(peak_list[i])
                    i += 1
            k += 1
        for indexes in observer_list:
            parameters_list.append(indexes)

    def flag_detection(self, signals, parameters_list, maneuvers):
        abs_flag = ["ABS Flag"]
        esc_flag = ["ESC Flag"]
        tcs_flag = ["TCS Flag"]
        observer_list = [abs_flag, esc_flag, tcs_flag]
        for item in maneuvers:    
            if "ABS" in item[0] or "ESC_Handling" == item[0] or "ESC_PartialBrkinTurn" == item[0] or "TCS" in item[0]:
                i = 2
            else:
                i = 3   
            try: 
                single_abs_flag = self.flag_detector([signals.objectives["ABSTrigger_FL"], signals.objectives["ABSTrigger_FR"], signals.objectives["ABSTrigger_RL"], signals.objectives["ABSTrigger_RR"]], item[i][0], item[i][1])
            except KeyError:
                single_abs_flag = "ND"
            try:
                single_esc_flag = self.flag_detector([signals.objectives["ESCTrigger"]], item[i][0], item[i][1])
            except KeyError:
                single_esc_flag = "ND"
            try:
                single_tcs_flag = self.flag_detector([signals.objectives["TCSTrigger"]], item[i][0], item[i][1])
            except KeyError:
                single_tcs_flag = "ND"
            peak_list = [single_abs_flag, single_esc_flag, single_tcs_flag]
            i = 0
            for obj in observer_list:
                obj.append(peak_list[i])
                i += 1

        for item in observer_list:
            parameters_list.append(item)

    def overall(self, maneuvers, dictionaries, reference_speed, parameters_list):
        total_time = ["Total Time"]
        total_distance = ["Total Distance"]
        max_intensity_actuator_FL = ["Actuator_FL_Current_Peak"]
        mean_intensity_actuator_FL = ["Actuator_FL_Current_Mean"]
        max_intensity_actuator_FR = ["Actuator_FR_Current_Peak"]
        mean_intensity_actuator_FR = ["Actuator_FR_Current_Mean"]
        max_intensity_actuator_RL = ["Actuator_RL_Current_Peak"]
        mean_intensity_actuator_RL = ["Actuator_RL_Current_Mean"]
        max_intensity_actuator_RR = ["Actuator_RR_Current_Peak"]
        mean_intensity_actuator_RR = ["Actuator_RR_Current_Mean"]
        # time_over_25_fa = ["CurrentPeakTime_500ms_FA"]
        # time_over_25_ra = ["CurrentPeakTime_500ms_RA"]
        observer_list = [max_intensity_actuator_FL, mean_intensity_actuator_FL, max_intensity_actuator_FR, mean_intensity_actuator_FR, max_intensity_actuator_RL, mean_intensity_actuator_RL, max_intensity_actuator_RR, mean_intensity_actuator_RR, total_time, total_distance] # time_over_25_fa, time_over_25_ra,
        corners = ["FL", "FR", "RL", "RR"]
        k = 0
        for item in maneuvers:    
            if reference_speed[k] + "_ms" in dictionaries.objectives:
                distance = self.overall_distance(item, dictionaries.time_resampled, dictionaries.objectives[reference_speed[k] + "_ms"])
                if distance != "ND":
                    total_distance.append(round(self.overall_distance(item, dictionaries.time_resampled, dictionaries.objectives[reference_speed[k] + "_ms"]), 2))
                else:
                    total_distance.append(distance)
            else:
                total_distance.append("ACQUISITION ERROR")
            total_time.append(round(self.overall_time(item, dictionaries.time_resampled), 2))
            i = 0
            single_max_intensity_actuator_FL = ""
            single_max_intensity_actuator_FR = ""
            single_max_intensity_actuator_RL = ""
            single_max_intensity_actuator_RR = ""
            single_mean_intensity_actuator_FL = ""
            single_mean_intensity_actuator_FR = ""
            single_mean_intensity_actuator_RL = ""
            single_mean_intensity_actuator_RR = ""
            # single_time_fa = ""
            # single_time_ra = ""
            single_observer_list = [single_max_intensity_actuator_FL, single_mean_intensity_actuator_FL, single_max_intensity_actuator_FR, single_mean_intensity_actuator_FR, single_max_intensity_actuator_RL, single_mean_intensity_actuator_RL, single_max_intensity_actuator_RR, single_mean_intensity_actuator_RR]#, single_time_fa, single_time_ra]
            for corner in corners:
                if "ActuatorCurrent_" + corner in dictionaries.objectives:
                    single_observer_list[i], single_observer_list[i+1] = self.intensities(dictionaries.objectives["ActuatorCurrent_" + corner], item[2][0], item[2][1])
                i = i+2
            # int_curr_fa = dictionaries.objectives["ActuatorCurrent_FL"][item[2][0]: item[2][0] + int(round(0.5*dictionaries.frequency))]
            # int_curr_ra = dictionaries.objectives["ActuatorCurrent_RL"][item[2][0]: item[2][0] + int(round(0.5*dictionaries.frequency))]
            # single_observer_list[8] = len(int_curr_fa[int_curr_fa > 25])/dictionaries.frequency*1000
            # single_observer_list[9] = len(int_curr_ra[int_curr_ra > 25])/dictionaries.frequency*1000
            for j in range(len(single_observer_list)):
                if single_observer_list[j] != "":
                    observer_list[j].append(round(single_observer_list[j], 2))
                else:
                    observer_list[j].append(single_observer_list[j])
            k += 1                
        for item in observer_list:
            parameters_list.append(item)

    def sensorless_estimators(self, dictionaries, parameters_list, reference_speed, maneuvers):
        avg_estimated_force_fl = ["EstimatedForce_FL_avg"]
        avg_estimated_force_fr = ["EstimatedForce_FR_avg"]
        avg_estimated_force_rl = ["EstimatedForce_RL_avg"]
        avg_estimated_force_rr = ["EstimatedForce_RR_avg"]
        avg_measured_force_fl = ["MeasuredForce_FL_avg"]
        avg_measured_force_fr = ["MeasuredForce_FR_avg"]
        avg_measured_force_rl = ["MeasuredForce_RL_avg"]
        avg_measured_force_rr = ["MeasuredForce_RR_avg"]
        avg_requested_force_fl = ["RequestedForce_FL_avg"]
        avg_requested_force_fr = ["RequestedForce_FR_avg"]
        avg_requested_force_rl = ["RequestedForce_RL_avg"]
        avg_requested_force_rr = ["RequestedForce_RR_avg"]
        relative_error_force_fl = ["Relative_Force_Error_FL"]
        relative_error_force_fr = ["Relative_Force_Error_FR"]
        relative_error_force_rl = ["Relative_Force_Error_RL"]
        relative_error_force_rr = ["Relative_Force_Error_RR"]
        ground_force_error_fl = ["Ground_Force_Error_FL"]
        ground_force_error_fr = ["Ground_Force_Error_FR"]
        ground_force_error_rl = ["Ground_Force_Error_RL"]
        ground_force_error_rr = ["Ground_Force_Error_RR"]
        temperature_at_start_rear = ["Temperature@Start_Rear"]
        temperature_at_start_front = ["Temperature@Start_Front"]
        estimated_position_fl = ["Estimated_Position_FL"]
        estimated_position_fr = ["Estimated_Position_FR"]
        estimated_position_rl = ["Estimated_Position_RL"]
        estimated_position_rr = ["Estimated_Position_RR"]
        measured_position_fl = ["Measured_Position_FL"]
        measured_position_fr = ["Measured_Position_FR"]
        measured_position_rl = ["Measured_Position_RL"]
        measured_position_rr = ["Measured_Position_RR"]
        sensorless_wear_fl = ["Sensorless_Wear_FL"]
        sensorless_wear_fr = ["Sensorless_Wear_FR"]
        sensorless_wear_rl = ["Sensorless_Wear_RL"]
        sensorless_wear_rr = ["Sensorless_Wear_RR"]
        observer_list = [avg_estimated_force_fl, avg_estimated_force_fr, avg_estimated_force_rl, avg_estimated_force_rr, avg_measured_force_fl, avg_measured_force_fr, avg_measured_force_rl, avg_measured_force_rr, avg_requested_force_fl, avg_requested_force_fr, avg_requested_force_rl, avg_requested_force_rr, relative_error_force_fl, relative_error_force_fr, relative_error_force_rl, relative_error_force_rr, ground_force_error_fl, ground_force_error_fr, ground_force_error_rl, ground_force_error_rr, temperature_at_start_rear, temperature_at_start_front, estimated_position_fl, estimated_position_fr, estimated_position_rl, estimated_position_rr, measured_position_fl, measured_position_fr, measured_position_rl, measured_position_rr, sensorless_wear_fl, sensorless_wear_fr, sensorless_wear_rl, sensorless_wear_rr]
        corners = ["FL", "FR", "RL", "RR"]
        k = 0
        for item in maneuvers:    
            single_avg_estimated_force_fl = ""
            single_avg_estimated_force_fr = ""
            single_avg_estimated_force_rl = ""
            single_avg_estimated_force_rr = ""
            single_avg_measured_force_fl = ""
            single_avg_measured_force_fr = ""
            single_avg_measured_force_rl = ""
            single_avg_measured_force_rr = ""
            single_avg_requested_force_fl = ""
            single_avg_requested_force_fr = ""
            single_avg_requested_force_rl = ""
            single_avg_requested_force_rr = ""
            single_relative_error_force_fl = ""
            single_relative_error_force_fr = ""
            single_relative_error_force_rl = ""
            single_relative_error_force_rr = ""
            single_ground_force_error_fl = ""
            single_ground_force_error_fr = ""
            single_ground_force_error_rl = ""
            single_ground_force_error_rr = ""
            single_temperature_at_start_rear = ""
            single_temperature_at_start_front = ""
            single_estimated_position_fl = ""
            single_estimated_position_fr = ""
            single_estimated_position_rl = ""
            single_estimated_position_rr = ""
            single_measured_position_fl = ""
            single_measured_position_fr = ""
            single_measured_position_rl = ""
            single_measured_position_rr = ""
            single_sensorless_wear_fl = ""
            single_sensorless_wear_fr = ""
            single_sensorless_wear_rl = ""
            single_sensorless_wear_rr = ""
            temperature_at_start_fl_ext = ""
            temperature_at_start_fl_int = ""
            temperature_at_start_fr_ext = ""
            temperature_at_start_fr_int = ""
            temperature_at_start_rl_ext = ""
            temperature_at_start_rl_int = ""
            temperature_at_start_rr_ext = ""
            temperature_at_start_rr_int = ""
            temperature_corners_front = ["FL", "FR"]
            temperature_corners_rear = ["RL", "RR"]
            temperatures_front = [temperature_at_start_fl_ext, temperature_at_start_fl_int, temperature_at_start_fr_ext, temperature_at_start_fr_int]
            temperatures_rear = [temperature_at_start_rl_ext, temperature_at_start_rl_int, temperature_at_start_rr_ext, temperature_at_start_rr_int]
            single_observer_list = [single_avg_estimated_force_fl, single_avg_estimated_force_fr, single_avg_estimated_force_rl, single_avg_estimated_force_rr, single_avg_measured_force_fl, single_avg_measured_force_fr, single_avg_measured_force_rl, single_avg_measured_force_rr, single_avg_requested_force_fl, single_avg_requested_force_fr, single_avg_requested_force_rl, single_avg_requested_force_rr, single_relative_error_force_fl, single_relative_error_force_fr, single_relative_error_force_rl, single_relative_error_force_rr, single_ground_force_error_fl, single_ground_force_error_fr, single_ground_force_error_rl, single_ground_force_error_rr, single_temperature_at_start_rear, single_temperature_at_start_front, single_estimated_position_fl, single_estimated_position_fr, single_estimated_position_rl, single_estimated_position_rr, single_measured_position_fl, single_measured_position_fr, single_measured_position_rl, single_measured_position_rr, single_sensorless_wear_fl, single_sensorless_wear_fr, single_sensorless_wear_rl, single_sensorless_wear_rr]
            i = 0
            if "ABS" in item[0] or "ESC_PartialBrkinTurn" == item[0]:
                for corner in corners:
                    single_observer_list[i], single_observer_list[i+4], single_observer_list[i+8], single_observer_list[i+12], single_observer_list[i+16] = self.force_avg_and_errors(dictionaries, reference_speed[k], corner, item[2][0])
                    single_observer_list[i+22], single_observer_list[i+26], single_observer_list[i+30], sample_start = self.touch_disc_positions(dictionaries, corner, item[2][0], reference_speed[k])
                    i += 1
                h = 0
                if "ExternalPadTemperature_FL" in dictionaries.objectives:
                    if "ExternalPadTemperature_FL" in dictionaries.times:
                        try:
                            if dictionaries.times["ExternalPadTemperature_" + corner][1] >= sample_start:
                                for corner in temperature_corners_front:
                                    temperatures_front[h] = property_at_sample(item, dictionaries, "ExternalPadTemperature_" + corner, 2, 0)
                                    temperatures_front[h+1] = property_at_sample(item, dictionaries, "InternalPadTemperature_" + corner, 2, 0)
                                    h += 2
                                single_observer_list[21] = (temperatures_front[0] + temperatures_front[1] + temperatures_front[2] + temperatures_front[3])/4
                        except:
                            single_observer_list[21] = ""
                    else:
                        for corner in temperature_corners_front:
                            temperatures_front[h] = property_at_sample(item, dictionaries, "ExternalPadTemperature_" + corner, 2, 0)
                            temperatures_front[h+1] = property_at_sample(item, dictionaries, "InternalPadTemperature_" + corner, 2, 0)
                            h += 2
                        single_observer_list[21] = (temperatures_front[0] + temperatures_front[1] + temperatures_front[2] + temperatures_front[3])/4
                h = 0
                if "ExternalPadTemperature_RL" in dictionaries.objectives:
                    if "ExternalPadTemperature_RL" in dictionaries.times:
                        try:
                            if dictionaries.times["ExternalPadTemperature_" + corner][1] >= sample_start:
                                for corner in temperature_corners_rear:
                                    temperatures_rear[h] = property_at_sample(item, dictionaries, "ExternalPadTemperature_" + corner, 2, 0)
                                    temperatures_rear[h+1] = property_at_sample(item, dictionaries, "InternalPadTemperature_" + corner, 2, 0)
                                    h += 2
                                single_observer_list[20] = (temperatures_rear[0] + temperatures_rear[1] + temperatures_rear[2] + temperatures_rear[3])/4
                        except:
                            single_observer_list[20] = ""
                    else:
                        for corner in temperature_corners_rear:
                            temperatures_rear[h] = property_at_sample(item, dictionaries, "ExternalPadTemperature_" + corner, 2, 0)
                            temperatures_rear[h+1] = property_at_sample(item, dictionaries, "InternalPadTemperature_" + corner, 2, 0)
                            h += 2
                        single_observer_list[20] = (temperatures_rear[0] + temperatures_rear[1] + temperatures_rear[2] + temperatures_rear[3])/4
            for j in range(len(single_observer_list)):
                if single_observer_list[j] != "" and single_observer_list[j] != "N/A":
                    observer_list[j].append(round(single_observer_list[j], 2))
                else:
                    observer_list[j].append(single_observer_list[j])    
            k += 1           
        for item in observer_list:
            parameters_list.append(item)
