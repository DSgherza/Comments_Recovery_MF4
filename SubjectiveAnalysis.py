import pandas as pd

class SubjectiveAnalysis():
    def __init__(self, maneuvres, dictionaries, log):
        vote_list = []
        samples = 2
        for i in range(len(maneuvres.maneuvre)):
            if maneuvres.trigger_check[i] == "":
                comfort = "NR"
                performance = "NR"
                stability = "NR"
                steerability = "NR"
                surface = "NR"
                target_speed = "NR"
                target_radius = "NR"
                model = "ND"
                scenario = "ND"
                safety = "ND"
                dict_comfort = {}
                dict_steerability = {}
                dict_stability = {}
                dict_performance = {}
                for akey in dictionaries:
                    if akey == "TargetSpeed":
                        target_speed = int(dictionaries[akey][maneuvres.maneuvre[i][1][1]])
                        if target_speed == 0:
                            target_speed = "NR"
                    elif akey == "TargetRadius":
                        target_radius = int(dictionaries[akey][maneuvres.maneuvre[i][1][1]])
                        if target_radius == 0:
                            target_radius = "NR"
                    elif "SurfaceSelector_" in akey:
                        if surface == "NR":
                            if int(dictionaries[akey][maneuvres.maneuvre[i][1][1]]) == 1:
                                surface = akey.split("_")[1]
                        else:
                            if int(dictionaries[akey][maneuvres.maneuvre[i][1][1]]) == 1:
                                surface = surface + "/" + akey.split("_")[1]
                    else:
                        time_counter = maneuvres.maneuvre[i][1][2]
                        while dictionaries[akey][time_counter] < 0.5 and time_counter >= maneuvres.maneuvre[i][1][0]:
                            time_counter -= 1
                        if "Comfort" in akey and dictionaries[akey][time_counter] >= 0.5:
                            vote_array = akey.split("_")
                            comfort = int(vote_array[2])
                            dict_comfort[comfort] = time_counter
                        if "Performance" in akey and dictionaries[akey][time_counter] >= 0.5:
                            vote_array = akey.split("_")
                            performance = int(vote_array[2])
                            dict_performance[performance] = time_counter
                        if "Stability" in akey and dictionaries[akey][time_counter] >= 0.5:
                            vote_array = akey.split("_")
                            stability = int(vote_array[2])
                            dict_stability[stability] = time_counter
                        if "Steerability" in akey and dictionaries[akey][time_counter] >= 0.5:
                            vote_array = akey.split("_")
                            steerability = int(vote_array[2])
                            dict_steerability[steerability] = time_counter
                        if akey == "Safety" and dictionaries[akey][time_counter] >= 0.5:
                            safety = int(dictionaries[akey][time_counter - samples])
                            if safety == 0:
                                safety = "NR"
                        if akey == "Environment_Scenario" and dictionaries[akey][time_counter] >= 0.5:
                            scenario = int(dictionaries[akey][time_counter - samples])
                            if scenario == 0:
                                scenario = "NR"
                        if akey == "Environment_Models" and dictionaries[akey][time_counter] >= 0.5:
                            model = int(dictionaries[akey][time_counter - samples])
                            if model == 0:
                                model = "NR"
                dict_list = [dict_comfort, dict_stability, dict_performance, dict_steerability]
                votes = [comfort, stability, performance, steerability]
                for j in range(len(dict_list)):
                    if len(dict_list[j]) == 1:
                        for key in dict_list[j]:
                            votes[j] = key
                    elif len(dict_list[j]) == 0:
                        votes[j] = "NR"
                    else:
                        time_counter = 0
                        for key in dict_list[j]:
                            if dict_list[j][key] > time_counter:
                                time_counter = dict_list[j][key]
                                votes[j] = key
                vote_list.append([maneuvres.maneuvre[i][0], log, surface, target_speed, target_radius, votes[1], votes[0], votes[2], votes[3], model, scenario, safety])
            elif maneuvres.trigger_check[i] == "ND":
                vote_list.append([maneuvres.maneuvre[i][0], log, "ND", "ND", "ND", "ND", "ND", "ND", "ND", "ND", "ND", "ND"])
            else:
                vote_list.append([maneuvres.maneuvre[i][0], log, "NR", "NR", "NR", "NR", "NR", "NR", "NR", "NR", "NR", "NR"])
        self.check_array = []
        for i in range(len(vote_list)):
            check_array = []
            for j in range(5, 9):
                if vote_list[i][j] != "NR" or maneuvres.trigger_check[i]:
                    check_array.append(True)
            if check_array == []:
                vote_list[i] = 0
                self.check_array.append(False)
            else:
                self.check_array.append(True)
        vote_list = list(filter((0).__ne__, vote_list))
        self.subjective_df = pd.DataFrame(vote_list, columns=["Maneuvers", "File Name", "Surface", "Target Speed", "Target Radius", "Stability", "Comfort", "Performance", "Steerability", "Model", "Scenario", "Safety"])
        self.subjective_df.set_index(["Maneuvers"], inplace=True)
        self.subjective_index = []
        for i in range(len(self.subjective_df)):
            self.subjective_index.append(i+1)
