from ManualManeuvreRecognition import ManualManeuvreRecognition as MMR

class ManualBrakingRecognition(MMR):

    def __init__ (self, input_management_obj, coerence, speed_check):
        self.trigger_check = []
        self.reference_string_speed, self.reference_string_decel, self.reference_string_angle = self.signals_management(input_management_obj)
        speed_list = ["ReferenceSpeed", "OpticalSpeed", "VehicleSpeed"]
        input_management_obj.speed_index = 0
        if "ReferenceSpeed_ms" not in input_management_obj.objectives:
            for j in range(len(speed_list)):
                if speed_list[j] + "_ms" in input_management_obj.objectives:
                    self.reference_string_speed = speed_list[j]
                    input_management_obj.speed_index = j
                    break
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
        self.maneuvre = self.no_trigger_braking(input_management_obj, coerence, speed_check)
    
    def no_trigger_braking(self, obj, coerence, speed_check):
        #brake_pedal_threshold_1 = 5 #threshold to leave an edge on brake pedal pressing
        brake_pedal_threshold = 1.5
        speed_threshold = [0.14, 0.28, 0.56, 5/3.6, 10/3.6]  #0.56m/s = 2km/h
        speed_list = ["ReferenceSpeed", "OpticalSpeed", "VehicleSpeed"]
        maneuvers = []
        reference_string_speed = []
        speed_index = []
        i = 0
        if "BrakePedalPosition" in obj.objectives:
            while i < len(obj.objectives["BrakePedalPosition"]):
                try:
                    if i == 0:
                        if obj.objectives["BrakePedalPosition"][i] > brake_pedal_threshold: #_1
                            while obj.objectives["BrakePedalPosition"][i] > brake_pedal_threshold: #_1
                                i += 1
                        else:
                            i += 1
                    else:
                        while obj.objectives["BrakePedalPosition"][i] <= brake_pedal_threshold:
                            i += 1
                        maneuver_i = i
                        while obj.objectives["BrakePedalPosition"][i] > brake_pedal_threshold:
                            i += 1
                        maneuver_f = i
                        go = True
                        while go:
                            try:
                                if obj.objectives[self.reference_string_speed + "_kmh"][maneuver_i] >= 0:
                                    maneuvers.append(["ABS_Braking", [maneuver_i, maneuver_f]])
                                go = False
                            except IndexError:
                                if self.reference_string_speed != "VehicleSpeed":
                                    if speed_list[obj.speed_index + 1] + "_kmh" in obj.objectives:
                                        self.reference_string_speed = speed_list[obj.speed_index + 1]
                                        obj.speed_index = obj.speed_index + 1
                                    else:
                                        obj.speed_index += 1
                                else:
                                    go = False
                                    i = len(obj.objectives["BrakePedalPosition"])
                except IndexError:
                    break
            for i in range(len(maneuvers)):
                if i == 0:
                    reference_string_speed = [self.reference_string_speed]
                    if self.reference_string_speed == "ReferenceSpeed":
                        speed_index = [0]
                    elif self.reference_string_speed == "OpticalSpeed":
                        speed_index = [1]
                    else:
                        speed_index = [2]
                else:
                    reference_string_speed.append(self.reference_string_speed)
                    if self.reference_string_speed == "ReferenceSpeed":
                        speed_index.append(0)
                    elif self.reference_string_speed == "OpticalSpeed":
                        speed_index.append(1)
                    else:
                        speed_index.append(2)
                if "ReferenceSpeed_ms" not in obj.objectives:
                    for j in range(len(speed_list)):
                        if speed_list[j] + "_ms" in obj.objectives:
                            reference_string_speed[i] = speed_list[j]
                            speed_index[i] = j
                            break
                abs_check = True
                for j in range(speed_index[i], len(speed_list)):
                    try:
                        auxiliar_speed = obj.objectives[speed_list[j] + "_ms"][maneuvers[i][1][1]]
                        reference_string_speed[i] = speed_list[j]
                        speed_index[i] = j
                        break
                    except IndexError:
                        pass
                    except KeyError:
                        pass
                #aggiungere qui (e anche in MMR) un controllo tale per cui, se  i satelliti vanno a zero anche in un solo sample della manovra, la velocità usata sarà quella da BCU e la cosa
                #dovrà essere segnalata (speed_check true)
                if abs_check:
                    time_counter = maneuvers[i][1][0]
                    bpp_f_found = False
                    while not bpp_f_found:
                        bpp_i = time_counter
                        for item in speed_threshold:
                            time_counter = bpp_i
                            if reference_string_speed[i] == "ReferenceSpeed" or reference_string_speed[i] == "RawSpeed":
                                if bpp_i < maneuvers[i][1][1]:
                                    for j in range(bpp_i, maneuvers[i][1][1]):
                                        try:
                                            if obj.objectives["Satellites"][j] == 0 and obj.objectives["Satellites"][j+int(0.2*obj.frequency)] == 0:
                                                if "OpticalSpeed_ms" in obj.objectives:
                                                    reference_string_speed[i] = "OpticalSpeed"
                                                    speed_index[i] = 1
                                                    try:
                                                        auxiliar_speed = obj.objectives["OpticalSpeed_ms"][maneuvers[i][1][1]]
                                                    except IndexError:
                                                        reference_string_speed[i] = "VehicleSpeed"
                                                        speed_index[i] = 2
                                                else:    
                                                    reference_string_speed[i] = "VehicleSpeed"
                                                    speed_index[i] = 2
                                                break
                                        except KeyError:
                                            pass
                                        except IndexError:
                                            pass
                            while obj.objectives["BrakePedalPosition"][time_counter] >= brake_pedal_threshold:
                                if obj.objectives[reference_string_speed[i] + "_ms"][time_counter] < item:
                                    bpp_f = time_counter - 1
                                    bpp_f_found = True
                                    break
                                else:
                                    time_counter += 1
                                if time_counter == maneuvers[i][1][1]: 
                                    break
                            if obj.objectives["BrakePedalPosition"][time_counter] <= brake_pedal_threshold and not time_counter == maneuvers[i][1][1]:
                                if obj.time_resampled[time_counter] - obj.time_resampled[bpp_i] > 0.2:
                                    bpp_f = time_counter - 1
                                    bpp_f_found = True
                            else:
                                break
                            if bpp_f_found:
                                break
                        if time_counter == maneuvers[i][1][1]: 
                            bpp_f = time_counter
                            bpp_f_found = True
                    if obj.time_resampled[bpp_f] - obj.time_resampled[bpp_i] > 1:
                        if bpp_i < maneuvers[i][1][1]:
                            maneuvers[i].append([bpp_i, bpp_f])
                            coerence.append(2)
                        else:
                            maneuvers[i].append([maneuvers[i][1][0], maneuvers[i][1][1]])
                            coerence.append(1)
                    else:
                        maneuvers[i].append([maneuvers[i][1][0], maneuvers[i][1][1]])
                        coerence.append(1)
                self.trigger_check.append("ND")
                if reference_string_speed[i] == "ReferenceSpeed" or reference_string_speed[i] == "RawSpeed":
                    speed_check.append("VBOX")
                elif reference_string_speed[i] == "OpticalSpeed":
                    speed_check.append("TestaOttica")
                else:
                    speed_check.append("Internal")
            self.reference_string_speed = reference_string_speed
            self.speed_index = speed_index
        else:
            self.reference_string_speed = []     
        return maneuvers

