import tkinter as tk
from tkinter import ttk
from tkinter import font

def get_label(refernce, label_text, font, label_relx, label_rely,
               label_relheight, label_relwidth):
     my_label = tk.Label(refernce, text= label_text, font=font)
     my_label.place(relx= label_relx, rely= label_rely, anchor= "center",
                         relheight= label_relheight, relwidth= label_relwidth)
     return my_label

def get_button(reference, command_function, button_text, font,
                   button_relx, button_rely, button_relheight, button_relwidth, 
                   button_bg, button_fg):
     my_button = tk.Button(master= reference , command= command_function,
                         text= button_text, font= font, bg= button_bg, fg= button_fg,
                         relief='groove', border = 2, borderwidth = 2)
     my_button.place(relx=button_relx, rely= button_rely, anchor= "center",
                    relheight= button_relheight, relwidth= button_relwidth)
     return my_button

def get_entry(reference, entry_width, entry_relx, entry_rely,
               entry_relheight, entry_initial_path, font):
     my_entry = tk.Entry(reference,width= entry_width, font = font)
     my_entry.place(relx= entry_relx, rely= entry_rely, anchor= "center",
                         relheight= entry_relheight)
     my_entry.insert(0, entry_initial_path)
     return my_entry

def get_combobox(reference, combo_text, combo_width, combo_relx, combo_rely):
     my_combobox= ttk.Combobox(reference, textvariable= combo_text, width=combo_width)
     my_combobox.place(relx= combo_relx, rely= combo_rely, anchor="center")
     return my_combobox

