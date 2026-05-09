import numpy as np

class SlipRepartition():

    def time_slip_ratio(self, maneuver, dictionaries, reference_speed, wheel_slip_check, check_2, check_3, check_4):
        time_counter = maneuver[2][0]
        found = True
        while dictionaries.objectives["ABSTrigger_FL"][time_counter] < 1 and dictionaries.objectives["ABSTrigger_FR"][time_counter] < 1 and dictionaries.objectives["ABSTrigger_RL"][time_counter] < 1 and dictionaries.objectives["ABSTrigger_RR"][time_counter] < 1 and dictionaries.objectives[reference_speed + "_ms"][time_counter] > 5/3.6 and time_counter <= maneuver[2][1]:
            time_counter += 1
        if reference_speed == "ReferenceSpeed" or reference_speed == "RawSpeed":
            if check_2:            
                wheel_slip_fl = (dictionaries.objectives["WheelSpeed_FL_ms"][maneuver[2][0]: time_counter] - dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter])/dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter]
                wheel_slip_fr = (dictionaries.objectives["WheelSpeed_FR_ms"][maneuver[2][0]: time_counter] - dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter])/dictionaries.objectives[reference_speed + "_ms"][maneuver[2][0]: time_counter]
                mean_wheel_slip_front = np.mean([wheel_slip_fl, wheel_slip_fr])
                wheel_slip_check.append(False) #True = devi colorare la cella. False = Non devi colorare la cella.
            else:
                time_perc_slip_ratio_positive = "ACQUISITION ERROR"
                time_perc_slip_ratio_negative = "ACQUISITION ERROR"
                wheel_slip_check.append(False)
                found = False
        else:
            if check_3:
                mean_wheel_slip_front = np.mean([dictionaries.objectives["WheelSlip_FL"][maneuver[2][0]: time_counter], dictionaries.objectives["WheelSlip_FR"][maneuver[2][0]: time_counter]])
                wheel_slip_check.append(True)
            else:
                time_perc_slip_ratio_positive = "N/A"
                time_perc_slip_ratio_negative = "N/A"
                found = False
                wheel_slip_check.append(False)

        if found and mean_wheel_slip_front <= -0.02 and check_4:
            slip_ratio_array = (np.mean([dictionaries.objectives["WheelSpeed_RL_ms"][maneuver[2][0]: time_counter], dictionaries.objectives["WheelSpeed_RR_ms"][maneuver[2][0]: time_counter]], axis = 0) - np.mean([dictionaries.objectives["WheelSpeed_FL_ms"][maneuver[2][0]: time_counter], dictionaries.objectives["WheelSpeed_FR_ms"][maneuver[2][0]: time_counter]], axis = 0))/np.mean([dictionaries.objectives["WheelSpeed_FL_ms"][maneuver[2][0]: time_counter], dictionaries.objectives["WheelSpeed_FR_ms"][maneuver[2][0]: time_counter]], axis = 0)
            pos_counter = 0
            neg_counter = 0
            for i in range(len(slip_ratio_array)):
                if slip_ratio_array[i] >= 0:
                    pos_counter += 1
                else:
                    neg_counter += 1
            time_perc_slip_ratio_positive = pos_counter/len(slip_ratio_array)*100
            time_perc_slip_ratio_negative = neg_counter/len(slip_ratio_array)*100
        else:
            wheel_slip_check[-1] = False
            try:
                time_perc_slip_ratio_negative = time_perc_slip_ratio_negative
            except UnboundLocalError:
                time_perc_slip_ratio_negative = ""
                time_perc_slip_ratio_positive = ""

        return time_perc_slip_ratio_negative, time_perc_slip_ratio_positive