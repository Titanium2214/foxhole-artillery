import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class FoxholeArtilleryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("419 - Artillery Control Center")
        self.root.geometry("1400x900")

        # Style for inputs/themes
        style = ttk.Style()
        style.theme_use('clam')
        # Control panel style (lighter)
        style.configure('Control.TFrame', background='#e0e0e0')
        style.configure('Control.TLabel', background='#e0e0e0', foreground='black')
        style.configure('TEntry', fieldbackground='white', foreground='black')
        style.configure('TButton', background='#5c5f61', foreground='white')
        style.configure('Control.TLabelframe', background='#e0e0e0', foreground='black')
        style.configure('Control.TLabelframe.Label', background='#e0e0e0', foreground='black')

        # Variables
        self.target_distance = tk.DoubleVar(value=0.0)
        self.target_azimuth = tk.DoubleVar(value=0.0)
        self.spotter_solution = tk.StringVar(value="-- / --")

        # Team entries & solutions
        self.team_entries = {}
        self.team_solution_labels = {}
        self.team_colors = ['cyan', 'magenta', 'yellow', 'lime']

        # Range and impacts
        self.max_range = 100
        self.impact_zones = []

        # Build UI
        self.setup_gui()
        self.root.after(100, self.initialize_plotting)

    def setup_gui(self):
        main = ttk.Frame(self.root, padding=10)
        main.grid(row=0, column=0, sticky='nsew')
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main.columnconfigure(1, weight=1)
        main.rowconfigure(0, weight=1)

        self.setup_control_panel(main)
        self.setup_plot_panel(main)

    def setup_control_panel(self, parent):
        ctrl = ttk.Frame(parent, padding=5, width=500, style='Control.TFrame')
        ctrl.grid(row=0, column=0, sticky='nsew', padx=(0,10))
        ctrl.grid_propagate(False)

        self.setup_target_section(ctrl, 0)
        self.setup_artillery_section(ctrl, 4)
        self.setup_controls_section(ctrl, 10)

    def setup_target_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Target Position', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        ttk.Label(f, text='Distance (m):', style='Control.TLabel').grid(row=0, column=0, sticky='w')
        ttk.Entry(f, textvariable=self.target_distance, width=15).grid(row=0, column=1, sticky='we', padx=(10,20))
        ttk.Label(f, text='Azimuth (°):', style='Control.TLabel').grid(row=1, column=0, sticky='w')
        ttk.Entry(f, textvariable=self.target_azimuth, width=15).grid(row=1, column=1, sticky='we', padx=(10,20))
        f.columnconfigure(1, weight=1)
        self.target_distance.trace_add('write', self.update_plot)
        self.target_azimuth.trace_add('write', self.update_plot)

    def setup_artillery_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Artillery Teams', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        headers = ['Team', 'Distance (m)', 'Azimuth (°)', 'Solution']
        for c, h in enumerate(headers):
            ttk.Label(f, text=h, font=('Arial',10,'bold'), style='Control.TLabel').grid(row=0, column=c, padx=5)

        # Spotter row
        ttk.Label(f, text='Spotter', style='Control.TLabel').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(f, textvariable=self.target_distance, width=10, state='disabled').grid(row=1, column=1)
        ttk.Entry(f, textvariable=self.target_azimuth, width=10, state='disabled').grid(row=1, column=2)
        ttk.Label(f, textvariable=self.spotter_solution, style='Control.TLabel').grid(row=1, column=3, sticky='w', padx=5)

        teams = [f'Team {i+1}' for i in range(4)]
        for i, name in enumerate(teams, start=2):
            ttk.Label(f, text=name, style='Control.TLabel').grid(row=i, column=0, sticky='w', padx=5)
            dv = tk.DoubleVar(value=0.0)
            av = tk.DoubleVar(value=0.0)
            ttk.Entry(f, textvariable=dv, width=10).grid(row=i, column=1)
            ttk.Entry(f, textvariable=av, width=10).grid(row=i, column=2)
            sol = ttk.Label(f, text='-- / --', style='Control.TLabel')
            sol.grid(row=i, column=3, sticky='w', padx=5)
            self.team_entries[name] = {'distance': dv, 'azimuth': av}
            self.team_solution_labels[name] = sol
            dv.trace_add('write', self.update_plot)
            av.trace_add('write', self.update_plot)

    def setup_controls_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Controls', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        ttk.Button(f, text='Reset Impacts', command=self.reset_impacts).grid(row=0, column=3, sticky='e')

    def setup_plot_panel(self, parent):
        pf = ttk.Frame(parent, padding=5)
        pf.grid(row=0, column=1, sticky='nsew')
        pf.columnconfigure(0, weight=1)
        pf.rowconfigure(0, weight=1)

        self.fig, self.ax = plt.subplots(figsize=(8,8))
        # Dark plot style
        self.fig.patch.set_facecolor('#2b2b2b')
        self.ax.set_facecolor('#2b2b2b')
        self.ax.tick_params(colors='white')
        for spine in self.ax.spines.values(): spine.set_color('white')
        self.ax.title.set_color('white')
        self.ax.xaxis.label.set_color('white')
        self.ax.yaxis.label.set_color('white')
        self.ax.grid(color='gray', linestyle='--')

        self.canvas = FigureCanvasTkAgg(self.fig, master=pf)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.canvas.mpl_connect('button_press_event', self.on_click)

    def reset_impacts(self):
        self.impact_zones.clear()
        self.update_plot()

    def initialize_plotting(self):
        self.update_plot()

    def on_click(self, event):
        if event.inaxes != self.ax or event.button != 1: return
        self.impact_zones.append((event.xdata, event.ydata))
        self.update_plot()

    def update_plot(self, *args):
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(color='gray', linestyle='--')

        # Original target
        td = self.target_distance.get()
        ta = np.deg2rad(self.target_azimuth.get())
        tx, ty = td * np.sin(ta), td * np.cos(ta)

        # Spotter solution updated by correction
        if self.impact_zones:
            ix, iy = self.impact_zones[-1]
            ex, ey = tx - ix, ty - iy
            cx, cy = tx + ex, ty + ey
        else:
            cx, cy = tx, ty
        sol_dist_sp = np.hypot(cx, cy)
        sol_az_sp = np.degrees(np.arctan2(cx, cy)) % 360
        self.spotter_solution.set(f"{sol_dist_sp:.1f}m / {sol_az_sp:.1f}°")

        # Spotter marker & dotted line to target
        self.ax.plot(0, 0, 'o', color='white', markersize=8, label='Spotter')
        self.ax.plot([0, tx], [0, ty], linestyle=':', color='white')

        # Target marker
        self.ax.plot(tx, ty, 'X', color='red', markersize=10, label='Target')

        # Impact markers
        for idx, (ix, iy) in enumerate(self.impact_zones, start=1):
            self.ax.plot(ix, iy, 'D', color='yellow')
            self.ax.text(ix, iy, str(idx), color='black', ha='center', va='center')

        # Teams
        for idx, (name, vars) in enumerate(self.team_entries.items()):
            d = vars['distance'].get()
            a = np.deg2rad(vars['azimuth'].get())
            if d == 0 and vars['azimuth'].get() == 0:
                self.team_solution_labels[name].config(text='-- / --')
                continue
            x, y = d * np.sin(a), d * np.cos(a)
            color = self.team_colors[idx % len(self.team_colors)]
            # Team marker & dotted line
            self.ax.plot(x, y, '^', color=color, markersize=8, label=name)
            self.ax.plot([x, tx], [y, ty], linestyle=':', color=color)

            # Compute corrected solution
            dx, dy = cx - x, cy - y
            sol_dist = np.hypot(dx, dy)
            sol_az = np.degrees(np.arctan2(dx, dy)) % 360
            self.team_solution_labels[name].config(text=f"{sol_dist:.1f}m / {sol_az:.1f}°")

            self.max_range = max(self.max_range, abs(tx), abs(ty), d)

        # Axis limits
        lim = self.max_range * 1.1
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        # Legend
        leg = self.ax.legend(loc='upper right', fontsize='small')
        for text in leg.get_texts():
            text.set_color('white')
        self.canvas.draw()

if __name__=='__main__':
    root = tk.Tk()
    app = FoxholeArtilleryApp(root)
    root.mainloop()
