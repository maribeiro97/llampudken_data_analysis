import os 
import sys
import numpy as np
import plotly.graph_objects as go
import plotly.io as pio
import datetime
from OSC_CALIBRATIONS import get_osc_config
from scipy.signal import savgol_filter
from scipy.integrate import cumulative_trapezoid

class OscilloscopeReader():
    OSC_DATA_PATH = 'osc_data'
    def __init__(self):
        self.noise_len = 10 ** 3
        self.fig = go.Figure()
        self.all_shot_files = [i for i in os.listdir(self.OSC_DATA_PATH) if os.path.isfile(os.path.join(self.OSC_DATA_PATH, i))]
        self.sorted_shots = self.sort_all_shots()
        pio.renderers.default = "browser"
        return  

    def get_shot_files(self, shot_nmbr):
        return self.sorted_shots[str(shot_nmbr)]

    def plot_raw_data(self, file_name):
        file_data = np.loadtxt(file_name)
        time_arr = file_data[:, 0]
        osc_info = self.id_osc(file_name)
        osc_params = get_osc_config(osc_info['osc_id'], shot_number=int(osc_info['shot_nmbr']))
        channel_names = osc_params['channels']
        axes_labels = osc_params['axes_labels']
        for col, label in zip(file_data.T[1:], channel_names):
            self.fig.add_trace(go.Scatter(x=time_arr, y=col, name=label, mode='lines'))
        plot_title = f"{osc_info['osc_id']} shot {osc_info['shot_nmbr']} {osc_info['date']}"
        self.fig.update_layout(template='plotly_dark', title=plot_title, xaxis_title=axes_labels[0], yaxis_title=axes_labels[1])
        self.fig.show()

    def id_osc(self, file_name):
        file_name = os.path.normpath(file_name) 
        file_name = file_name.split(os.sep)[-1]
        shot_nmbr, date, osc_id = file_name.strip('.txt').strip('shot').split('_')
        osc_info = {
            'shot_nmbr': shot_nmbr,
            'date': date,
            'osc_id': osc_id
        }
        return osc_info

    def sort_all_shots(self):
        shot_nmbrs = set([ i.split('_')[0].strip('shot') for i in self.all_shot_files ])
        shot_nmbrs = sorted(list(shot_nmbrs))
        ordered_data = dict()
        for sn in shot_nmbrs:
            ordered_data[sn] = [i for i in self.all_shot_files if f'shot{sn}' in i]
        return ordered_data

    def current_rogowski_no_ext_int(self, rogowski_v, time):
        smooth_signal = savgol_filter(rogowski_v, 100, 9)
        avg_noise = np.mean(smooth_signal[:self.noise_len])
        smooth_signal -= avg_noise
        rogowski_i = cumulative_trapezoid(smooth_signal, time)
        rogowski_i *= 5.7 * 10 ** 7
        return rogowski_i

    def current_rogowski_ext_int(self, rogowski_v, time):
        smooth_signal = savgol_filter(rogowski_v, 100, 9)
        tds7104_cfg = get_osc_config('tds7104')
        rogowski_i = smooth_signal * np.array(tds7104_cfg.get('calibration_factors', [1.0]))
        return rogowski_i

    def find_shots(self, shot_list):
        pass

    def set_universal_time(self):
        times = {
            'shot_nmbr':{
                'osc_id': [np.array(), ...]
            }
        }
        current_osc_id = "tds7104"
        all_rogowski_files = [i for i in self.all_shot_files if current_osc_id in i]
        for f in all_rogowski_files:
            shot_nmbr = f.split('_')[0].strip('shot') 
            f_data = np.loadtxt(f)
            time = f_data[:, 0]
            ##Integrated
            current_ext_v = f_data[:, 1]
            current_ext = self.current_rogowski_ext_int(current_ext_v)
            ##Non integrated
            current_no_ext_v = f_data[:, 2]
            current_no_ext = self.current_rogowski_no_ext_int(current_no_ext_v)
            ##
            curr_no_ext_max, curr_no_ext_max_ind = np.max(current_no_ext), np.argmax(current_no_ext)
            electric_noise = 5.0 * np.std(current_ext[:self.noise_len])
            curr_ext_min_ind = np.argmin(np.abs(current_ext[:curr_no_ext_max_ind] - electric_noise))
            time_0 = time[curr_ext_min_ind] #tPr0
            ##
            lower_ind, upper_ind = round(0.8 * curr_ext_min_ind), round(0.9 * curr_ext_min_ind)
            current_ext -= np.mean(current_ext[lower:upper])
            curr_ext_max = np.max(curr_ext)
            ##
            curr_no_ext_10_ind = np.argmin(np.abs(curr_ext[:curr_no_ext_max_ind] - 0.1 * curr_ext_max))
            curr_no_ext_90_ind = np.argmin(np.abs(curr_ext[:curr_no_ext_max_ind] - 0.9 * curr_ext_max))
            time_10 = time[curr_no_ext_10_ind]
            time_90 = time[curr_no_ext_90_ind]
            #Rising Time
            time_rise = (time_90 - time_10) * 10 ** 9 #[ns]
            ch_times = self.obtain_ch_times(shot_nmbr, time_0)
            return 
    
    def obtain_ch_times(self, shot_nmbr, time_0, reference_channel_index=1):
        for j in self.sorted_shots[str(shot_nmbr)]:                
            osc_time = np.loadtxt(j)[0]
            channel_times = np.array([osc_time] * 4)
            j_info = self.id_osc(j)
            shot_number = int(j_info['shot_nmbr']) if j_info['shot_nmbr'].isdigit() else None
            reference_cfg = get_osc_config('tds7104', shot_number=shot_number)
            reference_delays = np.array(reference_cfg.get('times', [0.0]))
            reference_delay = reference_delays[reference_channel_index] if reference_channel_index < len(reference_delays) else 0.0
            osc_cfg = get_osc_config(j_info['osc_id'], shot_number=shot_number)
            cable_delays = np.array(osc_cfg.get('times', [0.0] * len(channel_times)))
            channel_times = [channel_times[i] - time_0 - (cable_delays[i] - reference_delay) for i in range(len(channel_times))]
        return channel_times     

if __name__ == '__main__':
    a = OscilloscopeReader()
    file_path = os.path.join('osc_data', 'shot1558_20240410_dpo4104.txt')
    a.plot_raw_data(file_path)
    a.id_osc(file_path)
    a.list_all_shots()







