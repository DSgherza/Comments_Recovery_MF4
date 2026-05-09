class FlagDetection():
    def flag_detector(self, signals_list, start, end):
        flag = 0
        for item in signals_list:
            for i in range(len(item[start:end])):
                if item[i+start] == 1:
                    flag = 1
                    break
            if flag == 1:
                break
        return flag
