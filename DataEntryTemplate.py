import os
import copy
import pandas as pd
class DataEntryTemplate():
    def __init__(self, database, cb, link, output_file_name):
        df = copy.copy(database)
        metadata_file = open(os.getcwd() + r"\template_data_entry.txt", "r")
        self.database_formatting(df)
        if cb.get() == 1:
            data_entry_file = open(link + ("\\") + link.split("\\")[-1] + "_brake_psmec.txt", "w")
            df.to_csv(link + ("\\") + link.split("\\")[-1] + "_database.txt", index = False)
            database_file = open(link + ("\\") + link.split("\\")[-1] + "_database.txt", "r")
            self.data_entry_formatting(data_entry_file, database_file, metadata_file)
            os.remove(link + ("\\") + link.split("\\")[-1] + "_database.txt")
        else:
            data_entry_file = open(output_file_name.replace(output_file_name.split("/")[-1], "") + "\\" + output_file_name.split("/")[-2] + "_brake_psmec.txt", "w")
            df.to_csv(output_file_name.replace(output_file_name.split("/")[-1], "") + "\\" + output_file_name.split("/")[-2] + "_database.txt", index = False)
            database_file = open(output_file_name.replace(output_file_name.split("/")[-1], "") + "\\" + output_file_name.split("/")[-2] + "_database.txt", "r")
            self.data_entry_formatting(data_entry_file, database_file, metadata_file)
            os.remove(output_file_name.replace(output_file_name.split("/")[-1], "") + "\\" + output_file_name.split("/")[-2] + "_database.txt")

    def data_entry_formatting(self, data_entry_file, database_file, metadata):
        data_entry_file.write("brake_data_begin\n")
        j = 0
        for row in metadata:
            if j == 2:
                unit = row
            if j == 3:
                datatype = row
            j += 1
        i = 0
        for row in database_file:
            data_entry_file.write(row)
            if i == 0:
                data_entry_file.write(unit)
                data_entry_file.write(datatype)
                i += 1
        data_entry_file.write("brake_data_end")
        database_file.close()
        data_entry_file.close()
        metadata.close()

    def database_formatting(self, database):
        database.reset_index(inplace = True)
        metadata_2 = pd.read_excel(os.getcwd() + r"\data_entry_template.xlsx")
        database.columns = list(metadata_2["DataEntry Name"])
        for column in database:
            if column != "Maneuver" and column != "PedalApply_Type" and column != "FileSource" and column != "Surface":
                for i in range(len(database[column])):
                    if type(database[column][i]) == str and database[column][i] != "":
                        database[column][i] = 999999
        

        
    