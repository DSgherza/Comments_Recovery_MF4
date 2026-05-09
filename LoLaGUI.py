import tkinter as tk
from GUIComponents import *
from tkinter import *
from tkinter import filedialog as fd
from tkinter import messagebox as mb
import pandas as pd
import threading
from InputManagement import InputManagement
import time
import sys

main_window = tk.Tk()
main_window.geometry('700x300')
main_window.title('MF4 - Comment Recovery')
main_window.iconphoto(False, tk.PhotoImage(file='logo.png'))
save_path = ""
saving_folder = ""

def start_condition():
    start['state'] = DISABLED
    start['bg'] = "gray"
    browse['state'] = DISABLED
    if saving_folder == "":
        mb.showerror("Error", "Please, select a folder for starting elaborations.")
        sys.exit()
    start_time = time.time()
    progress_counter = 0
    progress_bar_list = []
    for file in save_path:
        if file.endswith(".MF4") or file.endswith(".mf4") or file.endswith(".mdf") or file.endswith(".MDF"):
            progress_bar_list.append(file)
    main_window.geometry('700x400')
    start.place(relx = 0.5, rely = 0.75, relheight = 0.2, relwidth = 0.3)
    start_position.place(rely= 0.10)
    browse.place(relheight= 0.11, rely = 0.19)
    display_folder.place(relheight= 0.11, rely = 0.19)
    progress_bar = ttk.Progressbar(main_window, orient = "horizontal", mode = "determinate")
    progress_bar.place(relx = 0.15, rely = 0.37, relheight = 0.1, relwidth = 0.7)
    progress_bar_label = get_label(refernce = main_window, label_text='Calculation in progress: 0%. 0/' + str(len(progress_bar_list)) + " files scanned.", font = ("Allumi Pro", 9),
                         label_relx= 0.49, label_rely= 0.5,
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
    mb.showinfo("Completed", f"All considered files have been elaborated successfully!")
    main_window.quit()
    print((time.time() - start_time)/60)

def browse_button(display_folder):
    display_folder.delete(0, 'end')
    global save_path
    save_path = fd.askopenfilenames()
    global saving_folder
    saving_folder = save_path[0].replace(save_path[0].split("/")[-1], "")
    display_folder.insert(0, saving_folder)

start_position = get_label(refernce = main_window, label_text='Repository:', font = ("Allumi Pro", 16),
                         label_relx= 0.09, label_rely= 0.1,
                         label_relheight= 0.11, label_relwidth= 0.3)
browse = get_button(reference= main_window, command_function = lambda:browse_button(display_folder = display_folder),
                    button_text= 'Browse', font = ("Allumi Pro", 16, "bold"),
                    button_relx=0.9, button_rely=0.25, button_relheight= 0.15, button_relwidth= 0.15, 
                    button_bg= '#D3D3D3', button_fg= '#000000')
display_folder = get_entry(reference = main_window, entry_width= 70, entry_relx= 0.41, entry_rely= 0.25,
                         entry_relheight= 0.15,
                         entry_initial_path= "", font = font.Font(family="Allumi Pro", size = 11))
start = get_button(reference= main_window,
                    command_function= lambda: threading.Thread(target=start_condition).start(),
                    button_text= 'START', font = ("Allumi Pro", 20, "bold"),
                    button_relx=0.5, button_rely=0.65, button_relheight= 0.3, button_relwidth= 0.3, 
                    button_bg= '#0B8227', button_fg= '#FFFFFF')

main_window.mainloop()