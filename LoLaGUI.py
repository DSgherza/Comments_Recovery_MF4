import tkinter as tk
from GUIComponents import *
from tkinter import *
from tkinter import Checkbutton as CB
from tkinter import filedialog as fd
from tkinter import messagebox as mb
import pandas as pd
import os
import threading
from InputManagement import InputManagement
import time
import sys

main_window = tk.Tk()
main_window.geometry('700x400')
main_window.title('LoLa - Longitudinal and Lateral analysis')
main_window.iconphoto(False, tk.PhotoImage(file='logo.png'))
save_path = ""
save_server_folder = ""
saving_folder = ""

def metrics_filler(ppa_obj):
    ppa_obj.name1 = []
    ppa_obj.name2 = []
    ppa_obj.name3 = []
    ppa_obj.name4 = []
    ppa_obj.name5 = []
    ppa_obj.name6 = []
    ppa_obj.metric1 = []
    ppa_obj.metric2 = []
    ppa_obj.metric3 = []
    ppa_obj.metric4 = []
    ppa_obj.metric5 = []
    ppa_obj.metric6 = []
    names = [ppa_obj.name1, ppa_obj.name2, ppa_obj.name3, ppa_obj.name4, ppa_obj.name5, ppa_obj.name6]
    metrics = [ppa_obj.metric1, ppa_obj.metric2, ppa_obj.metric3, ppa_obj.metric4, ppa_obj.metric5, ppa_obj.metric6]
    parameters_df = ppa_obj.parameters_df.T
    for i in range(len(parameters_df)):
        if "TCS" in parameters_df.index[i]:
            tcs_names = ["Launch Time 0-15\n [s]", "Launch Time 0-50\n [s]", "Ax Avg\n [m/s^2]", "Delta YawRate\n [°/s]", "YawRate RMS\n [°/s]", "SWA Max\n [°]"]
            tcs_metrics = ["launch_time_0_15kph", "launch_time_0_50kph", "Ax_avg", "Delta_Yaw_Max", "Yaw_RMS", "SWA_Peak (vs SWA @DrivingInput)"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ABS_PositiveMuJump", "ABS_PositiveMuSplitJump", "ABS_NegativeMuJump", "ABS_NegativeMuSplitJump"]:
            tcs_names = ["SV norm\n [m]", "MFDD\n [m/s^2]", "Dec Peak\n [m/s^2]", "Delta YawRate\n [°/s]", "YawRate RMS\n [°/s]", "SWA Max\n [°]"]
            tcs_metrics = ["SV_norm", "MFDD", "dec_peak", "Delta_Yaw_Max", "Yaw_RMS", "SWA_Peak (vs SWA @DrivingInput)"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ABS_StoppingDistance", "ABS_MuSplit"]:
            tcs_names = ["SV norm\n [m]", "MFDD\n [m/s^2]", "DeltaDec MFDD Min\n [m/s^2]", "Delta YawRate\n [°/s]", "YawRate RMS\n [°/s]", "SWA Max\n [°]"]
            tcs_metrics = ["SV_norm", "MFDD", "Delta_dec_MFDD_Min", "Delta_Yaw_Max", "Yaw_RMS", "SWA_Peak (vs SWA @DrivingInput)"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ABS_InTurn"]:
            tcs_names = ["SV norm\n [m]", "MFDD\n [m/s^2]", "DeltaDec MFDD Min\n [m/s^2]", "Beta Max\n [°]", "YawRate Max Overshoot\n [°/s]", ""]
            tcs_metrics = ["SV_norm", "MFDD", "Delta_dec_MFDD_Min", "Max_BSA", "YawRate_Max_Overshoot (+sx)", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ABS_LaneChange"]:
            tcs_names = ["SV norm\n [m]", "MFDD\n [m/s^2]", "DeltaDec MFDD Min\n [m/s^2]", "Beta Max\n [°]", "", ""]
            tcs_metrics = ["SV_norm", "MFDD", "Delta_dec_MFDD_Min", "Max_BSA", "", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ESC_LaneChange", "ESC_Slalom"]:
            tcs_names = ["Beta Max\n [°]", "Ay Max\n [m/s^2]", "Dec Peak\n [m/s^2]", "Entry Speed\n [km/h]", "Exit Speed\n [km/h]", "SWR Max\n [°/s]"]
            tcs_metrics = ["Max_BSA", "Ay_Max_Overshoot (+sx)", "dec_peak", "VehicleSpeed@DrivingInput", "VehicleSpeed@End", "SWA_spd_Peak"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ESC_StepSteer"]:
            tcs_names = ["Beta Max\n [°]", "Ay Max\n [m/s^2]", "Dec Peak\n [m/s^2]", "YawRate RMS\n [°/s]", "", "SWR Max\n [°/s]"]
            tcs_metrics = ["Max_BSA", "Ay_Max_Overshoot (+sx)", "dec_peak", "Yaw_RMS", "", "SWA_spd_Peak"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ESC_RampSteer", "ESC_ConstantRadius"]:
            tcs_names = ["Beta Max\n [°]", "Ay Max\n [m/s^2]", "Dec Peak\n [m/s^2]", "YawRate RMS\n [°/s]", "", ""]
            tcs_metrics = ["Max_BSA", "Ay_Max_Overshoot (+sx)", "dec_peak", "Yaw_RMS", "", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ESC_PowerOninTurn", "ESC_PowerOffinTurn"]:
            tcs_names = ["Beta Max\n [°]", "Ay Max\n [m/s^2]", "Dec Peak\n [m/s^2]", "YawRate Max Overshoot\n [°/s]", "", ""]
            tcs_metrics = ["Max_BSA", "Ay_Max_Overshoot (+sx)", "dec_peak", "YawRate_Max_Overshoot (+sx)", "", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] in ["ESC_PartialBrkinTurn"]:
            tcs_names = ["Beta Max\n [°]", "Ay Max\n [m/s^2]", "Dec Peak\n [m/s^2]", "YawRate Max Overshoot\n [°/s]", "Ax Avg\n[m/s^2]", ""]
            tcs_metrics = ["Max_BSA", "Ay_Max_Overshoot (+sx)", "dec_peak", "YawRate_Max_Overshoot (+sx)", "Ax_avg", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        elif parameters_df.index[i] == "ABS_Braking":
            tcs_names = ["SV norm\n [m]", "MFDD\n [m/s^2]", "DeltaDec MFDD Min\n [m/s^2]", "Delta YawRate\n [°/s]", "YawRate RMS\n [°/s]", "SWA Max\n [°]"]
            tcs_metrics = ["SV_norm", "MFDD", "Delta_dec_MFDD_Min", "Delta_Yaw_Max", "Yaw_RMS", "SWA_Peak (vs SWA @DrivingInput)"]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")
        else:
            tcs_names = ["Beta Max\n[°]", "Average Speed\n [m/s]", "", "", "", ""]
            tcs_metrics = ["Max_BSA", "Speed Avg", "", "", "", ""]
            for j in range(len(names)):
                if tcs_names[j] != "":
                    names[j].append(tcs_names[j])
                    metrics[j].append(parameters_df[tcs_metrics[j]][i])
                else:
                    names[j].append("")
                    metrics[j].append("")

def dataframe_reindexing(df, new_indexes):
    df.reset_index(names = "Maneuver", inplace = True)
    indexes_list = []
    for i in range(len(new_indexes)):
        for j in range(len(new_indexes[i])):
            indexes_list.append(new_indexes[i][j])
    df.set_index([indexes_list], inplace=True)

def start_condition():
    start['state'] = DISABLED
    start['bg'] = "gray"
    browse['state'] = DISABLED
    browse_2['state'] = DISABLED
    global save_server_folder
    if cb.get() == 1 and (saving_folder == "" and save_server_folder != ""):
        mb.showerror("Error", "Please, select a folder for starting local elaborations.")
        sys.exit()
    elif cb.get() == 1 and (saving_folder == "" and save_server_folder == ""):
        mb.showerror("Error", "Please, select a folder for starting local and server elaborations.")
        sys.exit()
    elif cb.get() == 1 and (saving_folder != "" and save_server_folder == ""):
        save_server_folder = server.get()
        if save_server_folder != "":
            if os.path.isdir(save_server_folder):
                pass
            else:
                mb.showerror("Error", "Please, select a valid folder for server elaborations.")
                sys.exit()
        else:
            mb.showerror("Error", "Please, select a folder for server elaborations.")
            sys.exit()
    if cb.get() == 0 and saving_folder == "":
        mb.showerror("Error", "Please, select a folder for starting elaborations.")
        sys.exit()
    start_time = time.time()
    progress_counter = 0
    progress_bar_list = []
    for file in save_path:
        if file.endswith(".MF4") or file.endswith(".mf4") or file.endswith(".mdf") or file.endswith(".MDF"):
            progress_bar_list.append(file)
    main_window.geometry('700x500')
    start.place(relx = 0.27, rely = 0.85, relheight = 0.16, relwidth = 0.3)
    start_position.place(rely= 0.10)
    browse.place(relheight= 0.09, rely = 0.19)
    display_folder.place(relheight= 0.09, rely = 0.19)
    server.place(relheight= 0.09, rely = 0.43)
    browse_2.place(relheight= 0.09, rely = 0.43)
    checkbox.place(relx=0.65, rely=0.75)
    let_frame.place(relx=0.77, rely=0.82, relheight = 0.157, relwidth = 0.21)
    export_frame.place(relx=0.52, rely=0.82, relheight = 0.157, relwidth = 0.2)
    server_position.place(rely= 0.34, relheight= 0.09)
    progress_bar = ttk.Progressbar(main_window, orient = "horizontal", mode = "determinate")
    progress_bar.place(relx = 0.15, rely = 0.57, relheight = 0.08, relwidth = 0.7)
    progress_bar_label = get_label(refernce = main_window, label_text='Calculation in progress: 0%. 0/' + str(len(progress_bar_list)) + " files scanned.", font = ("Allumi Pro", 9),
                         label_relx= 0.49, label_rely= 0.68,
                         label_relheight= 0.05, label_relwidth= 0.55)
    progress_bar["value"] = 0
    filename_list = []
    comments_list = []
    for file in save_path:
        if progress_counter != 0:
            if file.endswith(".MF4") or file.endswith(".mf4") or file.endswith(".mdf") or file.endswith(".MDF"):
                progress_bar["value"] += 1/len(progress_bar_list)*100
                progress_bar_label.config(text=f"Calculation in progress: {int(round(progress_bar['value']))}%. {progress_counter}/{len(progress_bar_list)} files scanned.")
        if file.endswith(".MF4") or file.endswith(".mf4") or file.endswith(".mdf") or file.endswith(".MDF"):
            progress_counter += 1
        if file.endswith(".MF4") or file.endswith(".mf4") or file.endswith(".mdf") or file.endswith(".MDF"):
            dictionaries = InputManagement(file)
            filename_list.append(dictionaries.log)
            comments_list.append(dictionaries.comment) 
    df = pd.DataFrame({"FileName": filename_list, "Comment": comments_list})
    df.to_excel(saving_folder + "Comments.xlsx", index = False)
    progress_bar["value"] += 1/len(progress_bar_list)*100
    progress_bar_label.config(text = f"Calculation in progress: {int(round(progress_bar['value']))}%. {progress_counter}/{len(progress_bar_list)} files scanned.")
    progress_bar_label.config(text = f"{int(round(progress_bar['value']))}%. {progress_counter}/{len(progress_bar_list)} files scanned. Wait...output elaboration in progress.")
    main_window.quit()
    print((time.time() - start_time)/60)

def browse_button(display_folder):
    display_folder.delete(0, 'end')
    global save_path
    save_path = fd.askopenfilenames()
    global saving_folder
    saving_folder = save_path[0].replace(save_path[0].split("/")[-1], "")
    display_folder.insert(0, saving_folder)

def browse_button_2(server, initial_dir):
    server.delete(0, 'end')
    global save_server_folder
    save_server_folder = fd.askdirectory(initialdir = initial_dir)
    server.insert(0, save_server_folder)

def ODE():
    global cb
    if ode_val.get() == 1:
        server['state'] = DISABLED
        browse_2['state'] = DISABLED
        cb.set(0)
        export_frame.config(foreground = "#000000")
        let_val.set(0)
        ode.config(foreground = "#000000")
        checkbox['state'] = DISABLED
        let_frame.config(foreground = "#969696")
        let.config(foreground = "#969696")
        frequency_value_let.set("MAX")
        frequency_combobox_let["state"] = DISABLED
        frequency_combobox["state"] = "readonly"
        start_position['text'] = "Files Repository:"
        server_position['text'] = ""
    else:
        server['state'] = NORMAL
        frequency_value.set("MAX")
        ode.config(foreground = "#969696")
        export_frame.config(foreground = "#969696")
        frequency_combobox["state"] = DISABLED
        browse_2['state'] = DISABLED
        server['state'] = DISABLED
        checkbox['state'] = NORMAL
        start_position['text'] = "Local Repository:"
        server_position['text'] = ""

def LET():
    if let_val.get() == 1:
        ode_val.set(0)
        let_frame.config(foreground = "#000000")
        let.config(foreground = "#000000")
        export_frame.config(foreground = "#969696")
        ode.config(foreground = "#969696")
        frequency_value.set("MAX")
        checkbox['state'] = NORMAL
        frequency_combobox_let["state"] = "readonly"
        frequency_combobox["state"] = DISABLED
    else:
        let_frame.config(foreground = "#969696")
        frequency_value_let.set("MAX")
        let.config(foreground = "#969696")
        frequency_combobox_let["state"] = DISABLED

export_frame = tk.LabelFrame(main_window, text = "OtE - (Only .txt Export)", foreground = "#969696", font = ("Allumi Pro", 9))
export_frame.place(relx=0.5, rely=0.75, relheight = 0.22, relwidth = 0.2)
ode_val = IntVar(value = 0)
ode = CB(export_frame, text = "Enable OtE Mode", font = ("Allumi Pro", 9), variable = ode_val, onvalue = 1, offvalue = 0, command = ODE, foreground = "#969696")
ode.place(relx=0.05, rely=0.05)
frequency_value = StringVar()
frequency_combobox = ttk.Combobox(export_frame, textvariable = frequency_value, font = ("Allumi Pro", 9))
frequency_combobox["values"] = ("5", "10", "20", "50", "100", "200", "MAX")
frequency_value.set("MAX")
frequency_combobox.set("MAX")
frequency_combobox.place(relx=0.07, rely=0.55, relwidth = 0.5)
frequency_combobox["state"] = DISABLED

let_frame = tk.LabelFrame(main_window, text = "LEt - (LoLa & Export .txt)", foreground = "#969696", font = ("Allumi Pro", 9))
let_frame.place(relx=0.75, rely=0.75, relheight = 0.22, relwidth = 0.21)
let_val = IntVar(value = 0)
let = CB(let_frame, text = "Enable LEt Mode", font = ("Allumi Pro", 9), variable = let_val, onvalue = 1, offvalue = 0, command = LET, foreground = "#969696")
let.place(relx=0.05, rely=0.05)
frequency_value_let = StringVar()
frequency_combobox_let = ttk.Combobox(let_frame, font = ("Allumi Pro", 9), textvariable = frequency_value_let)
frequency_combobox_let["values"] = ("5", "10", "20", "50", "100", "200", "MAX")
frequency_value_let.set("MAX")
frequency_combobox_let.set("MAX")
frequency_combobox_let.place(relx=0.07, rely=0.55, relwidth = 0.5)
frequency_combobox_let["state"] = DISABLED

start_position = get_label(refernce = main_window, label_text='Local Repository:', font = ("Allumi Pro", 16),
                         label_relx= 0.13, label_rely= 0.1,
                         label_relheight= 0.11, label_relwidth= 0.3)
browse = get_button(reference= main_window, command_function = lambda:browse_button(display_folder = display_folder),
                    button_text= 'Browse', font = ("Allumi Pro", 16, "bold"),
                    button_relx=0.9, button_rely=0.2, button_relheight= 0.11, button_relwidth= 0.15, 
                    button_bg= '#D3D3D3', button_fg= '#000000')
display_folder = get_entry(reference = main_window, entry_width= 70, entry_relx= 0.41, entry_rely= 0.2,
                         entry_relheight= 0.11,
                         entry_initial_path= "", font = font.Font(family="Allumi Pro", size = 11))
start = get_button(reference= main_window,
                    command_function= lambda: threading.Thread(target=start_condition).start(),
                    button_text= 'START', font = ("Allumi Pro", 20, "bold"),
                    button_relx=0.24, button_rely=0.81, button_relheight= 0.2, button_relwidth= 0.3, 
                    button_bg= '#0B8227', button_fg= '#FFFFFF')

def isChecked():
    if cb.get() == 1:
        server['state'] = NORMAL
        browse_2['state'] = NORMAL
        checkbox.config(foreground = "#000000")
        start_position['text'] = "Local Repository:"
        server_position['text'] = "Server Repository:"
    elif cb.get() == 0:
        checkbox.config(foreground = "#969696")
        server['state'] = DISABLED
        browse_2['state'] = DISABLED
        start_position['text'] = "Files Repository:"
        server_position['text'] = ""

cb = IntVar(value = 1)
checkbox = CB(main_window, text = "Local&Server Use", variable = cb, onvalue = 1, offvalue = 0, command = isChecked, font = ("Allumi Pro", 9))
checkbox.place(relx=0.63, rely=0.65)
server = get_entry(reference = main_window, entry_width = 70, entry_relx = 0.41, entry_rely = 0.49,
                         entry_relheight = 0.11,
                         entry_initial_path = "", font = font.Font(family="Allumi Pro", size = 11))
browse_2 = get_button(reference = main_window, command_function = lambda:browse_button_2(server = server, initial_dir = r'\\brembo.org\FS-ITA\Progetti\Advanced_R&D_Archive'),
                    button_text = 'Browse', font = ("Allumi Pro", 16, "bold"),
                    button_relx = 0.9, button_rely = 0.49, button_relheight = 0.11, button_relwidth = 0.15, 
                    button_bg = '#D3D3D3', button_fg = '#000000')
server_position = get_label(refernce = main_window, label_text = 'Server Repository:', font = ("Allumi Pro", 16),
                         label_relx = 0.14, label_rely = 0.38,
                         label_relheight = 0.11, label_relwidth = 0.3)

main_window.mainloop()