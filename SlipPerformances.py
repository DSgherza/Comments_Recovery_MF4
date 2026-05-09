import numpy as np

class SlipPerformances:
    def slip_target_accuracy(self, maneuver, dictionaries, reference_speed, corner_string):
        time_counter = maneuver[2][0]
        time_counter_2 = maneuver[2][1]
        check_abs = True
        check_wheel_speed = True
        check_wheel_slip = True
        if "ABSTrigger_FL" in dictionaries.objectives:
            try:
                while dictionaries.objectives["ABSTrigger_" + corner_string][time_counter] < 1 and time_counter <= maneuver[2][1]:
                    time_counter += 1
            except KeyError:
                check_abs = False
                slip_target_accuracy = "N/A"
                time_int = ""
            if check_abs:
                while dictionaries.objectives["ABSTrigger_" + corner_string][time_counter_2] < 1 and time_counter_2 >= time_counter:
                    time_counter_2 -= 1
                vbox_speed = dictionaries.objectives[reference_speed + "_ms"][time_counter: time_counter_2]
                time = dictionaries.time_resampled[time_counter: time_counter_2]
            
                try:
                    slip_setpoint = dictionaries.objectives["SlipSetpoint_" + corner_string][time_counter: time_counter_2]
                    abs_sign = dictionaries.objectives["ABSTrigger_" + corner_string][time_counter: time_counter_2] 
                    slip_setpoint_int = slip_setpoint[abs_sign > 0.5]
                except KeyError:
                    check_abs = False
                    slip_target_accuracy = "N/A"
                    slip_setpoint_int = ""
            if reference_speed == "ReferenceSpeed" or reference_speed == "RawSpeed" or reference_speed == "OpticalSpeed":
                if check_abs:
                    vbox_speed_int = vbox_speed[abs_sign > 0.5]
                    time_int = time[abs_sign > 0.5]
                    try:
                        wheel_speed = dictionaries.objectives["WheelSpeed_" + corner_string + "_ms"][time_counter: time_counter_2]
                    except KeyError:
                        check_wheel_speed = False
                        try:
                            wheel_slip = dictionaries.objectives["WheelSlip_" + corner_string][time_counter: time_counter_2]
                        except KeyError:
                            check_abs = False
                            slip_target_accuracy = "N/A"
                    if check_wheel_speed:
                        wheel_speed_int = wheel_speed[abs_sign > 0.5]
                        slip_calc = (wheel_speed_int - vbox_speed_int)/vbox_speed_int
                        slip_difference = abs(-slip_calc - slip_setpoint_int)
                        slip_target_accuracy = np.mean((-slip_calc - slip_setpoint_int)*100)
                    
                    else:
                        wheel_slip_int = wheel_slip[abs_sign > 0.5]
                        slip_difference = abs(-wheel_slip_int - slip_setpoint_int)
                        slip_target_accuracy = np.mean((-wheel_slip_int - slip_setpoint_int)*100)
                else:
                    slip_target_accuracy = "N/A"
                    slip_difference = ""
                    time_int = ""
                    vbox_speed_int = ""
            else:
                if check_abs:
                    vbox_speed_int = ""
                    time_int = time[abs_sign > 0.5]
                    try:
                        wheel_slip = dictionaries.objectives["WheelSlip_" + corner_string][time_counter: time_counter_2]
                    except KeyError:
                        check_wheel_slip = False
                        slip_setpoint_int = ""
                        slip_target_accuracy = "N/A"
                        slip_difference = ""
                    if check_wheel_slip:
                        wheel_slip_int = wheel_slip[abs_sign > 0.5]
                        slip_difference = abs(-wheel_slip_int-slip_setpoint_int)
                        slip_target_accuracy = np.mean((-wheel_slip_int-slip_setpoint_int)*100)
                else:
                    slip_setpoint_int = ""
                    slip_target_accuracy = "N/A"
                    slip_difference = ""
                    time_int = ""
                    vbox_speed_int = ""
        else:
            slip_setpoint_int = ""
            slip_target_accuracy = "N/A"
            slip_difference = ""
            time_int = ""
            vbox_speed_int = ""
            check_abs = False
        return slip_target_accuracy, slip_difference, check_abs, time_int, vbox_speed_int, slip_setpoint_int
    
    def slip_control_accuracy(self, slip_difference, time, vbox_speed_int, slip_setpoint):
        num = 0
        if type(vbox_speed_int) == np.array:
            for i in range(1, len(slip_difference)):
                num = num + (slip_difference[i]*vbox_speed_int[i])*(time[i] - time[i-1])
            den = 0
            for i in range(1, len(slip_setpoint)):
                den = den + ((1-slip_setpoint[i])*vbox_speed_int[i])*(time[i] - time[i-1])
            try:
                slip_control = 1 - num/den
            except ZeroDivisionError:
                slip_control = ""
        else:
            slip_control = ""
        return slip_control