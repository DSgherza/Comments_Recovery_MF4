import numpy as np

class SpeedlPerformance():

    def nominal_speed(self, maneuvres, dictionaries, base, string, i):
        nominal_list = [250, 200, 160, 150, 130, 120, 110, 100, 90, 80, 75, 70, 60, 55, 50, 40, 30, 25, 15, 10]
        v_actual = dictionaries.objectives[string + "_kmh"][maneuvres[base][0]]
        if dictionaries.target_speed[i] != "":
            v_nominal = dictionaries.target_speed[i]
            min_error = abs(v_nominal - v_actual)
        else:
            error_nominal_list = []
            
            for i in range(len(nominal_list)):
                error_nominal_list.append(abs(nominal_list[i] - v_actual))
            min_error = error_nominal_list[0]
            counter = 0
            for i in range(1, len(error_nominal_list)):
                if min_error > error_nominal_list[i]:
                    min_error = error_nominal_list[i]
                    counter = i
            v_nominal = nominal_list[counter]
        if "ABS" in maneuvres[0] or ("ESC" in maneuvres[0] and "ESC_ConstantRadius" != maneuvres[0] and "ESC_Handling" != maneuvres[0]):
            if v_nominal < 100:
                if min_error > 2:
                    control = False
                else:
                    control = True
            else:
                if min_error/v_nominal*100 > 2:
                    control = False
                else:
                    control = True
        elif "ESC_ConstantRadius" == maneuvres[0]:
            if v_nominal < 100:
                if min_error > 2:
                    control = False
                else:
                    control = True
            else:
                if min_error/v_nominal*100 > 2:
                    control = False
                else:
                    control = True
            if v_nominal == 10:
                if v_actual > 2:
                    control = False
                else:
                    control = True
        elif "TCS" in maneuvres[0]:
            if v_actual > 2:
                control = False
            else:
                control = True
        elif "ESC_Handling" == maneuvres[0]:
            control = True
        return v_nominal, v_actual, control
    
    # def speed_average(self, maneuvres, dictionaries):
    #     average_speed = ["Average Speed"]
    #     vel_maneuvre = []
    #     samples = []
    #     for i in range(len(maneuvres.maneuvre)):
    #         time_counter = maneuvres.maneuvre[i][1][0]
    #         list_vel_maneuvre = []
    #         list_samples = []
    #         while time_counter <= maneuvres.maneuvre[i][1][1]:
    #             if "ReferenceSpeed" in dictionaries.objectives:
    #                 maneuvres.reference_string = "ReferenceSpeed"
    #             else:
    #                 maneuvres.reference_string = "VehicleSpeed"
    #             list_vel_maneuvre.append(dictionaries.objectives[maneuvres.reference_string + "_kmh"][time_counter])
    #             list_samples.append(time_counter)
    #             time_counter += 1
    #         samples.append(list_samples)
    #         vel_maneuvre.append(np.array(list_vel_maneuvre))
    #         average_speed.append(round(np.mean(vel_maneuvre[i]), 2))
    #     return average_speed, vel_maneuvre, samples
    
    # def speed_loss(self, maneuvres, vel_maneuvre, speed_average, parameters_list):
    #     #chiedere meglio a Monica
    #     #RIPARTI DA QUI!!
    #     speed_loss = ["Speed Loss"]
    #     for i in range(len(maneuvres.maneuvre)):
    #         max_vel = np.max(vel_maneuvre[i])
    #         speed_loss.append(round(max_vel/speed_average[i+1], 2))
    #     parameters_list.append(speed_loss)
    #     return parameters_list

    def speed_accuracy(self, dictionaries, maneuver, reference_speed_string, axle):
        if "VehicleSpeed" != reference_speed_string:
            if "ABS" in maneuver[0] or "ESC_PartialBrkinTurn" == maneuver[0]:
                end = maneuver[2][1]
                for i in range(len(dictionaries.objectives[reference_speed_string + "_kmh"][maneuver[2][0]: maneuver[2][1]])):
                    if dictionaries.objectives[reference_speed_string + "_kmh"][maneuver[2][0] + i] < 10:
                        end = maneuver[2][0] + i
                        break
                reference_speed = dictionaries.objectives[reference_speed_string + "_kmh"][maneuver[2][0]: end]
                try:
                    vehicle_speed = dictionaries.objectives["VehicleSpeedBraking" + axle + "_kmh"][maneuver[2][0]: end]
                    speed_error = (vehicle_speed - reference_speed)/reference_speed
                    accuracy_avg = np.mean(speed_error*100)
                    accuracy_avg_abs = np.mean(abs(speed_error*100))
                except KeyError:
                    accuracy_avg = ""
                    accuracy_avg_abs = ""
            elif "TCS" in maneuver[0]:
                reference_speed = dictionaries.objectives[reference_speed_string + "_kmh"][maneuver[2][0]: maneuver[2][1]]
                try:
                    vehicle_speed = dictionaries.objectives["VehicleSpeedTraction" + axle + "_kmh"][maneuver[2][0]: maneuver[2][1]]
                    speed_error = (vehicle_speed - reference_speed)/reference_speed
                    accuracy_avg = np.mean(speed_error*100)
                    accuracy_avg_abs = np.mean(abs(speed_error*100))
                except KeyError:
                    accuracy_avg = ""
                    accuracy_avg_abs = ""
            elif "ESC" in maneuver[0] and "ESC_Handling" != maneuver[0]:
                reference_speed = dictionaries.objectives[reference_speed_string + "_kmh"][maneuver[3][0]: maneuver[3][1]]
                vehicle_speed = dictionaries.objectives["VehicleSpeed" + axle + "_kmh"][maneuver[3][0]: maneuver[3][1]]
                speed_error = (vehicle_speed - reference_speed)/reference_speed
                accuracy_avg = np.mean(speed_error*100)
                accuracy_avg_abs = np.mean(abs(speed_error*100))
            else:
                accuracy_avg = ""
                accuracy_avg_abs = ""
        else:
            accuracy_avg = ""
            accuracy_avg_abs = ""
        return accuracy_avg, accuracy_avg_abs

