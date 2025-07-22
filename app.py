import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import matplotlib.patches as patches

class FoxholeArtilleryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("419 - Artillery Control Center")
        self.root.geometry("1400x900")

        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Control.TFrame', background='#e0e0e0')
        style.configure('Control.TLabel', background='#e0e0e0', foreground='black')
        style.configure('TEntry', fieldbackground='white', foreground='black')
        style.configure('TButton', background='#5c5f61', foreground='white')
        style.configure('Control.TLabelframe', background='#e0e0e0', foreground='black')
        style.configure('Control.TLabelframe.Label', background='#e0e0e0', foreground='black')

        self.target_distance = tk.DoubleVar(value=0.0)
        self.target_azimuth = tk.DoubleVar(value=0.0)
        self.spotter_solution = tk.StringVar(value="-- / --")
        self.artillery_type = tk.StringVar(value="Mortar")
        self.temp_line = None
        self.temp_text = None

        self.show_team_ranges = {}

        self.artillery_ranges = {
            "Mortar": ((45, 80), (5.5, 12)),
            "Gunship": ((75, 100), (2.5, 14.5)),
            "Devitt-Caine": ((45, 80), (2.5, 9.45)),
            "Peltast": ((45, 80), (2.5, 9.45)),
            "Skycaller": ((275, 350), (37.5, 60)),
            "Rocket Battery": ((350, 400), (41.5, 57.7)),
            "Wasp Nest": ((375, 450), (37.5, 60)),
            "Hades' Net": ((300, 575), (35, 52)),
            "O'Brien Squire": ((375, 500), (39, 51)),
            "r-17 Skirmisher": ((375, 500), (37, 51)),
        }

        self.team_entries = {}
        self.team_solution_labels = {}
        self.team_colors = ['cyan', 'magenta', 'yellow', 'lime']
        self.impact_zones = []
        self.max_range = 100

        self.setup_gui()
        self.root.after(100, self.update_plot)

    def safe_get_double(self, var):
        try:
            return var.get()
        except tk.TclError:
            return 0.0
        
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
        ttk.Label(f, text='Artillery Type:', style='Control.TLabel').grid(row=2, column=0, sticky='w')
        types = list(self.artillery_ranges.keys())
        ttk.Combobox(f, textvariable=self.artillery_type, values=types, state='readonly').grid(row=2, column=1, sticky='we', padx=(10,20))
        self.artillery_info_label = ttk.Label(f, text='', style='Control.TLabel')
        self.artillery_info_label.grid(row=3, column=0, columnspan=2, sticky='w')
        f.columnconfigure(1, weight=1)
        self.target_distance.trace_add('write', self.update_plot)
        self.target_azimuth.trace_add('write', self.update_plot)
        self.artillery_type.trace_add('write', self.update_plot)

    def setup_artillery_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Artillery Teams', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        headers = ['Team', 'Distance (m)', 'Azimuth (°)', 'Solution']
        for c, h in enumerate(headers):
            ttk.Label(f, text=h, font=('Arial',10,'bold'), style='Control.TLabel').grid(row=0, column=c, padx=5)

        ttk.Label(f, text='Spotter', style='Control.TLabel').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(f, textvariable=self.target_distance, width=10, state='disabled').grid(row=1, column=1)
        ttk.Entry(f, textvariable=self.target_azimuth, width=10, state='disabled').grid(row=1, column=2)
        ttk.Label(f, textvariable=self.spotter_solution, style='Control.TLabel').grid(row=1, column=3, sticky='w', padx=5)

        teams = [f'Team {i+1}' for i in range(4)]
        for i, name in enumerate(teams, start=2):
            lbl = ttk.Label(f, text=name, style='Control.TLabel')
            lbl.grid(row=i, column=0, sticky='w', padx=5)
            dv = tk.DoubleVar(value=0.0)
            av = tk.DoubleVar(value=0.0)
            ttk.Entry(f, textvariable=dv, width=10).grid(row=i, column=1)
            ttk.Entry(f, textvariable=av, width=10).grid(row=i, column=2)
            sol = ttk.Label(f, text='-- / --', style='Control.TLabel')
            sol.grid(row=i, column=3, sticky='w', padx=5)
            self.team_entries[name] = {
                'distance': dv,
                'azimuth': av,
                'label': lbl,
                'firing_solution': {'distance': 0.0, 'azimuth': 0.0}
            }
            self.team_solution_labels[name] = sol
            dv.trace_add('write', self.update_plot)
            av.trace_add('write', self.update_plot)

    def setup_controls_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Controls', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        ttk.Button(f, text='TOTAL RESET', command=self.total_reset).grid(row=0, column=2, sticky='e')
        ttk.Button(f, text='Reset Impacts', command=self.reset_impacts).grid(row=0, column=3, sticky='e')
        for i, name in enumerate(self.team_entries.keys()):
            self.show_team_ranges[name] = tk.BooleanVar(value=True)
            ttk.Checkbutton(f, text=f'Show {name} Range', variable=self.show_team_ranges[name], command=self.update_plot).grid(row=1+i//2, column=i%2, sticky='w')

    def setup_plot_panel(self, parent):
        pf = ttk.Frame(parent, padding=5)
        pf.grid(row=0, column=1, sticky='nsew')
        pf.columnconfigure(0, weight=1)
        pf.rowconfigure(0, weight=1)
        self.fig, self.ax = plt.subplots(figsize=(8,8))
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
        self.canvas.mpl_connect("motion_notify_event", self.on_mouse_move)

    def reset_impacts(self):
        self.impact_zones.clear()
        self.update_plot()

    def total_reset(self):
        self.target_distance.set(0.0)
        self.target_azimuth.set(0.0)
        for entry in self.team_entries.values():
            entry['distance'].set(0.0)
            entry['azimuth'].set(0.0)
            entry['firing_solution']['distance'] = 0.0
            entry['firing_solution']['azimuth'] = 0.0
        self.reset_impacts()

    def on_click(self, event):
        if event.inaxes != self.ax or event.button != 1:
            return
        self.impact_zones.append((event.xdata, event.ydata))
        if self.temp_line:
            try: self.temp_line.remove()
            except: pass
            self.temp_line = None
        if self.temp_text:
            try: self.temp_text.remove()
            except: pass
            self.temp_text = None
        self.update_plot()

    def on_mouse_move(self, event):
        if not event.inaxes: return
        mx, my = event.xdata, event.ydata
        td = self.safe_get_double(self.target_distance)
        ta = np.deg2rad(self.safe_get_double(self.target_azimuth))
        tx, ty = td * np.sin(ta), td * np.cos(ta)
        if self.temp_line:
            try: self.temp_line.remove()
            except: pass
            self.temp_line = None
        if self.temp_text:
            try: self.temp_text.remove()
            except: pass
            self.temp_text = None
        self.temp_line = self.ax.plot([tx, mx], [ty, my], linestyle=':', color='yellow')[0]
        dist = np.hypot(mx - tx, my - ty)
        self.temp_text = self.ax.text(mx, my, f"{dist:.1f} m", color='yellow', fontsize=8, ha='left', va='bottom')
        self.canvas.draw()

    def update_plot(self, *args):
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(color='gray', linestyle='--')

        # Original target location (entered by user)
        td = self.safe_get_double(self.target_distance)
        ta = np.deg2rad(self.safe_get_double(self.target_azimuth))
        tx, ty = td * np.sin(ta), td * np.cos(ta)  # true target
        target_x, target_y = tx, ty

        # Compute correction vector from last impact to target (used for adjusted solutions)
        if self.impact_zones:
            impact_x, impact_y = self.impact_zones[-1]
            dx_corr = target_x - impact_x
            dy_corr = target_y - impact_y
        else:
            dx_corr = dy_corr = 0.0

        # Apply correction to spotter solution
        adj_tx = target_x + dx_corr
        adj_ty = target_y + dy_corr
        spotter_dist = np.hypot(adj_tx, adj_ty)
        spotter_az = np.degrees(np.arctan2(adj_tx, adj_ty)) % 360
        self.spotter_solution.set(f"{spotter_dist:.1f}m / {spotter_az:.1f}°")

        self.ax.plot(0, 0, 'o', color='white', markersize=8, label='Spotter')
        self.ax.plot([0, target_x], [0, target_y], linestyle=':', color='white')
        self.ax.plot(target_x, target_y, 'X', color='red', markersize=10, label='Target')

        self.max_range = 100

        for idx, (name, vars) in enumerate(self.team_entries.items()):
            d = self.safe_get_double(vars['distance'])
            a = np.deg2rad(self.safe_get_double(vars['azimuth']))
            if d == 0 and vars['azimuth'].get() == 0:
                self.team_solution_labels[name].config(text='-- / --')
                vars['label'].config(foreground='black')
                continue

            x, y = d * np.sin(a), d * np.cos(a)

            # Corrected firing vector
            dx = target_x - x + dx_corr
            dy = target_y - y + dy_corr
            sol_dist = np.hypot(dx, dy)
            sol_az = np.degrees(np.arctan2(dx, dy)) % 360

            vars['firing_solution']['distance'] = sol_dist
            vars['firing_solution']['azimuth'] = sol_az

            self.team_solution_labels[name].config(text=f"{sol_dist:.1f}m / {sol_az:.1f}°")

            color = self.team_colors[idx % len(self.team_colors)]
            self.ax.plot(x, y, '^', color=color, markersize=8, label=name)
            self.ax.plot([x, target_x], [y, target_y], linestyle=':', color=color)

            # Artillery range visualization (based on actual target only!)
            art_type = self.artillery_type.get()
            if art_type in self.artillery_ranges:
                (min_dist, max_dist), (min_r, max_r) = self.artillery_ranges[art_type]
                firing_dist = max(min(sol_dist, max_dist), min_dist)
                frac = (firing_dist - min_dist) / (max_dist - min_dist) if max_dist > min_dist else 0
                total_radius = min_r + frac * (max_r - min_r)
                inner_radius = total_radius * 0.5
                outer_radius = total_radius

                if self.show_team_ranges.get(name, tk.BooleanVar()).get():
                    self.ax.add_patch(
                        patches.Wedge((x, y), max_dist, 0, 360, width=max_dist - min_dist,
                                      edgecolor=color, facecolor='none', linestyle='--')
                    )

                self.ax.add_patch(
                    patches.Circle((target_x, target_y), inner_radius,
                                   facecolor='green', alpha=0.3, edgecolor='none')
                )
                self.ax.add_patch(
                    patches.Wedge((target_x, target_y), outer_radius, 0, 360,
                                  width=outer_radius - inner_radius,
                                  facecolor='orange', alpha=0.3, edgecolor='none')
                )

            self.max_range = max(self.max_range, abs(x), abs(y), abs(target_x), abs(target_y))

        # Draw impact zones
        for (ix, iy) in self.impact_zones:
            self.ax.plot(ix, iy, 'D', color='yellow')
            self.ax.text(ix, iy, str(self.impact_zones.index((ix, iy)) + 1), color='black', ha='center', va='center')
            self.max_range = max(self.max_range, abs(ix), abs(iy))

        # Final plot settings
        lim = self.max_range * 1.1
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        leg = self.ax.legend(loc='upper right', fontsize='small')
        for text in leg.get_texts():
            text.set_color('white')
        self.canvas.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = FoxholeArtilleryApp(root)
    root.mainloop()
