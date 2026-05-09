import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
import numpy as np
import os

from docxtpl import DocxTemplate, InlineImage
from docxtpl import RichText
import gc

def check_folder(folder_name: str)-> None:
    if not os.path.isdir(folder_name):
        os.makedirs(folder_name)

class WordGenartor():
    def __init__(self, file_name: str, maneuvre, reference_speed, reference_angle, mdf_reading_output, ppa_obj, subjective_value:np.array, report: list, cb):
        self.filename = file_name.split('/')[-1][:-4]
        self.objective_signals = mdf_reading_output.objectives
        self.subjective_signals = mdf_reading_output.subjectives
        self.time_signal = mdf_reading_output.time_resampled
        times = mdf_reading_output.times
        self.maneouvres_done = maneuvre
        self.subjective_value = subjective_value
        self.template_path = os.getcwd() + "\LoLaReportTemplate.docx"
        self.image_path = file_name.removesuffix("/"+file_name.split('/')[-1]) + "/Figures"
        check_folder(self.image_path)
        self.report_sheet = DocxTemplate(self.template_path)

        i = 1
        for manoeuvre in self.maneouvres_done:
            if "ABS" in manoeuvre[0]:
                try:
                    aux = mdf_reading_output.time_resampled[manoeuvre[2][1] + int(0.5*mdf_reading_output.frequency)]
                    span = [manoeuvre[2][0], manoeuvre[2][1] + int(0.5*mdf_reading_output.frequency)]
                except IndexError:
                    span = [manoeuvre[2][0], manoeuvre[2][1]]
            elif "TCS" in manoeuvre[0]:
                try:
                    aux = mdf_reading_output.time_resampled[manoeuvre[2][1] + int(mdf_reading_output.frequency)]
                    span = [manoeuvre[2][0], manoeuvre[2][1] + int(mdf_reading_output.frequency)]
                except IndexError:
                    span = [manoeuvre[2][0], manoeuvre[2][1]]
            else:
                span = manoeuvre[2]
            self.context = {"Maneuver": manoeuvre[0]}
            self.time_scaling(sample_span = span)
            fig, axs = plt.subplots(3, 2)
            fig.set_size_inches(20/2.76, 24/2.98)
            if ("ABS" in manoeuvre[0] or "TCS" in manoeuvre[0]) and manoeuvre[0] != "ABS_LaneChange" and manoeuvre[0] != "ABS_InTurn":
                # Driving inputs plot. It has gas_pedal(t) and brakepedal(t) 
                self.plot_generator(signals_name=[['GasPedalPosition','BrakePedalPosition']], 
                                                    sample_span = span, topics= 'Driving Inputs', ax = axs [0,0], reference_angle = reference_angle,
                                                    y_lim=(0, 120), y_label= ['[mm]'])
            elif "ESC_RampSteer" == manoeuvre[0] or "ESC_Handling" == manoeuvre[0] or "ABS_LaneChange" == manoeuvre[0] or "ESC_LaneChange" == manoeuvre[0]:
                self.plot_generator(signals_name=[['GasPedalPosition','BrakePedalPosition'], ["SteeringAngle_deg"]], 
                                                    sample_span = span, topics= 'Driving Inputs', ax = axs [0,0], reference_angle = reference_angle,
                                                    y_lim=(0, 120), y_label= ['[mm]', "[°]"], y2_lim = (-540, 540))
            else:
                self.plot_generator(signals_name=[['GasPedalPosition','BrakePedalPosition'], ["SteeringAngle_deg"]], 
                                                    sample_span = span, topics= 'Driving Inputs', ax = axs [0,0], reference_angle = reference_angle,
                                                    y_lim=(0, 120), y_label= ['[mm]', "[°]"], y2_lim = (-180, 180))
            speeds = ["WheelSpeed_FL_kmh", "WheelSpeed_FR_kmh", "WheelSpeed_RL_kmh", "WheelSpeed_RR_kmh", reference_speed[i-1] + "_kmh"]
            max_speeds = []
            try:
                for item in speeds:
                    if item in mdf_reading_output.objectives:
                        max_speeds.append(max(mdf_reading_output.objectives[item][manoeuvre[2][0]: manoeuvre[2][1]]))
                speeds = np.array(max_speeds)
                if max(speeds) < 60:
                    speed_lim = 60
                elif max(speeds) < 120:
                    speed_lim = 120
                elif max(speeds) < 180:
                    speed_lim = 180
                else:
                    speed_lim = 250
            except:
                speed_lim = 250
            # Wheel dynaic plot. It has vehicle speed(t), estimated and real, and the speed(t) of the 4 corner
            self.plot_generator(signals_name=[[reference_speed[i-1] + "_kmh", 'WheelSpeed_FL_kmh', 'WheelSpeed_FR_kmh', 'WheelSpeed_RL_kmh','WheelSpeed_RR_kmh']], 
                                                    sample_span = span, topics= 'Speeds', ax = axs [0,1], reference_angle = reference_angle, y_lim = (0, speed_lim), y_label= ['[km/h]'], reference_speed = reference_speed[i-1])
            
            # Acceleration plot. It has Ax(t), Ay(t) and the vectorial sum of both.
            try:
                self.objective_signals.update({'A': np.sqrt((self.objective_signals['Ax'])**2 + (self.objective_signals['Ay'])**2)})
            except KeyError:
                pass
            self.plot_generator(signals_name=[['Ax','Ay','A']], sample_span = span, topics= 'Accelerations', ax = axs [1,0], reference_angle = reference_angle,
                                                    y_lim=(-15, 15),  y_label= ['[m/s^2]'])
            
            check_calc = False
            if "SideSlipAngle_deg" in self.objective_signals or "BSAAngle_deg" in self.objective_signals or "BSEAngle_deg" in self.objective_signals or "BodySlipAngle_deg" in self.objective_signals:
                flag_1 = True
                flag_2 = True
                flag_3 = True
                flag_4 = True
                channels = ["SideSlipAngle", "BSAAngle", "BSEAngle", "BodySlipAngle"]
                flags = [flag_1, flag_2, flag_3, flag_4]
                if "SideSlipAngle_deg" in self.objective_signals:
                    if "SideSlipAngle" in times:
                        if times["SideSlipAngle"][1] < manoeuvre[2][1]:
                            flags[0] = False
                else:
                    flags[0] = False
                if "BSAAngle_deg" in self.objective_signals:
                    if "BSAAngle" in times:
                        if times["BSAAngle"][1] < manoeuvre[2][1]:
                            flags[1] = False
                else:
                    flags[1] = False
                if "BSEAngle_deg" in self.objective_signals:
                    if "BSEAngle" in times:
                        if times["BSEAngle"][1] < manoeuvre[2][1]:
                            flags[2] = False
                else:
                    flags[2] = False
                if "BodySlipAngle_deg" in self.objective_signals:
                    if "BodySlipAngle" in times:
                        if times["BodySlipAngle"][1] < manoeuvre[2][1]:
                            flags[3] = False
                else:
                    flags[3] = False
                for j in range(4):
                    if flags[j]:
                        reference_angle = channels[j]
                        check_calc = True
                        break
            
            if not check_calc:
                reference_angle = "NONE"

            try:
                if ("ABS" in manoeuvre[0] or "TCS" in manoeuvre[0]) and manoeuvre[0] != "ABS_LaneChange" and manoeuvre[0] != "ABS_InTurn" and ("ABS_Braking" != manoeuvre[0] and abs(self.objective_signals["Effective_Yaw_degs"][i-1][0]) < 3):
                #Lateral dynamics. It has SteeringAngle(t), YawRate(t), SideslipAngle(t)
                    axs[1,1].yaxis.set_major_locator(ticker.MultipleLocator(2))
                    self.plot_generator_yaw(signals_name=[['Effective_Yaw_degs', 'Theorical_Yaw_degs']], cont = i,
                                                    topics= 'Lateral Dynamic', ax = axs [1,1], reference_angle = reference_angle,
                                                    y_lim=(-10, 10), y_label= ['[°/s]'])
                else:
                #Lateral dynamics. It has SteeringAngle(t), YawRate(t), SideslipAngle(t)
                    try:
                        signal_data = self.objective_signals["Theorical_Yaw_degs"][i-1]
                        y_lim = self.set_dynamic_yaw_axis(axs[1,1], signal_data)
                    except:
                        y_lim = 20
                    self.plot_generator_yaw(signals_name=[['Effective_Yaw_degs', 'Theorical_Yaw_degs']], cont = i,
                                                    topics= 'Lateral Dynamic', ax = axs [1,1], reference_angle = reference_angle,
                                                    y_lim = y_lim, y_label= ['[°/s]'])
            except:
                axs[1,1].yaxis.set_major_locator(ticker.MultipleLocator(2))
                self.plot_generator_yaw(signals_name=[[]], cont = i,
                                                    topics= 'Lateral Dynamic', ax = axs [1,1], reference_angle = reference_angle,
                                                    y_lim=(-10, 10), y_label= ['[°/s]'])
            # Force feedback(t) plot
            self.plot_generator(signals_name=[['ForceFeedback_FL', 'ForceFeedback_FR', 'ForceFeedback_RL','ForceFeedback_RR']], 
                                                    sample_span = span, topics= 'Actuator Control', ax = axs [2,0], reference_angle = reference_angle,
                                                    y_lim=(0, 50), y_label= ['[kN]'])
            
            # Torque(t), engine and braking 
            self.plot_generator(signals_name=[['EngineTorque_FA', 'EngineTorque_RA']],
                                                    sample_span = span, topics= 'Torques', ax = axs[2,1], reference_angle = reference_angle,
                                                    y_lim=(-5, 5), y_label= ['[kNm]'])
            
            figure_name = self.filename + '_' + str(i) + '.png'
            fig.tight_layout()
            plt.savefig(self.image_path + '/' + figure_name, bbox_inches='tight')
            plt.close() 
            gc.collect()
            self.template_fill("Subplots", figure_name= figure_name)


            # Fill the subjective table
            self.table_fill(ppa_obj, i)
            self.context.update({"Comment": mdf_reading_output.comment})
            self.context.update({"Vehicle": mdf_reading_output.vehicle})
            self.context.update({"Date": mdf_reading_output.date})
            self.context.update({"Weight": mdf_reading_output.weight})
            self.context.update({"FrontTires": mdf_reading_output.front_tires})
            self.context.update({"RearTires": mdf_reading_output.rear_tires})
            rt = RichText()
            self.context.update({"File": rt})
            rt.add(mdf_reading_output.log,url_id=self.report_sheet.build_url_id(mdf_reading_output.link), font = "Allumi Pro", size = 14, underline = True, bold = False)
            if "ESC" in manoeuvre[0] and manoeuvre[0] != "ESC_PartialBrkinTurn" and manoeuvre[0] != "ESC_Handling":
                self.context.update({"Time": round(mdf_reading_output.time_resampled[manoeuvre[3][0]], 2)})
            else:
                self.context.update({"Time": round(mdf_reading_output.time_resampled[manoeuvre[2][0]], 2)})
            # Save the report document as word file
            self.report_sheet.render(self.context)
            if "/" == self.image_path[0]:
                self.report_repository_name = r"\\brembo.org\fs-ita\Progetti\Advanced_R&D_Archive\SENSIFY_RT\Processing" + "/" + manoeuvre[0]
                check_folder(self.report_repository_name)
                self.report_sheet.save(self.report_repository_name + '/' + self.filename + '_' + str(i) + '.docx')
                report.append(self.report_repository_name + '/' + self.filename + '_' + str(i) + '.docx')
            if cb.get() == 1:
                self.report_repository_name = r"\\brembo.org\fs-ita\Progetti\Advanced_R&D_Archive\SENSIFY_RT\Processing" + "/" + manoeuvre[0]
                check_folder(self.report_repository_name)
                self.report_sheet.save(self.report_repository_name + '/' + self.filename + '_' + str(i) + '.docx')
                self.report_sheet.save(self.image_path + '/' + self.filename + '_' + str(i) + '.docx')
                report.append(self.report_repository_name + '/' + self.filename + '_' + str(i) + '.docx')
            else:
                if "/" != self.image_path[0]:
                    self.report_sheet.save(self.image_path + '/' + self.filename + '_' + str(i) + '.docx')
                    report.append(self.image_path + '/' + self.filename + '_' + str(i) + '.docx')
            i += 1

    def table_fill(self, ppa_obj, i: int) -> None:
        self.context.update({"Com":self.subjective_value[i-1][5], "Perfo": self.subjective_value[i-1][6], "Stab": self.subjective_value[i-1][4], "Steer": self.subjective_value[i-1][7]})
        try:
            self.context.update({"Speed": int(ppa_obj.v_nominal[i-1])})
        except ValueError:
            self.context.update({"Speed": ppa_obj.v_nominal[i-1]})
        self.context.update({"Metric1": ppa_obj.metric1[i-1]})
        self.context.update({"Metric2": ppa_obj.metric2[i-1]})
        self.context.update({"Metric3": ppa_obj.metric3[i-1]})
        self.context.update({"Metric4": ppa_obj.metric4[i-1]})
        self.context.update({"Metric5": ppa_obj.metric5[i-1]})
        self.context.update({"Metric6": ppa_obj.metric6[i-1]})
        self.context.update({"Name1": ppa_obj.name1[i-1]})
        self.context.update({"Name2": ppa_obj.name2[i-1]})
        self.context.update({"Name3": ppa_obj.name3[i-1]})
        self.context.update({"Name4": ppa_obj.name4[i-1]})
        self.context.update({"Name5": ppa_obj.name5[i-1]})
        self.context.update({"Name6": ppa_obj.name6[i-1]})



    def set_dynamic_yaw_axis(self, ax, signal):
        """
    Imposta dinamicamente i limiti dell'asse Y e la spaziatura dei tick principali
    in base al segnale 'Theorical_Yaw_degs'.
    """
        max_val = max(abs(val) for val in signal)
        upper_limit = 10
        while 0.9 * upper_limit < max_val:
            upper_limit += 10
        y_lim = (-upper_limit, upper_limit)
        tick_spacing = upper_limit / 5

        ax.set_ylim(y_lim)
        ax.yaxis.set_major_locator(ticker.MultipleLocator(tick_spacing))
        return y_lim



    def template_fill(self, topics, figure_name)->None:

        # Word document filling
        self.context.update({topics: InlineImage(self.report_sheet, self.image_path + '/' + figure_name)})
        

    def time_scaling(self, sample_span: list) -> None: 
        """
        We plot the time intervall between predefined time intervall. 
        The time intervall range is by multiple of 5 seconds eg [5, 10, 20, ...]
        the manoeuvre will start at the time 0.5. It meneas the time history for the manoeuvre 
        until 4.5 s will we plot wit a 5 s time history.
        """   
        duration = self.time_signal[sample_span[1]] - self.time_signal[(sample_span[0])]
        self.length_x_axis = (duration//4 + 1)*4
        self.x_axis = np.linspace(0, duration, (sample_span[1] - (sample_span[0]- round(0.5/(self.time_signal[1] - self.time_signal[0]))))) 


    def pad_array_to_match(self, x_axis, sample_span):
        """
        Pads the sample_span array with np.nan values at the end to match the length of x_axis.
    
    Parameters:
    x_axis (array-like): Reference array for target length.
    sample_span (array-like): Array to be padded.
    
    Returns:
    np.ndarray: Padded sample_span array.
    """
        x_len = len(x_axis)
        s_len = len(sample_span)
    
        if s_len < x_len:
            padding = np.full(x_len - s_len, np.nan)
            sample_span_padded = np.concatenate([sample_span, padding])
        else:
            sample_span_padded = np.array(sample_span)
    
        return sample_span_padded


    def get_plot(self, signal:str, axis, sample_span, reference_angle, reference_speed = None): 
        try:
            lines = self.get_color(signal_name= signal, axis = axis, x_axis = self.x_axis,
                                    sample_span=self.objective_signals[signal][(sample_span[0]- round(0.5/(self.time_signal[1] - self.time_signal[0]))):sample_span[1]], reference_angle = reference_angle, reference_speed = reference_speed)
        except KeyError:
            lines = None
        except IndexError:
            lines = None
        return lines 
    
    def get_plot_yaw(self, signal:str, axis, cont, reference_angle, reference_speed = None): 
        try:
            sample_span_padded = self.pad_array_to_match(self.x_axis, self.objective_signals[signal][cont-1])
            lines = self.get_color(signal_name= signal, axis = axis, x_axis = self.x_axis,
                                    sample_span=sample_span_padded, reference_angle = reference_angle, reference_speed = reference_speed)
        except KeyError:
            lines = None
        except IndexError:
            lines = None
        return lines

    def plot_generator(self, signals_name: list, sample_span: list, topics: str, ax, reference_angle, y_lim: tuple = None, y_label: list= None, y2_lim: tuple = None, reference_speed = None) -> None:

        signals_list = [[], []]

        ax.set_xlim(0, self.length_x_axis)
        if max(self.x_axis) < 20:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,1))
        elif max(self.x_axis) < 60:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,5))
        else:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,10))
        ax.xaxis.set_tick_params(labelsize = 6)
        ax.xaxis.label.set_fontsize(6)
        ax.set_xlabel('Time [s]')
        ax.set_title(topics, loc = "center", fontweight = "bold", fontsize = 7)

        if y_lim != None:
            ax.set_ylim(y_lim)
        ax.set_ylabel(y_label[0])
        ax.yaxis.label.set_fontsize(6)
        ax.yaxis.label.set_size(6)
        ax.yaxis.set_tick_params(labelsize=6)

        if len(y_label)>1:
            ax2= ax.twinx()
            ax.set_ylabel(y_label[0])
            ax2.set_ylabel(y_label[1])
            ax2.set_ylim(y2_lim)
            ax2.yaxis.set_tick_params(labelsize=6)
            ax2.yaxis.label.set_size(6)
        
        else:
            ax.set_ylabel(y_label[0])

        if len(y_label)>1 and "BrakePedalPosition" in signals_name[0]:
            ax.set_yticks(np.arange(0, 121, 20))
            if y2_lim == (-90, 90):
                ax2.set_yticks(np.arange(-90, 91, 30))
            elif y2_lim == (-540, 540):
                ax2.set_yticks(np.arange(-540, 541, 180))
            else:
                ax2.set_yticks(np.arange(-180, 181, 60))

        for signal in signals_name[0]:
            lines = self.get_plot( signal, ax, sample_span, reference_angle = reference_angle, reference_speed = reference_speed)
            try:
                signals_list[0].append(lines[0])
            except TypeError:
                pass
        
        if len(signals_name)>1:
            for signal in signals_name[1]:
                lines = self.get_plot( signal, ax2, sample_span, reference_angle = reference_angle, reference_speed = reference_speed)
                try:
                    signals_list[1].append(lines[0])
                except TypeError:
                    pass

        if len(y_label)>1:
            ax2.yaxis.set_tick_params(labelsize=6)
            ax2.yaxis.label.set_fontsize(6)

        labs = [[], []]
        for l in signals_list:
            if l == signals_list[0]:
                for lab in l:
                    if lab.get_label() == "ReferenceSpeed_kmh":
                        labs[0].append("ExternalSpeed_kmh")     
                    else:
                        labs[0].append(lab.get_label())
            else:
                for lab in l:
                    if lab.get_label() == "ReferenceSpeed_kmh":
                        labs[1].append("ExternalSpeed_kmh")
                    else:
                        labs[1].append(lab.get_label())

        ax.legend(signals_list[0], labs[0], loc='upper right', fontsize = 4.5)
        if len(y_label)>1:
            ax.legend(signals_list[0], labs[0], loc='upper left', fontsize = 4.5)
            ax2.legend(signals_list[1], labs[1], loc='upper right', fontsize = 4.5)

        if len(y_label) == 1 and "EngineTorque_FA" in signals_name[0]:
            ax.set_yticks(np.arange(-5, 6, 1))

    def plot_generator_yaw(self, signals_name: list, cont, topics: str, ax, reference_angle, y_lim: tuple = None, y_label: list= None, y2_lim: tuple = None, reference_speed = None) -> None:

        signals_list = [[]]

        ax.set_xlim(0, self.length_x_axis)
        if max(self.x_axis) < 20:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,1))
        elif max(self.x_axis) < 60:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,5))
        else:
            ax.set_xticks(np.arange(0, self.length_x_axis + 1,10))
        ax.xaxis.set_tick_params(labelsize = 6)
        ax.xaxis.label.set_fontsize(6)
        ax.set_xlabel('Time [s]')
        ax.set_title(topics, loc = "center", fontweight = "bold", fontsize = 7)

        if y_lim != None:
            ax.set_ylim(y_lim)
        ax.set_ylabel(y_label[0])
        ax.yaxis.label.set_fontsize(6)
        ax.yaxis.label.set_size(6)
        ax.yaxis.set_tick_params(labelsize=6)

        for signal in signals_name[0]:
            lines = self.get_plot_yaw(signal, ax, cont, reference_angle = reference_angle, reference_speed = reference_speed)
            try:
                signals_list[0].append(lines[0])
            except TypeError:
                pass

        labs = [[]]
        for l in signals_list:
            for lab in l:
                labs[0].append(lab.get_label())

        ax.legend(signals_list[0], labs[0], loc='upper right', fontsize = 4.5)

    @staticmethod
    def get_color(signal_name:str, axis, x_axis, sample_span, reference_angle, reference_speed = None):
        try:
            if "_FL" in signal_name or signal_name == "BrakePedalPosition":
                lines = axis.plot(x_axis, sample_span, 'red', label=signal_name)
            elif "_FR" in signal_name or signal_name == "GasPedalPosition":
                lines = axis.plot(x_axis, sample_span, 'green', label=signal_name)
            elif signal_name == "Ax":
                lines = axis.plot(x_axis, sample_span, 'dimgray', label=signal_name)
            elif signal_name == "Theorical_Yaw_degs" or signal_name == "A":
                lines = axis.plot(x_axis, sample_span, 'dimgray', label=signal_name, ls = "--", lw = 0.7)
            elif "_RL" in signal_name:
                lines = axis.plot(x_axis, sample_span, 'gold', label=signal_name)
            elif "_RR" in signal_name or signal_name == "SteeringAngle_deg":
                lines = axis.plot(x_axis, sample_span, "blue", label=signal_name)
            elif signal_name == reference_angle + "_deg" or (reference_speed != None and signal_name == reference_speed + "_kmh"):
                lines = axis.plot(x_axis, sample_span, "deeppink", label=signal_name)
            elif signal_name == "EngineTorque_RA" or signal_name == "Ay"  or signal_name == "Effective_Yaw_degs":
                lines = axis.plot(x_axis, sample_span, "black", label=signal_name)
            elif signal_name == "EngineTorque_FA":
                lines = axis.plot(x_axis, sample_span, "gray", label=signal_name)
        except ValueError:
            lines = None
        return lines