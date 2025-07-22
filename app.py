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
        self.recommendation_text = tk.StringVar(value="")
        self.artillery_type = tk.StringVar(value="Mortar")
        self.temp_line = None
        self.temp_text = None

        self.dx_corr = 0.0
        self.dy_corr = 0.0
        self.recommendation_text.set("No impacts yet")

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
        # create a Notebook with two tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)

        # ── Tab 1: your existing Fire Control UI ────────────────────────
        tab1 = ttk.Frame(self.notebook)
        self.notebook.add(tab1, text='Fire Control')
        main = ttk.Frame(tab1, padding=10)
        main.pack(fill='both', expand=True)
        self.setup_control_panel(main)
        self.setup_plot_panel(main)

        # ── Tab 2: Artillery Info Browser ───────────────────────────────
        tab2 = ttk.Frame(self.notebook)
        self.notebook.add(tab2, text='Artillery Info')
        self.setup_info_tab(tab2)


    def setup_info_tab(self, parent):
        # — create scrollable canvas/frame combo —
        canvas = tk.Canvas(parent, borderwidth=0, background='#e0e0e0')
        vsb = ttk.Scrollbar(parent, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side='right', fill='y')
        canvas.pack(side='left', fill='both', expand=True)

        container = ttk.Frame(canvas, style='Control.TFrame')
        canvas.create_window((0,0), window=container, anchor='nw')
        container.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )

        # diagram constants
        W, H = 500, 80            # diagram canvas size
        margin = 20               # left/right padding
        rect_h = 20               # half‐height of the spread box

        for art, ((min_d, max_d), (min_r, max_r)) in self.artillery_ranges.items():
            # each row: name on left, diagram + info on right
            row = ttk.Frame(container, style='Control.TFrame', padding=(5,2))
            row.pack(fill='x', pady=4)

            # 1) artillery name
            ttk.Label(
                row,
                text=art,
                style='Control.TLabel',
                width=15
            ).pack(side='left')

            # 2) right‐side subframe for diagram + numeric info
            right = ttk.Frame(row, style='Control.TFrame')
            right.pack(side='left', fill='x', expand=True)

            # 2a) drawing canvas
            diag = tk.Canvas(
                right,
                width=W,
                height=H,
                background='white',
                highlightthickness=0
            )
            diag.pack(fill='x', expand=True, padx=5)
            y = H // 2

            # full scale so the max spread at max_d never clips
            full_extent = max_d + max_r
            def to_px(d):
                return margin + (d / full_extent) * (W - 2*margin)

            # 2b) baseline from 0 → full_extent
            diag.create_line(
                to_px(0), y, to_px(full_extent), y,
                dash=(4,2), width=2, fill='black'
            )

            # 2c) vertical guide lines at min_d & max_d
            for d in (min_d, max_d):
                x = to_px(d)
                diag.create_line(
                    x, y-rect_h-5, x, y+rect_h+5,
                    dash=(2,2), fill='gray', width=1
                )

            # 2d) endpoint ticks & labels
            for d, lbl in ((0,'0m'), (min_d,f'{min_d}m'), (max_d,f'{max_d}m')):
                x = to_px(d)
                diag.create_line(x, y-8, x, y+8, width=2, fill='black')
                diag.create_text(
                    x, y+20,
                    text=lbl,
                    anchor='n',
                    font=('TkDefaultFont', 9, 'bold')
                )

            # 2e) solid orange spread boxes at min_d & max_d
            for d, spread in ((min_d, min_r), (max_d, max_r)):
                x = to_px(d)
                half_w = (spread / full_extent) * (W - 2*margin)
                diag.create_rectangle(
                    x-half_w, y-rect_h,
                    x+half_w, y+rect_h,
                    fill='orange',
                    stipple='gray25',
                    outline='',
                    width=1
                )

            # 3) numeric info below diagram
            info = (
                f"Range: {min_d}–{max_d} m    "
                f"Spread: {min_r:.1f}–{max_r:.1f} m"
            )
            ttk.Label(
                right,
                text=info,
                style='Control.TLabel',
                justify='left'
            ).pack(anchor='w', pady=(4,0))

    def setup_control_panel(self, parent):
        ctrl = ttk.Frame(parent, padding=5, width=500, style='Control.TFrame')
        ctrl.grid(row=0, column=0, sticky='nsew', padx=(0,10))
        ctrl.grid_propagate(False)

        # 1) Target inputs
        self.setup_target_section(ctrl, 0)
        # 2) Artillery teams
        self.setup_artillery_section(ctrl, 4)
        # 3) Reset buttons
        self.setup_controls_section(ctrl, 8)
        # 4) User instructions
        self.setup_instructions_section(ctrl, 10)

    def setup_instructions_section(self, parent, row):
        f = ttk.LabelFrame(
            parent,
            text='Instructions',
            padding=10,
            style='Control.TLabelframe'
        )
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(10,0))
        instruction_text = (
            "• Enter your target’s Distance and Azimuth, then choose Artillery Type.\n"
            "• For each firing team, input its Distance/Azimuth from the spotter.\n"
            "• Click on the map to record each shell’s impact (yellow diamond).\n"
            "• The green ring = expected “on-target” zone; orange ring = max acceptable spread.\n"
            "  – If a shot lands outside orange, the tool suggests a correction (Δx, Δy).\n"
            "  – If the last two shots both land inside green, it will say “Hold fire.”\n"
            "\n"
            "Manual Override (Why & How):\n"
            "• Even if you see “Hold fire,” spread may be acting in your favor of the wind and your center shot could be off.\n"
            "  – If your last 2-3 shots are baised to one side of the target in the orange zone, consider adjusting in the opposite direction.\n"
            "  – Ideally, your shots should 'surround' the target with a simple distribution"
        )
        ttk.Label(
            f,
            text=instruction_text,
            style='Control.TLabel',
            justify='left',
            wraplength=460
        ).grid(row=0, column=0, sticky='w')

    def setup_target_section(self, parent, row):
        f = ttk.LabelFrame(
            parent,
            text='Target Position',
            padding=10,
            style='Control.TLabelframe'
        )
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))

        # 1) Distance entry
        ttk.Label(f, text='Distance (m):', style='Control.TLabel')\
            .grid(row=0, column=0, sticky='w')
        ttk.Entry(f, textvariable=self.target_distance, width=15)\
            .grid(row=0, column=1, sticky='we', padx=(10,20))

        # 2) Azimuth entry
        ttk.Label(f, text='Azimuth (°):', style='Control.TLabel')\
            .grid(row=1, column=0, sticky='w')
        ttk.Entry(f, textvariable=self.target_azimuth, width=15)\
            .grid(row=1, column=1, sticky='we', padx=(10,20))

        # 3) Artillery type chooser
        ttk.Label(f, text='Artillery Type:', style='Control.TLabel')\
            .grid(row=2, column=0, sticky='w')
        ttk.Combobox(
            f,
            textvariable=self.artillery_type,
            values=list(self.artillery_ranges.keys()),
            state='readonly'
        ).grid(row=2, column=1, sticky='we', padx=(10,20))

        # 4) Effective‐range + inaccuracy display
        self.artillery_info_label = ttk.Label(
            f,
            text='',  # filled in below
            style='Control.TLabel'
        )
        self.artillery_info_label.grid(
            row=3, column=0, columnspan=2,
            sticky='w', pady=(10,0)
        )

        f.columnconfigure(1, weight=1)

        # redraw plot when distance or azimuth changes
        self.target_distance.trace_add('write', self.update_plot)
        self.target_azimuth.trace_add('write', self.update_plot)

        # on type change, update info *and* clear old impacts
        self.artillery_type.trace_add('write', self.on_artillery_type_change)

        # init the info label (but NOT the plot yet)
        self.update_artillery_info()


    def on_artillery_type_change(self, *args):
        # 1) refresh the range/spread label
        self.update_artillery_info()
        # 2) clear any old impacts & corrections
        self.reset_impacts()
        # (reset_impacts() already calls update_plot for us)


    def update_artillery_info(self, *args):
        art = self.artillery_type.get()
        (min_d, max_d), (min_r, max_r) = self.artillery_ranges[art]

        # Format the ranges neatly
        info = (
            f"Effective Range: {min_d}–{max_d} m    "
            f"Spread Radius: {min_r:.1f}–{max_r:.1f} m"
        )
        self.artillery_info_label.config(text=info)

    def setup_artillery_section(self, parent, row):
        f = ttk.LabelFrame(parent, text='Artillery Teams', padding=10, style='Control.TLabelframe')
        f.grid(row=row, column=0, columnspan=4, sticky='we', pady=(0,10))
        headers = ['Team', 'Distance (m)', 'Azimuth (°)', 'Firing Solution', 'Range']
        for c, h in enumerate(headers):
            ttk.Label(f, text=h, font=('Arial',10,'bold'), style='Control.TLabel').grid(row=0, column=c, padx=5)
        ttk.Label(f, text='Spotter', style='Control.TLabel').grid(row=1, column=0, sticky='w', padx=5)
        ttk.Entry(f, textvariable=self.target_distance, width=10, state='disabled').grid(row=1, column=1)
        ttk.Entry(f, textvariable=self.target_azimuth, width=10, state='disabled').grid(row=1, column=2)
        ttk.Label(f, textvariable=self.spotter_solution, style='Control.TLabel').grid(row=1, column=3, padx=5)
        teams = [f'Team {i+1}' for i in range(4)]
        for i, name in enumerate(teams, start=2):
            lbl = ttk.Label(f, text=name, style='Control.TLabel'); lbl.grid(row=i, column=0, sticky='w', padx=5)
            dv, av = tk.DoubleVar(), tk.DoubleVar()
            ttk.Entry(f, textvariable=dv, width=10).grid(row=i, column=1)
            ttk.Entry(f, textvariable=av, width=10).grid(row=i, column=2)
            sol = ttk.Label(f, text='-- / --', style='Control.TLabel'); sol.grid(row=i, column=3, padx=5)

            show_var = tk.BooleanVar(value=True)
            chk = tk.Checkbutton(f, variable=show_var, command=self.update_plot,
                                 onvalue=True, offvalue=False,
                                 bg='#e0e0e0', activebackground='#e0e0e0', relief='flat')
            chk.grid(row=i, column=4)
            self.show_team_ranges[name] = show_var

            self.team_entries[name] = {'distance': dv, 'azimuth': av, 'label': lbl, 'firing_solution': {'distance':0.0,'azimuth':0.0}}
            self.team_solution_labels[name] = sol
            dv.trace_add('write', self.update_plot)
            av.trace_add('write', self.update_plot)

    def setup_controls_section(self, parent, row):
        # Separator above
        sep = ttk.Separator(parent, orient='horizontal')
        sep.grid(row=row, column=0, columnspan=4, sticky='ew', pady=(10,5))

        # Frame to hold buttons
        f = ttk.Frame(parent, style='Control.TFrame')
        f.grid(row=row+1, column=0, columnspan=4, sticky='ew', padx=5, pady=(0,10))

        # Give the outer columns weight so buttons are centered
        f.columnconfigure(0, weight=1)
        f.columnconfigure(1, weight=0)
        f.columnconfigure(2, weight=0)
        f.columnconfigure(3, weight=1)

        # Total Reset
        btn_total = ttk.Button(
            f,
            text='TOTAL RESET',
            style='Control.TButton',
            command=self.total_reset
        )
        btn_total.grid(row=0, column=1, padx=10, pady=5, sticky='ew')

        # Reset Impacts
        btn_imp = ttk.Button(
            f,
            text='Reset Impacts',
            style='Control.TButton',
            command=self.reset_impacts
        )
        btn_imp.grid(row=0, column=2, padx=10, pady=5, sticky='ew')

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
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def reset_impacts(self):
        # Clear recorded impacts
        self.impact_zones.clear()

        # Clear any persistent correction so solutions revert to original
        self.dx_corr = 0.0
        self.dy_corr = 0.0

        # Reset recommendation text
        self.recommendation_text.set("No impacts yet")

        # Redraw everything
        self.update_plot()

    def total_reset(self):
        # Reset target inputs
        self.target_distance.set(0.0)
        self.target_azimuth.set(0.0)

        # Reset team inputs and their last solutions
        for entry in self.team_entries.values():
            entry['distance'].set(0.0)
            entry['azimuth'].set(0.0)
            entry['firing_solution']['distance'] = 0.0
            entry['firing_solution']['azimuth'] = 0.0

        # Clear impacts and corrections
        self.impact_zones.clear()
        self.dx_corr = 0.0
        self.dy_corr = 0.0

        # Reset recommendation text
        self.recommendation_text.set("No impacts yet")

        # Redraw with everything back to factory defaults
        self.update_plot()

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
        # 1) Clear & style
        self.ax.clear()
        self.ax.set_facecolor('#2b2b2b')
        self.ax.grid(color='gray', linestyle='--')
        # Ensure autoscale is off so the view doesn't jump around
        self.ax.set_autoscale_on(False)

        # 2) Compute target in map coords
        td = self.safe_get_double(self.target_distance)
        ta = np.deg2rad(self.safe_get_double(self.target_azimuth))
        tx, ty = td * np.sin(ta), td * np.cos(ta)

        # 3) Interpolate spread radius at this distance
        art = self.artillery_type.get()
        (min_d, max_d), (min_r, max_r) = self.artillery_ranges[art]
        d0 = min(max(td, min_d), max_d)
        frac = (d0 - min_d) / (max_d - min_d) if max_d > min_d else 0
        total_r = min_r + frac * (max_r - min_r)
        inner_r, outer_r = total_r * 0.5, total_r

        # 4) Update correction only if last impact is outside the true spread
        if self.impact_zones:
            ix, iy = self.impact_zones[-1]
            miss = np.hypot(ix - tx, iy - ty)
            if miss > outer_r:
                self.dx_corr = tx - ix
                self.dy_corr = ty - iy
                self.recommendation_text.set(
                    f"Correct by ({self.dx_corr:.1f}m, {self.dy_corr:.1f}m)"
                )
            else:
                self.recommendation_text.set("Hold fire")
        else:
            self.dx_corr = self.dy_corr = 0.0
            self.recommendation_text.set("No impacts yet")

        # 5) Spotter uses persistent correction
        adj_x, adj_y = tx + self.dx_corr, ty + self.dy_corr
        sd = np.hypot(adj_x, adj_y)
        sa = np.degrees(np.arctan2(adj_x, adj_y)) % 360
        self.spotter_solution.set(f"{sd:.1f}m / {sa:.1f}°")

        # 6) Draw spotter & target
        self.ax.plot(0, 0, 'o', color='white', markersize=8, label='Spotter')
        self.ax.plot([0, tx], [0, ty], linestyle=':', color='white')
        self.ax.plot(tx, ty, 'X', color='red', markersize=10, label='Target')

        # 7) Plot each team
        for idx, (name, vars) in enumerate(self.team_entries.items()):
            d = self.safe_get_double(vars['distance'])
            a = np.deg2rad(self.safe_get_double(vars['azimuth']))
            if d == 0 and self.safe_get_double(vars['azimuth']) == 0:
                vars['label'].config(foreground='black')
                self.team_solution_labels[name].config(text='-- / --')
                continue

            x, y = d * np.sin(a), d * np.cos(a)
            dx, dy = tx - x + self.dx_corr, ty - y + self.dy_corr
            sol_d = np.hypot(dx, dy)
            sol_a = np.degrees(np.arctan2(dx, dy)) % 360

            # ← FIX: specify text=
            self.team_solution_labels[name].config(text=f"{sol_d:.1f}m / {sol_a:.1f}°")

            color = self.team_colors[idx % len(self.team_colors)]
            # dotted wedge = min_d→max_d around team
            if self.show_team_ranges[name].get():
                self.ax.add_patch(
                    patches.Wedge(
                        (x, y),
                        max_d, 0, 360,
                        width=(max_d - min_d),
                        edgecolor=color,
                        facecolor='none',
                        linestyle='--'
                    )
                )
            # team marker + aim line
            self.ax.plot(x, y, '^', color=color, markersize=8, label=name)
            self.ax.plot([x, tx], [y, ty], linestyle=':', color=color)

        # 8) Draw the green/orange rings at the target
        self.ax.add_patch(
            patches.Circle((tx, ty), inner_r,
                           facecolor='green', alpha=0.3, edgecolor='none')
        )
        self.ax.add_patch(
            patches.Wedge((tx, ty), outer_r, 0, 360,
                          width=(outer_r - inner_r),
                          facecolor='orange', alpha=0.3, edgecolor='none')
        )

        # 9) Plot impacts
        for i, (ix, iy) in enumerate(self.impact_zones, start=1):
            self.ax.plot(ix, iy, 'D', color='yellow')
            self.ax.text(ix, iy, str(i), color='black',
                         ha='center', va='center')

        # 10) Lock limits and draw legend
        lim = self.max_range * 1.1
        self.ax.set_xlim(-lim, lim)
        self.ax.set_ylim(-lim, lim)
        leg = self.ax.legend(loc='upper right', fontsize='small')
        for t in leg.get_texts():
            t.set_color('white')

        self.canvas.draw()

if __name__ == '__main__':
    root = tk.Tk()
    app = FoxholeArtilleryApp(root)
    root.mainloop()
