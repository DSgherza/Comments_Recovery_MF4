import pandas as pd
import os
import math
import scipy
import numpy as np

class ManualManeuvreRecognition():

    def signal_fragment_recovery(self, maneuvres: list, dictionaries: dict, property: str, base: int) -> list:
        """ Consente di recuperare un pezzo di un determinato segnale, fra sample on e sample off"""
        global_fragment = []
        global_sample = []
        local_sample= [] 
        time_counter = maneuvres[base][0]
        local_fragment = []
        local_sample.append(time_counter)

        while time_counter <= maneuvres[base][1]:
            time_counter += 1
            local_sample.append(time_counter)
            local_fragment.append(dictionaries.objectives[property][time_counter])

        global_fragment.append(local_fragment)
        global_sample.append(local_sample)

        return global_fragment

    def derivative_calculation(self, dictionaries, string, unit, sub_string):
        derivative_list = []
        for i in range(len(dictionaries.objectives[string])):
            try:
                derivative_list.append((dictionaries.objectives[string][i+1] - dictionaries.objectives[string][i])/(dictionaries.time_resampled[i+1] - dictionaries.time_resampled[i])) 
            except IndexError:
                derivative_list.append(derivative_list[-1])
        b,a = scipy.signal.butter(2, 10/(0.5*167), analog=False, output='ba')
        dictionaries.objectives[string.split(sub_string)[0] + "Der" + unit] = scipy.signal.filtfilt(b, a, np.array(derivative_list))
    
    def accel_conversion(self, dictionaries, string):
            signal_list_df = pd.read_excel(os.getcwd() + "\\signalList.xlsx", sheet_name = dictionaries.vehicle_name)
            signal_list_variables = signal_list_df["VariableName"]
            signal_list_unit = signal_list_df["Unit"]
            for i in range(len(signal_list_variables)):
                if signal_list_variables[i] == string:
                    unit = signal_list_unit[i]
                    break
            if unit == "g":
                dictionaries.objectives[string] = dictionaries.objectives[string]*9.81


    def vel_conversion(self, dictionaries, string):
        if string + "_kmh" not in dictionaries.objectives or string + "_ms" not in dictionaries.objectives:
            signal_list_df = pd.read_excel(os.getcwd() + "\\signalList.xlsx", sheet_name = dictionaries.vehicle_name)
            signal_list_variables = signal_list_df["VariableName"]
            signal_list_unit = signal_list_df["Unit"]
            for i in range(len(signal_list_variables)):
                if signal_list_variables[i] == string:
                    unit = signal_list_unit[i]
                    break
            if unit == "m/s":
                vel_km_h = []
                for i in range(len(dictionaries.objectives[string])):
                    vel_km_h.append(dictionaries.objectives[string][i]*3.6)
                dictionaries.objectives[string + "_kmh"] = np.array(vel_km_h)
                dictionaries.objectives[string + "_ms"] = dictionaries.objectives[string]
                del dictionaries.objectives[string]
            else:
                dictionaries.objectives[string + "_kmh"] = dictionaries.objectives[string]
                dictionaries.objectives[string + "_ms"] = dictionaries.objectives[string]/3.6
                del dictionaries.objectives[string]

    def angle_conversion(self, dictionaries, string1, string2, string, measurment_unit):
        if string1 not in dictionaries.objectives or string2 not in dictionaries.objectives:
            signal_list_df = pd.read_excel(os.getcwd() + "\\signalList.xlsx", sheet_name = dictionaries.vehicle_name)
            signal_list_variables = signal_list_df["VariableName"]
            signal_list_unit = signal_list_df["Unit"]
            for i in range(len(signal_list_variables)):
                if signal_list_variables[i] == string:
                    unit = signal_list_unit[i]
            if unit == measurment_unit:
                yaw_deg_s = []
                for i in range(len(dictionaries.objectives[string])):
                    yaw_deg_s.append(dictionaries.objectives[string][i]*180/math.pi)
                dictionaries.objectives[string1] = np.array(yaw_deg_s)
                dictionaries.objectives[string2] = dictionaries.objectives[string]
                del dictionaries.objectives[string]
            else:
                dictionaries.objectives[string1] = dictionaries.objectives[string]
                dictionaries.objectives[string2] = dictionaries.objectives[string]*math.pi/180
                del dictionaries.objectives[string]

    def priority_research(self, dictionaries, priority_list, reference_string, string):
        found = False
        for i in range(len(priority_list)):
            for item in dictionaries.signal_priority[priority_list[i]]:
                if string in item.lower() and item in dictionaries.objectives:
                    reference_string = item
                    found = True
                    break
            if found:
                break
        return reference_string

    def signals_management(self, dictionaries) -> str:
        reference_string_speed, reference_string_decel, reference_string_angle = self.priority_definition(dictionaries)
        if "VehicleSpeed" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "VehicleSpeed")
        if "OpticalSpeed" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "OpticalSpeed")
        if "VehicleSpeedBraking" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "VehicleSpeedBraking")
        if "VehicleSpeedTraction" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "VehicleSpeedTraction")
        if "ReferenceSpeed" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "ReferenceSpeed")
        if "RawSpeed" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "RawSpeed")
        for item in ["FL", "FR", "RL", "RR"]:
            if "WheelSpeed_" + item in dictionaries.objectives:
                self.vel_conversion(dictionaries, "WheelSpeed_" + item)
        if "VehicleSpeed_FA" in dictionaries.objectives:
            self.vel_conversion(dictionaries, "VehicleSpeed_FA")
            self.vel_conversion(dictionaries, "VehicleSpeedBraking_FA")
            self.vel_conversion(dictionaries, "VehicleSpeedTraction_FA")
        if "RollRate" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "RollRate_degs", "RollRate_rads", "RollRate", "rad/s") 
        if "YawRate" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "YawRate_degs", "YawRate_rads", "YawRate", "rad/s")
        if "SteeringAngle" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "SteeringAngle_deg", "SteeringAngle_rad", "SteeringAngle", "rad")
        if "SideSlipAngle" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "SideSlipAngle_deg", "SideSlipAngle_rad", "SideSlipAngle", "rad")
        if "BSAAngle" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "BSAAngle_deg", "BSAAngle_rad", "BSAAngle", "rad")
        if "BSEAngle" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "BSEAngle_deg", "BSEAngle_rad", "BSEAngle", "rad")
        if "BodySlipAngle" in dictionaries.objectives:
            self.angle_conversion(dictionaries, "BodySlipAngle_deg", "BodySlipAngle_rad", "BodySlipAngle", "rad")
        try:
            self.angle_conversion(dictionaries, "SteeringAngleDer_degs", "SteeringAngleDer_rads", "SteeringAngleDer", "rad/s")
        except UnboundLocalError:
            if "SteeringAngle_deg" in dictionaries.objectives:
                self.derivative_calculation(dictionaries, "SteeringAngle_deg", "_degs", "_deg")
                self.derivative_calculation(dictionaries, "SteeringAngle_rad", "_rads", "_rad")
        except KeyError:
            if "SteeringAngle_deg" in dictionaries.objectives:
                self.derivative_calculation(dictionaries, "SteeringAngle_deg", "_degs", "_deg")
                self.derivative_calculation(dictionaries, "SteeringAngle_rad", "_rads", "_rad")
        if "Ax" in dictionaries.objectives:
            self.accel_conversion(dictionaries, "Ax")
            self.derivative_calculation(dictionaries, "Ax", "", "b")
        if "Ay" in dictionaries.objectives:
            self.accel_conversion(dictionaries, "Ay")
            self.derivative_calculation(dictionaries, "Ay", "", "b")
        for item in ["FL", "FR", "RL", "RR"]:
            if "ForceFeedback_" + item in dictionaries.objectives:
                dictionaries.objectives["ForceFeedback_" + item] = dictionaries.objectives["ForceFeedback_" + item]/1000
        for item in ["RA", "FA"]:
            if "EngineTorque_" + item in dictionaries.objectives:
                dictionaries.objectives["EngineTorque_" + item] = dictionaries.objectives["EngineTorque_" + item]/1000
        if dictionaries.objectives["PressureForceRatio_FA"] != 1:
            if "BrakePressure_FL" in dictionaries.objectives:
                dictionaries.objectives["ForceFeedback_FL"] = dictionaries.objectives["BrakePressure_FL"]*dictionaries.objectives["PressureForceRatio_FA"]/1000
            if "BrakePressure_FR" in dictionaries.objectives:
                dictionaries.objectives["ForceFeedback_FR"] = dictionaries.objectives["BrakePressure_FR"]*dictionaries.objectives["PressureForceRatio_FA"]/1000
        if dictionaries.objectives["PressureForceRatio_RA"] != 1:
            if "BrakePressure_RL" in dictionaries.objectives:
                dictionaries.objectives["ForceFeedback_RL"] = dictionaries.objectives["BrakePressure_RL"]*dictionaries.objectives["PressureForceRatio_RA"]/1000
            if "BrakePressure_RR" in dictionaries.objectives:    
                dictionaries.objectives["ForceFeedback_RR"] = dictionaries.objectives["BrakePressure_RR"]*dictionaries.objectives["PressureForceRatio_RA"]/1000
        for item in ["FL", "FR", "RL", "RR"]:
            if "BrakePressure_" + item in dictionaries.objectives:
                del dictionaries.objectives["BrakePressure_" + item]
        return reference_string_speed, reference_string_decel, reference_string_angle


    def priority_definition(self, dictionaries):
        reference_string_speed = "ReferenceSpeed"
        reference_string_decel = "BPDecelReq"
        reference_string_angle = "BodySlipAngle"
        priority_list = ["Prio1", "Prio2", "Prio3", "Prio4", "Prio5"]
        reference_string_decel = self.priority_research(dictionaries, priority_list, reference_string_decel, "decel")
        reference_string_angle = self.priority_research(dictionaries, priority_list, reference_string_angle, "angle")
        return reference_string_speed, reference_string_decel, reference_string_angle


    def __init__ (self, input_management_obj, coerence, speed_check, direction_check, yaw_check, ay_check, lws_check):
        maneuvres = self.trigger_recognition(input_management_obj)
        input_management_obj.speed_index = 0
        self.reference_string_speed, self.reference_string_decel, self.reference_string_angle = self.signals_management(input_management_obj)
        if "RawSpeed_kmh" in input_management_obj.objectives:
            try:
                for i in range(len(input_management_obj.objectives["ReferenceSpeed_kmh"])):
                    try:
                        if input_management_obj.objectives["ReferenceSpeed_kmh"][i] < input_management_obj.objectives["RawSpeed_kmh"][i] - 5:
                            if "OpticalSpeed_kmh" in input_management_obj.objectives:
                                self.reference_string_speed = "OpticalSpeed"
                                input_management_obj.speed_index = 1
                            else:
                                self.reference_string_speed = "VehicleSpeed"
                                input_management_obj.speed_index = 2
                            break
                    except IndexError:
                        pass
                    try:
                        if input_management_obj.objectives["ReferenceSpeed_kmh"][i] > input_management_obj.objectives["RawSpeed_kmh"][i] + 5:
                            if "OpticalSpeed_kmh" in input_management_obj.objectives:
                                self.reference_string_speed = "OpticalSpeed"
                                input_management_obj.speed_index = 1
                            else:
                                self.reference_string_speed = "VehicleSpeed"
                                input_management_obj.speed_index = 2
                            break
                    except IndexError:
                        pass
            except KeyError:
                self.reference_string_speed = "RawSpeed"
        else:
            if "OpticalSpeed_kmh" in input_management_obj.objectives:
                self.reference_string_speed = "OpticalSpeed"
                input_management_obj.speed_index = 1
            else:
                self.reference_string_speed = "VehicleSpeed"
                input_management_obj.speed_index = 2
        maneuvres = self.ABS_maneuvre_recognition(input_management_obj, maneuvres, coerence, speed_check, direction_check, yaw_check, ay_check, lws_check)
        maneuvres = self.ESC_maneuvre_recognition(input_management_obj, maneuvres, coerence, speed_check, direction_check, yaw_check, ay_check, lws_check)
        self.maneuvre = self.TCS_maneuvre_recognition(input_management_obj, maneuvres, coerence, speed_check, yaw_check, direction_check, ay_check, lws_check)

    def maneuver_search(self, obj, single_maneuvre_sample_list, maneuvres_sample_list, i, trigger_check, time_counter, maneuvre_sample):
        if obj.subjectives["LatAnalyzer_Trigger"][i+1]<0.05 and obj.subjectives["LatAnalyzer_Trigger"][i+int(round(0.1*obj.frequency))] < 0.05:
            maneuvres_sample_list.append(single_maneuvre_sample_list)
            for key in obj.subjectives:
                if key in ["ManeuverSelector_ABS_Chessboard", "ManeuverSelector_ABS_InTurn", "ManeuverSelector_ABS_LaneChange", "ManeuverSelector_ABS_MuSplit", 
                                "ManeuverSelector_ABS_NegativeMuJump", "ManeuverSelector_ABS_NegativeMuSplitJump", "ManeuverSelector_ABS_PositiveMuJump", "ManeuverSelector_ABS_PositiveMuSplitJump", 
                                "ManeuverSelector_ABS_StoppingDistance", "ManeuverSelector_ABS_DoubleMuJump", "ManeuverSelector_ESC_ConstantRadius", "ManeuverSelector_ESC_Handling", "ManeuverSelector_ESC_LaneChange", 
                                "ManeuverSelector_ESC_PartialBrkinTurn", "ManeuverSelector_ESC_PowerOffinTurn", "ManeuverSelector_ESC_PowerOninTurn", "ManeuverSelector_ESC_RampSteer", 
                                "ManeuverSelector_ESC_Slalom", "ManeuverSelector_ESC_StepSteer", "ManeuverSelector_TCS_Chessboard", "ManeuverSelector_TCS_LaunchHomogeneous",
                                "ManeuverSelector_TCS_LaunchMuSplit", "ManeuverSelector_TCS_NegativeMuJump", "ManeuverSelector_TCS_NegativeMuSplitJump", "ManeuverSelector_TCS_PositiveMuJump",
                                "ManeuverSelector_TCS_PositiveMuSplitJump", "ManeuverSelector_ZERO_Static", "ManeuverSelector_ZERO_Dynamic"]:
                    if  obj.subjectives[key][time_counter] < 1.05 and obj.subjectives[key][time_counter] > 0.95:
                        maneuvre = key
                        try:
                            if obj.subjectives["TargetSpeed"][time_counter+20] > 20:
                                obj.target_speed.append(obj.subjectives["TargetSpeed"][time_counter + 20])
                            else:
                                obj.target_speed.append("")
                        except KeyError:
                            obj.target_speed.append("")
                        try:
                            if obj.subjectives["TargetRadius"][time_counter+20] > 5:
                                obj.target_radius.append(obj.subjectives["TargetRadius"][time_counter + 20])
                            else:
                                obj.target_radius.append("")
                        except KeyError:
                            obj.target_radius.append("")
                        try:
                            while obj.subjectives[maneuvre][time_counter] > 0.05:
                                time_counter += 1
                            trigger_check.append("")
                        except IndexError:
                            trigger_check.append(True)
                        sfm = time_counter
                        if maneuvre_sample == []:
                            maneuvre_sample = [[maneuvre, sfm]]
                        else:
                            maneuvre_sample.append([maneuvre, sfm])
                        break
                    else: 
                        maneuvre = ""
            if maneuvre == "":
                maneuvres_sample_list.pop(-1)
        return maneuvre_sample
        
    def trigger_recognition(self, obj):
        self.maneuvres_sample_list = []
        maneuvre_sample = []
        self.trigger_check = []
        obj.target_speed = []
        for i in range(len(obj.subjectives["LatAnalyzer_Trigger"])):
            if obj.subjectives["LatAnalyzer_Trigger"][i]>=0.05:
                if obj.subjectives["LatAnalyzer_Trigger"][i-1]<0.05 and obj.subjectives["LatAnalyzer_Trigger"][i-int(round(0.1*obj.frequency))]<0.05:
                    time_counter = i
                    single_maneuvre_sample_list = [i]
                else:
                    single_maneuvre_sample_list.append(i)
                try:
                    maneuvre_sample = self.maneuver_search(obj, single_maneuvre_sample_list, self.maneuvres_sample_list, i, self.trigger_check, time_counter, maneuvre_sample)
                except IndexError:
                    break      
        list_maneuvre = []
        list_samples = []
        maneuvres_samples = []
        for i in range(len(self.maneuvres_sample_list)):
            list_maneuvre.append(maneuvre_sample[i][0].split("Selector_")[1])
            list_samples.append([self.maneuvres_sample_list[i][0], self.maneuvres_sample_list[i][-1], maneuvre_sample[i][1]])
            maneuvres_samples.append([list_maneuvre[i], list_samples[i]])
        return maneuvres_samples
    
    def ABS_maneuvre_recognition(self, obj, maneuvre, coerence, speed_check, direction_check, yaw_check, ay_check, lws_check):
        reference_string_speed = self.reference_string_speed
        #brake_pedal_threshold_1 = 5 #threshold to leave an edge on brake pedal pressing
        brake_pedal_threshold = 1.5
        speed_threshold = [0.14, 0.28, 0.56]  #0.56m/s = 2km/h
        maneuvre_controls = []
        abs_check = True
        speed_list = ["ReferenceSpeed", "OpticalSpeed", "VehicleSpeed"]
        for i in range(len(maneuvre)):
            if i == 0:
                reference_string_speed = [self.reference_string_speed]
                speed_index = [obj.speed_index]
            else:
                reference_string_speed.append(self.reference_string_speed)
                speed_index.append(obj.speed_index)
            if "ReferenceSpeed_ms" not in obj.objectives:
                for j in range(len(speed_list)):
                    if speed_list[j] + "_ms" in obj.objectives:
                        reference_string_speed[i] = speed_list[j]
                        speed_index[i] = j
                        break
            if abs_check:
                ctrl = False
                if "ABS" in maneuvre[i][0] or "ESC_PartialBrkinTurn" == maneuvre[i][0]:
                    time_counter = maneuvre[i][1][0]
                    bpp_f_found = False
                    try:
                        while obj.objectives["BrakePedalPosition"][time_counter] > brake_pedal_threshold : #_1
                            time_counter += 1
                    except IndexError:
                        abs_check = False
                        maneuvre_controls.append(i)
                        ctrl = True
                    while not bpp_f_found and not ctrl:
                        try:
                            while obj.objectives["BrakePedalPosition"][time_counter] < brake_pedal_threshold:
                                time_counter += 1
                        except IndexError:
                            abs_check = False
                            maneuvre_controls.append(i)
                            ctrl = True
                            break
                        bpp_i = time_counter
                        if reference_string_speed[i] == "ReferenceSpeed" or reference_string_speed[i] == "RawSpeed":
                            if bpp_i < maneuvre[i][1][1]:
                                for j in range(bpp_i, maneuvre[i][1][1]):
                                    try:
                                        if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                            if "OpticalSpeed_ms" in obj.objectives:
                                                reference_string_speed[i] = "OpticalSpeed"
                                                speed_index[i] = 1
                                            else:    
                                                reference_string_speed[i] = "VehicleSpeed"
                                                speed_index[i] = 2
                                            break
                                    except KeyError:
                                        pass
                                    except IndexError:
                                        pass
                        for item in speed_threshold:
                            time_counter = bpp_i
                            try:
                                while obj.objectives["BrakePedalPosition"][time_counter] >= brake_pedal_threshold and not bpp_f_found:
                                    try:
                                        if obj.objectives[reference_string_speed[i] + "_ms"][time_counter] < item:
                                            bpp_f = time_counter - 1
                                            bpp_f_found = True
                                            break
                                        else:
                                            time_counter += 1
                                    except IndexError:
                                        if reference_string_speed[i] != "VehicleSpeed":
                                            reference_string_speed[i] = speed_list[speed_index[i] + 1]
                                            speed_index[i] = speed_index[i] + 1
                                            time_counter = bpp_i
                                        else:
                                            maneuvre_controls.append(i)
                                            ctrl = True
                                            break
                                    except KeyError:
                                        if self.reference_string_speed[i] != "VehicleSpeed":
                                            self.reference_string_speed[i] = speed_list[self.speed_index[i] + 1]
                                            self.speed_index[i] = self.speed_index[i] + 1
                                            time_counter = bpp_i
                                        else:
                                            maneuvre_controls.append(i)
                                            ctrl = True
                                            break
                                    if time_counter == maneuvre[i][1][1]: 
                                        break
                            except IndexError:
                                abs_check = False
                                maneuvre_controls.append(i)
                                ctrl = True
                                break
                        if not bpp_f_found:
                            bpp_f = time_counter
                            bpp_f_found = True
                        if not ctrl:
                            if obj.objectives["BrakePedalPosition"][time_counter] <= brake_pedal_threshold and not time_counter == maneuvre[i][1][1]:
                                if obj.time_resampled[time_counter] - obj.time_resampled[bpp_i] > 0.2:
                                    bpp_f = time_counter - 1
                                    bpp_f_found = True
                            else:
                                break
                            if bpp_f_found:
                                break
                        if not ctrl:
                            if time_counter == maneuvre[i][1][1]: 
                                bpp_f = time_counter
                                bpp_f_found = True
                    if not ctrl:
                        if obj.time_resampled[bpp_f] - obj.time_resampled[bpp_i] > 1:
                            if bpp_i < maneuvre[i][1][1]:
                                maneuvre[i].append([bpp_i, bpp_f])
                                coerence.append(2)
                            else:
                                maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                                coerence.append(1)
                        else:
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            coerence.append(1)
                if reference_string_speed[i] == "ReferenceSpeed" or reference_string_speed[i] == "RawSpeed":
                    speed_check.append("VBOX")
                elif reference_string_speed[i] == "OpticalSpeed":
                    speed_check.append("TestaOttica")
                else:
                    speed_check.append("Internal")
                frequency = obj.frequency
                if "ABS" in maneuvre[i][0] and "ABS_InTurn" not in maneuvre[i][0]:
                    if len(maneuvre[i]) > 2:
                        try:
                            in_yaw = np.mean(obj.objectives["YawRate_degs"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                            in_ay = np.mean(obj.objectives["Ay"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                            in_lws = np.mean(obj.objectives["SteeringAngle_deg"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                            if abs(in_yaw) < 1 and abs(in_ay) < 0.5 and abs(in_lws) < 5:
                                direction_check.append(True)
                            else:
                                direction_check.append(False)
                            if abs(in_yaw) > 1:
                                yaw_check.append(False)
                            else:
                                yaw_check.append(True)
                            if abs(in_ay) > 0.5:
                                ay_check.append(False)
                            else:
                                ay_check.append(True)
                            if abs(in_lws) > 5:
                                lws_check.append(False)
                            else:
                                lws_check.append(True)
                        except KeyError:
                            direction_check.append(True)
                            lws_check.append(True)
                            ay_check.append(True)
                            yaw_check.append(True)
                else:
                    if "ABS_InTurn" in maneuvre[i][0]:
                        if len(maneuvre[i]) > 2:
                            try:
                                in_yaw = np.mean(obj.objectives["YawRate_degs"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                                in_ay = np.mean(obj.objectives["Ay"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                                in_lws = np.mean(obj.objectives["SteeringAngle_deg"][maneuvre[i][2][0]-int(round(0.5*frequency)):maneuvre[i][2][0]])
                                for k in range(maneuvre[i][2][0]-int(round(0.5*frequency)), maneuvre[i][2][0]):
                                    if abs(obj.objectives["YawRate_degs"][k]-in_yaw) > 2:
                                        yaw_check.append(False)
                                        break
                                    else:
                                        yaw_check.append(True)
                                    if abs(obj.objectives["Ay"][k]-in_ay) > 1:
                                        ay_check.append(False)
                                        break
                                    else:
                                        ay_check.append(True)
                                    if abs(obj.objectives["SteeringAngle_deg"][k]-in_lws) > 10:
                                        lws_check.append(False)
                                        break
                                    else:
                                        lws_check.append(True)
                                if yaw_check[-1] and ay_check[-1] and lws_check[-1]:
                                    direction_check.append(True)
                                else:
                                    direction_check.append(False)
                            except KeyError:
                                direction_check.append(True)
                                lws_check.append(True)
                                ay_check.append(True)
                                yaw_check.append(True)
                        else:
                            yaw_check.append("")
                            ay_check.append("")
                            lws_check.append("")
                            direction_check.append("")
                    else:
                        yaw_check.append(True)
                        ay_check.append(True)
                        lws_check.append(True)
                        direction_check.append(True)
        for item in maneuvre_controls:
            maneuvre[item] = 0
            reference_string_speed[item] = 0
        self.reference_string_speed = reference_string_speed
        self.speed_index = speed_index
        return maneuvre

    def ESC_maneuvre_recognition(self, obj, maneuvre, coerence, speed_check, direction_check, yaw_check, ay_check, lws_check):
        steering_rate_threshold = 1
        throttle_threshold = 0.05
        steering_threshold_rampsteer = 0.5
        maneuvre_controls = []
        steer_check = True
        throttle_check = True
        ctrl = True
        speed_list = ["ReferenceSpeed", "OpticalSpeed", "VehicleSpeed"]
        for i in range(len(maneuvre)):
            try:
                auxiliar_steer = obj.objectives["SteeringAngle_deg"][maneuvre[i][1][1]]
            except IndexError:
                steer_check = False
            except KeyError:
                steer_check = False
                if maneuvre[i][0] != "ESC_PowerOninTurn" and maneuvre[i][0] != "ESC_PowerOffinTurn" and "ABS" not in maneuvre[i][0] and "TCS" not in maneuvre[i][0]:
                    maneuvre_controls.append(i)
            except TypeError:
                steer_check = False
            try:
                auxiliar_throttle = obj.objectives["GasPedalPosition"][maneuvre[i][1][1]]
            except IndexError:
                throttle_check = False
            except KeyError:
                throttle_check = False
            except TypeError:
                throttle_check = False
                if type(maneuvre[i]) != int:
                    if maneuvre[i][0] == "ESC_PowerOninTurn" and maneuvre[i][0] == "ESC_PowerOffinTurn":    
                        if i not in maneuvre_controls:
                            maneuvre_controls.append(i)
            if steer_check:
                max_steer = self.signal_fragment_recovery(maneuvre[i], obj, "SteeringAngle_deg", 1)
                max_steer = np.max(abs(np.array(max_steer)))
            if throttle_check:
                max_gas = self.signal_fragment_recovery(maneuvre[i], obj, "GasPedalPosition", 1)
                max_gas = np.max(abs(np.array(max_gas)))

            if steer_check and throttle_check:
                if "ESC_Handling" == maneuvre[i][0]:
                    m_i = maneuvre[i][1][0]
                    m_f = maneuvre[i][1][1]
                    maneuvre[i].append([m_i, m_f])
                    coerence.append(2)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0

            if steer_check:
                if "ESC_ConstantRadius" == maneuvre[i][0]:
                    m_i = maneuvre[i][1][0]
                    m_f = maneuvre[i][1][1]
                    maneuvre[i].append([m_i, m_f])
                    time_counter = maneuvre[i][1][1]
                    if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                        if m_i < maneuvre[i][1][1]:
                            for j in range(m_i, maneuvre[i][1][1]):
                                try:
                                    if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                        if "OpticalSpeed_ms" in obj.objectives:
                                            self.reference_string_speed[i] = "OpticalSpeed"
                                            self.speed_index[i] = 1
                                        else:    
                                            self.reference_string_speed[i] = "VehicleSpeed"
                                            self.speed_index[i] = 2
                                        break
                                except KeyError:
                                    pass
                                except IndexError:
                                    pass
                    ctrl = True
                    for j in range(self.speed_index[i], len(speed_list)):
                        try:
                            auxiliar_speed = obj.objectives[speed_list[j] + "_ms"][maneuvre[i][1][1]]
                            self.reference_string_speed[i] = speed_list[j]
                            self.speed_index[i] = j
                            break
                        except IndexError:
                            if self.reference_string_speed[i] == "VehicleSpeed":
                                maneuvre_controls.append(i)
                                ctrl = False
                                break
                        except KeyError:
                            if self.reference_string_speed[i] == "VehicleSpeed":
                                maneuvre_controls.append(i)
                                ctrl = False
                                break
                    if ctrl:
                        if obj.objectives[self.reference_string_speed[i] + "_ms"][maneuvre[i][1][0]] < 5/3.6:
                            loop_in = False
                            while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) < steering_rate_threshold and abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) < 0.1:
                                time_counter -= 1
                                loop_in = True
                            if loop_in:
                                time_counter = time_counter - 10
                                while abs(obj.objectives["SteeringAngle_deg"][time_counter + 1] - obj.objectives["SteeringAngle_deg"][time_counter]) > 0.001 or abs(obj.objectives["SteeringAngle_deg"][time_counter]) > 10:
                                    time_counter += 1
                        else:
                            time_counter = m_f
                        if time_counter <= maneuvre[i][1][1]:
                            maneuvre[i].append([m_i, time_counter])     
                            coerence.append(2)
                        else:
                            maneuvre[i].append([m_i, time_counter])
                            coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0
            
            if steer_check:
                if maneuvre[i][0] == "ESC_Slalom" or maneuvre[i][0] == "ESC_LaneChange":
                    time_counter = maneuvre[i][1][0]
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 10] - obj.objectives["SteeringAngle_deg"][time_counter]) > steering_rate_threshold or abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) > 0.1:
                        time_counter += 1
                    while (abs(obj.objectives["SteeringAngle_deg"][time_counter + 10] - obj.objectives["SteeringAngle_deg"][time_counter]) < steering_rate_threshold and abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) < 0.1) and time_counter < maneuvre[i][1][1]:
                        time_counter += 1
                    time_counter = time_counter + 10
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) > 0.01 or abs(obj.objectives["SteeringAngle_deg"][time_counter]) > 3:
                        time_counter -= 1
                    aux_mi = time_counter
                    target_time = obj.time_resampled[time_counter] - 2
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:    
                        m_i = time_counter
                    time_counter = maneuvre[i][1][1]
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) > steering_rate_threshold or abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) > 0.1:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        aux_mf = maneuvre[i][1][1]
                        m_f = maneuvre[i][1][1]
                    else:
                        while (abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) < steering_rate_threshold or abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) < 0.1) and time_counter > maneuvre[i][1][0]:
                            time_counter -= 1
                        time_counter = time_counter - 10
                        if time_counter <= maneuvre[i][1][0]:
                            m_f = maneuvre[i][1][1]
                            aux_mf = maneuvre[i][1][1]
                        else:
                            while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter + 10]) > 0.01 or abs(obj.objectives["SteeringAngle_deg"][time_counter]) > 15:
                                time_counter += 1
                            aux_mf = time_counter
                            target_time = obj.time_resampled[time_counter] + 2
                            while obj.time_resampled[time_counter] < target_time:
                                time_counter += 1
                            if time_counter >= maneuvre[i][1][1]:
                                m_f = maneuvre[i][1][1]
                            else:    
                                m_f = time_counter
                    if aux_mi < maneuvre[i][1][1]:
                        if m_f > m_i and aux_mf > aux_mi and aux_mi > m_i:
                            maneuvre[i].append([m_i, m_f])
                            maneuvre[i].append([aux_mi, aux_mf])
                            coerence.append(2)
                        else:
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            coerence.append(1)
                    else:
                        maneuvre[i].append([m_i, m_f])
                        maneuvre[i].append([m_i, m_f])
                        coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0
            
            if maneuvre[i] != 0:
                if maneuvre[i][0] == "ESC_PartialBrkinTurn":
                    target_time = obj.time_resampled[maneuvre[i][2][0]] - 2
                    time_counter = maneuvre[i][2][0]
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:
                        m_i = time_counter
                    time_counter = m_i
                    while obj.objectives[self.reference_string_speed[i] + "_ms"][time_counter] > 0.5/3.6 and time_counter < maneuvre[i][2][1]:
                        time_counter += 1
                    if time_counter >= maneuvre[i][1][1]:
                        time_counter = m_i
                        while obj.objectives[self.reference_string_speed[i] + "_ms"][time_counter] > 10/3.6 and time_counter < maneuvre[i][2][1]:
                            time_counter += 1
                        m_f = time_counter
                    else:
                        m_f = time_counter
                    if m_f > m_i:
                        maneuvre[i].append([m_i, m_f])

            if throttle_check:    
                if maneuvre[i][0] == "ESC_PowerOffinTurn":
                    time_counter = maneuvre[i][1][0]
                    not_found = True
                    while not_found:
                        while abs(obj.objectives["GasPedalPosition"][time_counter + 10] - obj.objectives["GasPedalPosition"][time_counter]) > throttle_threshold:
                            time_counter += 1
                        if obj.objectives["GasPedalPosition"][time_counter] < 0.1*max_gas:
                            not_found = False
                        else:
                            time_counter += 1
                        if time_counter == maneuvre[i][1][1]:
                            time_counter = maneuvre[i][1][0]
                            not_found = False
                    while (obj.objectives["GasPedalPosition"][time_counter] - obj.objectives["GasPedalPosition"][time_counter - 10]) < -throttle_threshold:
                        time_counter -= 1
                    time_counter = time_counter - 10
                    while (obj.objectives["GasPedalPosition"][time_counter + 1] - obj.objectives["GasPedalPosition"][time_counter]) > -throttle_threshold:
                        time_counter += 1
                    aux_mi = time_counter
                    target_time = obj.time_resampled[time_counter] - 2
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:
                        m_i = time_counter
                    time_counter = m_i
                    if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                        if m_i < maneuvre[i][1][1]:
                            for j in range(m_i, maneuvre[i][1][1]):
                                try:
                                    if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                        if "OpticalSpeed_ms" in obj.objectives:
                                            self.reference_string_speed[i] = "OpticalSpeed"
                                            self.speed_index[i] = 1
                                        else:    
                                            self.reference_string_speed[i] = "VehicleSpeed"
                                            self.speed_index[i] = 2
                                        break
                                except KeyError:
                                    pass
                                except IndexError:
                                    pass
                    go = True
                    ctrl = True
                    while go:
                        try:
                            while obj.objectives[self.reference_string_speed[i] + "_ms"][time_counter] > 0.5/3.6 and time_counter <= maneuvre[i][1][1]:
                                time_counter += 1
                            go = False
                        except IndexError:
                            if self.reference_string_speed[i] != "VehicleSpeed":
                                self.reference_string_speed[i] = speed_list[self.speed_index[i] + 1]
                                self.speed_index[i] = self.speed_index[i] + 1
                                time_counter = m_i
                            else:
                                maneuvre_controls.append(i)
                                ctrl = False
                                go = False
                                break
                        except KeyError:
                            if self.reference_string_speed[i] != "VehicleSpeed":
                                self.reference_string_speed[i] = speed_list[self.speed_index[i] + 1]
                                self.speed_index[i] = self.speed_index[i] + 1
                                time_counter = m_i
                            else:
                                maneuvre_controls.append(i)
                                ctrl = False
                                go = False
                                break
                    if ctrl:
                        if time_counter >= maneuvre[i][1][1]:
                            time_counter = m_i
                            go = True
                            while go:
                                try:
                                    while obj.objectives[self.reference_string_speed[i] + "_ms"][time_counter] > 10/3.6 and time_counter <= maneuvre[i][1][1]:
                                        time_counter += 1
                                    go = False
                                except IndexError:
                                    if self.reference_string_speed[i] != "VehicleSpeed":
                                        self.reference_string_speed[i] = speed_list[self.speed_index[i] + 1]
                                        self.speed_index[i] = self.speed_index[i] + 1
                                        time_counter = m_i
                                    else:
                                        maneuvre_controls.append(i)
                                        ctrl = False
                                        go = False
                                        break
                                except KeyError:
                                    if self.reference_string_speed[i] != "VehicleSpeed":
                                        self.reference_string_speed[i] = speed_list[self.speed_index[i] + 1]
                                        self.speed_index[i] = self.speed_index[i] + 1
                                        time_counter = m_i
                                    else:
                                        maneuvre_controls.append(i)
                                        ctrl = False
                                        go = False
                                        break
                            if time_counter >= maneuvre[i][1][1]:
                                m_f = maneuvre[i][1][1]
                            else:
                                m_f = time_counter
                        else:
                            m_f = time_counter
                        if ctrl:
                            if aux_mi < maneuvre[i][1][1]:
                                if m_f > m_i and m_f > aux_mi:
                                    maneuvre[i].append([m_i, m_f])
                                    maneuvre[i].append([aux_mi, m_f])
                                    coerence.append(2)
                                else:
                                    maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                                    maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                                    coerence.append(1)
                            else:
                                maneuvre[i].append([m_i, m_f])
                                maneuvre[i].append([m_i, m_f])
                                coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0
            
            if throttle_check:
                if maneuvre[i][0] == "ESC_PowerOninTurn":
                    time_counter = maneuvre[i][1][0]
                    not_found = True
                    while not_found:
                        while abs(obj.objectives["GasPedalPosition"][time_counter + 10] - obj.objectives["GasPedalPosition"][time_counter]) < throttle_threshold:
                            time_counter += 1
                        if obj.objectives["GasPedalPosition"][time_counter] > 0.6*max_gas:
                            not_found = False
                        else:
                            time_counter += 1
                        if time_counter == maneuvre[i][1][1]:
                            time_counter = maneuvre[i][1][0]
                            not_found = False
                    while abs(obj.objectives["GasPedalPosition"][time_counter] - obj.objectives["GasPedalPosition"][time_counter - 10]) > throttle_threshold:
                        time_counter -= 1
                    time_counter = time_counter - 10
                    while abs(obj.objectives["GasPedalPosition"][time_counter + 1] - obj.objectives["GasPedalPosition"][time_counter]) < throttle_threshold:
                        time_counter += 1
                    aux_mi = time_counter
                    target_time = obj.time_resampled[time_counter] - 2
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:
                        m_i = time_counter
                    time_counter = aux_mi
                    while abs(obj.objectives["GasPedalPosition"][time_counter + 10] - obj.objectives["GasPedalPosition"][time_counter]) > throttle_threshold:
                        time_counter += 1
                    while abs(obj.objectives["GasPedalPosition"][time_counter + 10] - obj.objectives["GasPedalPosition"][time_counter]) < throttle_threshold:
                        time_counter += 1
                    time_counter = time_counter + 10
                    while abs(obj.objectives["GasPedalPosition"][time_counter + 10] - obj.objectives["GasPedalPosition"][time_counter]) > throttle_threshold:
                        time_counter += 1
                    aux_mf = time_counter
                    target_time = obj.time_resampled[time_counter] + 3
                    while obj.time_resampled[time_counter] < target_time:
                        time_counter += 1
                    if time_counter >= maneuvre[i][1][1]:
                        m_f = maneuvre[i][1][1]
                    else:
                        m_f = time_counter
                    if aux_mi < maneuvre[i][1][1]:
                        if m_f > m_i and aux_mf > aux_mi:
                            maneuvre[i].append([m_i, m_f])
                            maneuvre[i].append([aux_mi, aux_mf])
                            coerence.append(2)
                        else:
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            coerence.append(1)
                    else:
                        maneuvre[i].append([m_i, m_f])
                        maneuvre[i].append([m_i, m_f])
                        coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0

            if steer_check:
                if maneuvre[i][0] == "ESC_RampSteer":
                    time_counter = maneuvre[i][1][0]
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 10] - obj.objectives["SteeringAngle_deg"][time_counter]) > steering_threshold_rampsteer:
                        time_counter += 1
                    time_counter = time_counter + 10
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter]) < 15:
                        time_counter += 1
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) > 0.1:
                        time_counter -= 1
                    time_counter = time_counter - 10
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 1] - obj.objectives["SteeringAngle_deg"][time_counter]) < 0.01:
                        time_counter += 1 
                    aux_mi = time_counter
                    aux_f = aux_mi
                    target_time = obj.time_resampled[time_counter] - 3
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:
                        m_i = time_counter
                    while abs(obj.objectives["SteeringAngle_deg"][aux_mi + 50]) - abs(obj.objectives["SteeringAngle_deg"][aux_mi]) >= -10 and aux_mi <= maneuvre[i][1][1]:
                        aux_mi += 1    
                    if aux_mi >= maneuvre[i][1][1]:
                        m_f = maneuvre[i][1][1]
                    else:
                        m_f = aux_mi
                    if aux_f < maneuvre[i][1][1]:
                        if m_f > m_i and m_f > aux_f:
                            maneuvre[i].append([m_i, m_f])
                            maneuvre[i].append([aux_f, m_f])
                            coerence.append(2)
                        else:
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            coerence.append(1)
                    else:
                        maneuvre[i].append([m_i, m_f])
                        maneuvre[i].append([m_i, m_f])
                        coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0

            if steer_check:
                if maneuvre[i][0] == "ESC_StepSteer":
                    time_counter = maneuvre[i][1][0]
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 10] - obj.objectives["SteeringAngle_deg"][time_counter]) > steering_rate_threshold:
                        time_counter += 1
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 10] - obj.objectives["SteeringAngle_deg"][time_counter]) < steering_rate_threshold or abs(obj.objectives["SteeringAngle_deg"][time_counter])/abs(max_steer) < 0.1:
                        time_counter += 1
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter] - obj.objectives["SteeringAngle_deg"][time_counter - 10]) > 0.1:
                        time_counter -= 1
                    time_counter = time_counter - 10
                    while abs(obj.objectives["SteeringAngle_deg"][time_counter + 1] - obj.objectives["SteeringAngle_deg"][time_counter]) < 0.01:
                        time_counter += 1
                    aux_mi = time_counter
                    aux_f = time_counter
                    target_time = obj.time_resampled[time_counter] - 2
                    while obj.time_resampled[time_counter] > target_time:
                        time_counter -= 1
                    if time_counter <= maneuvre[i][1][0]:
                        m_i = maneuvre[i][1][0]
                    else:
                        m_i = time_counter
                    while abs(obj.objectives["SteeringAngle_deg"][aux_mi]) <= 15 and aux_mi <= maneuvre[i][1][1]:
                        aux_mi += 1
                    while abs(obj.objectives["SteeringAngle_deg"][aux_mi]) > 15 and aux_mi <= maneuvre[i][1][1]:
                        aux_mi += 1
                    if aux_mi >= maneuvre[i][1][1]:
                        m_f = maneuvre[i][1][1]
                    else:
                        m_f = aux_mi
                    if m_i < maneuvre[i][1][1]:
                        if m_f > m_i and m_f > aux_f:
                            maneuvre[i].append([m_i, m_f])
                            maneuvre[i].append([aux_f, m_f])
                            coerence.append(2)
                        else:
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                            coerence.append(1)
                    else:
                        maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                        maneuvre[i].append([maneuvre[i][1][0], maneuvre[i][1][1]])
                        coerence.append(1)
            else:
                if "ESC" in maneuvre[i][0]:
                    maneuvre[i] = 0

            if type(maneuvre[i]) != int:
                if maneuvre[i][0] not in ["ESC_PowerOffinTurn", "ESC_PartialBrkinTurn", "ESC_ConstantRadius"] and "ABS" not in maneuvre[i][0] and "TCS" not in maneuvre[i][0]:
                    if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                        for j in range(maneuvre[i][2][0], maneuvre[i][2][1]):
                            try:
                                if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                    if "OpticalSpeed_ms" in obj.objectives:
                                        self.reference_string_speed[i] = "OpticalSpeed"
                                        self.speed_index[i] = 1
                                    else:    
                                        self.reference_string_speed[i] = "VehicleSpeed"
                                        self.speed_index[i] = 2
                                    break
                            except KeyError:
                                pass
                            except IndexError:
                                pass
                    for j in range(self.speed_index[i], len(speed_list)):
                        try:
                            auxiliar_speed = obj.objectives[speed_list[j] + "_ms"][maneuvre[i][1][1]]
                            self.reference_string_speed[i] = speed_list[j]
                            self.speed_index[i] = j
                            break
                        except IndexError:
                            if self.reference_string_speed[i] == "VehicleSpeed":
                                maneuvre_controls.append(i)
                                break
                        except KeyError:
                            if self.reference_string_speed[i] == "VehicleSpeed":
                                maneuvre_controls.append(i)
                                break
            
            if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                speed_check[i - len(maneuvre)] = "VBOX"
            elif self.reference_string_speed[i] == "OpticalSpeed":
                speed_check[i - len(maneuvre)] = "TestaOttica"
            else:
                speed_check[i - len(maneuvre)] = "Internal"

            if steer_check and throttle_check and ctrl:
                if maneuvre[i][0] in ["ESC_StepSteer", "ESC_RampSteer", "ESC_LaneChange", "ESC_Slalom"]:
                    frequency = obj.frequency
                    in_yaw = np.mean(obj.objectives["YawRate_degs"][maneuvre[i][3][0]-int(round(0.5*frequency)):maneuvre[i][3][0]])
                    in_ay = np.mean(obj.objectives["Ay"][maneuvre[i][3][0]-int(round(0.5*frequency)):maneuvre[i][3][0]])
                    in_lws = np.mean(obj.objectives["SteeringAngle_deg"][maneuvre[i][3][0]-int(round(0.5*frequency)):maneuvre[i][3][0]])
                    if abs(in_yaw) < 1 and abs(in_ay) < 0.5 and abs(in_lws) < 5:
                        direction_check[i-len(maneuvre)] = True
                    else:
                        direction_check[i-len(maneuvre)] = False
                    if abs(in_yaw) > 1:
                        yaw_check[i-len(maneuvre)] = False
                    else:
                        yaw_check[i-len(maneuvre)] = True
                    if abs(in_ay) > 0.5:
                        ay_check[i-len(maneuvre)] = False
                    else:
                        ay_check[i-len(maneuvre)] = True
                    if abs(in_lws) > 5:
                        lws_check[i-len(maneuvre)] = False
                    else:
                        lws_check[i-len(maneuvre)] = True
                else:
                    if maneuvre[i][0] in ["ESC_PartialBrkinTurn", "ESC_PowerOffinTurn", "ESC_PowerOninTurn"]:
                        if maneuvre[i][0] == "ESC_PartialBrkinTurn":
                            in_yaw = np.mean(obj.objectives["YawRate_degs"][maneuvre[i][2][0]-int(round(0.5*obj.frequency)):maneuvre[i][2][0]])
                            in_ay = np.mean(obj.objectives["Ay"][maneuvre[i][2][0]-int(round(0.5*obj.frequency)):maneuvre[i][2][0]])
                            in_lws = np.mean(obj.objectives["SteeringAngle_deg"][maneuvre[i][2][0]-int(round(0.5*obj.frequency)):maneuvre[i][2][0]])
                            for k in range(maneuvre[i][2][0]-int(round(0.5*obj.frequency)), maneuvre[i][2][0]):
                                if abs(obj.objectives["YawRate_degs"][k]-in_yaw) > 2:
                                    yaw_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    yaw_check[i-len(maneuvre)] = True
                                if abs(obj.objectives["Ay"][k]-in_ay) > 1:
                                    ay_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    ay_check[i-len(maneuvre)] = True
                                if abs(obj.objectives["SteeringAngle_deg"][k]-in_lws) > 10:
                                    lws_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    lws_check[i-len(maneuvre)] = True
                        else:
                            in_yaw = np.mean(obj.objectives["YawRate_degs"][maneuvre[i][3][0]-int(round(0.5*obj.frequency)):maneuvre[i][3][0]])
                            in_ay = np.mean(obj.objectives["Ay"][maneuvre[i][3][0]-int(round(0.5*obj.frequency)):maneuvre[i][3][0]])
                            in_lws = np.mean(obj.objectives["SteeringAngle_deg"][maneuvre[i][3][0]-int(round(0.5*obj.frequency)):maneuvre[i][3][0]])
                            for k in range(maneuvre[i][3][0]-int(round(0.5*obj.frequency)), maneuvre[i][3][0]):
                                if abs(obj.objectives["YawRate_degs"][k]-in_yaw) > 2:
                                    yaw_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    yaw_check[i-len(maneuvre)] = True
                                if abs(obj.objectives["Ay"][k]-in_ay) > 1:
                                    ay_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    ay_check[i-len(maneuvre)] = True
                                if abs(obj.objectives["SteeringAngle_deg"][k]-in_lws) > 10:
                                    lws_check[i-len(maneuvre)] = False
                                    break
                                else:
                                    lws_check[i-len(maneuvre)] = True
                        if yaw_check[i-len(maneuvre)] and ay_check[i-len(maneuvre)] and lws_check[i-len(maneuvre)]:
                            direction_check[i-len(maneuvre)] = True
                        else:
                            direction_check[i-len(maneuvre)] = False
        for item in maneuvre_controls:
            maneuvre[item] = 0
            self.reference_string_speed[item] = 0
        return maneuvre

    def TCS_maneuvre_recognition(self, obj, maneuvre, coerence, speed_check, yaw_check, direction_check, ay_check, lws_check):
        throttle_pedal_threshold = 1 #threshold to leave an edge on throttle pedal pressing
        throttle_check = True
        maneuvre_controls = []
        for i in range(len(maneuvre)):
            if type(maneuvre[i]) != int:
                if "TCS" in maneuvre[i][0]:
                    try:
                        auxiliar_throttle = obj.objectives["GasPedalPosition"][maneuvre[i][1][1]]
                    except IndexError:
                        throttle_check = False
                        maneuvre_controls.append(i)
                    except KeyError:
                        throttle_check = False
                        maneuvre_controls.append(i)
                    except TypeError:
                        throttle_check = False
            if throttle_check:
                if type(maneuvre[i]) != int:
                    if "TCS" in maneuvre[i][0]:
                        time_counter = maneuvre[i][1][0]
                        try:
                            while obj.objectives["GasPedalPosition"][time_counter] > throttle_pedal_threshold:
                                time_counter += 1
                            while obj.objectives["GasPedalPosition"][time_counter] < throttle_pedal_threshold:
                                time_counter += 1
                            tpp_i = time_counter
                            max_throttle = np.max(self.signal_fragment_recovery(maneuvre[i], obj, "GasPedalPosition", 1))
                            while obj.objectives["GasPedalPosition"][time_counter] < max_throttle:
                                time_counter += 1
                            while obj.objectives["GasPedalPosition"][time_counter] > 0.7*max_throttle:
                                time_counter += 1
                            tpp_f = time_counter
                        except IndexError:
                            tpp_f = maneuvre[i][1][1] + 10
                        if tpp_f > maneuvre[i][1][1] or tpp_f <= maneuvre[i][1][0]:
                            tpp_i = maneuvre[i][1][0]
                            tpp_f = maneuvre[i][1][1]
                            maneuvre[i].append([tpp_i, tpp_f])
                            coerence.append(1)
                        else:
                            maneuvre[i].append([tpp_i, tpp_f])
                            coerence.append(2)
                if type(maneuvre[i]) != int:
                    if "TCS" in maneuvre[i][0]:
                        if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                            for j in range(maneuvre[i][2][0], maneuvre[i][2][1]):
                                try:
                                    if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                        if "OpticalSpeed_ms" in obj.objectives:
                                            self.reference_string_speed[i] = "OpticalSpeed"
                                            self.speed_index[i] = 1
                                        else:    
                                            self.reference_string_speed[i] = "VehicleSpeed"
                                            self.speed_index[i] = 2
                                        break
                                except KeyError:
                                    pass
                                except IndexError:
                                    pass
                        speed_list = ["ReferenceSpeed", "OpticalSpeed", "VehicleSpeed"]
                        for j in range(self.speed_index[i], len(speed_list)):
                            try:
                                auxiliar_speed = obj.objectives[speed_list[j] + "_ms"][maneuvre[i][1][1]]
                                self.reference_string_speed[i] = speed_list[j]
                                self.speed_index[i] = j
                                break
                            except IndexError:
                                if self.reference_string_speed[i] == "VehicleSpeed":
                                    maneuvre_controls.append(i)
                                    break
                            except KeyError:
                                if self.reference_string_speed[i] == "VehicleSpeed":
                                    maneuvre_controls.append(i)
                                    break
                    # yaw_check.append("")
                    # ay_check.append("")
                    # lws_check.append("")
                    # direction_check.append("")
                if self.reference_string_speed[i] == "ReferenceSpeed" or self.reference_string_speed[i] == "RawSpeed":
                    speed_check[i  - len(maneuvre)] = "VBOX"
                elif self.reference_string_speed[i] == "OpticalSpeed":
                    speed_check[i - len(maneuvre)] = "TestaOttica"
                else:
                    speed_check[i - len(maneuvre)] = "Internal"
        for item in maneuvre_controls:
            maneuvre[item] = 0
            self.reference_string_speed[item] = 0
        return maneuvre