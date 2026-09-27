#!/usr/bin/env python3
"""Solar battery planning GUI. Estimates energy, not electrical wiring safety."""
import csv
import math
import statistics
import tkinter as tk
from datetime import date, datetime, timedelta
from pathlib import Path
from tkinter import filedialog, messagebox, ttk


def number(value, label, low=0, high=None):
    try:
        x = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{label} must be a number") from None
    if not math.isfinite(x) or x < low or (high is not None and x > high):
        raise ValueError(f"{label} must be between {low} and {high if high is not None else 'infinity'}")
    return x


def simulate(capacity_wh, start_soc, min_soc, load_w, solar_wh_day, inverter_eff, days, daily_load=None, daily_solar=None):
    """Daily energy model; solar is DC and load is AC. Returns SOC and shortfall."""
    stored = capacity_wh * start_soc / 100
    floor = capacity_wh * min_soc / 100
    rows = []
    for day in range(days):
        demand = (daily_load[day] if daily_load is not None else load_w * 24) / inverter_eff
        solar = daily_solar[day] if daily_solar is not None else solar_wh_day
        available = max(0, stored + solar - floor)
        unmet = max(0, demand - available)
        stored = min(capacity_wh, max(floor, stored + solar - demand))
        rows.append((day + 1, solar, demand * inverter_eff, stored / capacity_wh * 100, unmet * inverter_eff))
    return rows


class SolarApp:
    def __init__(self, root):
        self.root = root
        root.title('Solar & Battery Planner')
        root.geometry('1120x780')
        self.values = {}
        self.loads = []
        self.trends = []
        self.forecast = []
        style = ttk.Style()
        style.configure('Title.TLabel', font=('TkDefaultFont', 15, 'bold'))
        outer = ttk.Frame(root, padding=12)
        outer.pack(fill='both', expand=True)
        ttk.Label(outer, text='Solar & Battery Planner', style='Title.TLabel').pack(anchor='w')
        ttk.Label(outer, text='Estimates use energy averages; weather, shade, battery limits and instantaneous peaks can change actual runtime.').pack(anchor='w', pady=(3, 8))
        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill='both', expand=True)
        self.setup_tab()
        self.load_tab()
        self.forecast_tab()
        self.trend_tab()
        self.chart_tab()

    def tab(self, name):
        frame = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(frame, text=name)
        return frame

    def field(self, parent, row, label, key, default, col=0, width=12):
        ttk.Label(parent, text=label).grid(row=row, column=col, sticky='w', padx=5, pady=5)
        var = tk.StringVar(value=str(default))
        ttk.Entry(parent, textvariable=var, width=width).grid(row=row, column=col+1, sticky='w', padx=5, pady=5)
        self.values[key] = var
        return var

    def get(self, key, label=None, low=0, high=None):
        return number(self.values[key].get(), label or key.replace('_',' '), low, high)

    def config(self):
        count = self.get('battery_count', low=1)
        ah = self.get('battery_ah', low=1)
        volts = self.get('battery_volts', low=1)
        soc = self.get('start_soc', high=100)
        floor = self.get('min_soc', high=100)
        if floor >= soc:
            raise ValueError('Starting charge must exceed minimum charge')
        eff = self.get('inverter_eff', low=1, high=100)/100
        peak = self.get('observed_peak')
        hours = self.get('sun_hours', high=24)
        factor = self.get('cloud_percent', high=100)/100
        return count*ah*volts, soc, floor, eff, peak*hours, factor

    def setup_tab(self):
        f = self.tab('System & quick estimate')
        for row, args in enumerate([
            ('Battery count','battery_count',4), ('Ah per battery','battery_ah',400),
            ('Battery nominal voltage (V)','battery_volts',12.8), ('Starting charge (%)','start_soc',100),
            ('Minimum charge (%)','min_soc',20), ('Inverter efficiency (%)','inverter_eff',90),
            ('Observed solar peak (W)','observed_peak',440), ('Useful sun hours / day','sun_hours',4),
            ('Cloudy output (% of normal)','cloud_percent',35), ('Simple AC load (W)','quick_load',600),
            ('Days to simulate','days',7)]):
            self.field(f,row,*args)
        ttk.Button(f, text='Calculate quick estimate', command=self.quick).grid(row=11,column=0,columnspan=2,sticky='w',pady=12)
        self.quick_result = tk.StringVar(value='Enter your measurements and calculate.')
        ttk.Label(f,textvariable=self.quick_result,justify='left',wraplength=850).grid(row=12,column=0,columnspan=4,sticky='w')

    def quick(self):
        try:
            cap,soc,floor,eff,solar,cloud = self.config()
            load = self.get('quick_load',low=0.001)
            usable = cap*(soc-floor)/100*eff
            daily = solar*eff
            net = load*24-daily
            normal = 'sustainable on an average day (until storage fills)' if net <= 0 else f'{usable/net:.1f} days ({usable/net*24:.1f} hours), daily-average model'
            cloudy_net = load*24-daily*cloud
            cloudy = 'sustainable' if cloudy_net <= 0 else f'{usable/cloudy_net:.1f} days ({usable/cloudy_net*24:.1f} hours)'
            self.quick_result.set(f'Nominal battery energy: {cap:,.0f} Wh | usable AC energy: {usable:,.0f} Wh\n'
                f'Normal solar: {daily:,.0f} AC Wh/day | cloudy solar: {daily*cloud:,.0f} AC Wh/day\n'
                f'Load: {load*24:,.0f} Wh/day | no-sun runtime: {usable/load:.1f} hours\n'
                f'Normal: {normal} | cloudy: {cloudy}\n'
                'These daily averages do not guarantee continuous power through the night or brief high loads.')
        except ValueError as exc:
            messagebox.showerror('Check inputs',str(exc))

    def load_tab(self):
        f = self.tab('Variable loads')
        ttk.Label(f,text='Add loads with typical watts, hours per day, and low/high multipliers.').pack(anchor='w')
        form = ttk.Frame(f)
        form.pack(anchor='w',pady=8)
        for col,(label,default) in enumerate([('Name','600 W load'),('Watts','600'),('Hours/day','24'),('Low ×','0.5'),('High ×','2')]):
            ttk.Label(form,text=label).grid(row=0,column=col,padx=4)
            entry = ttk.Entry(form,width=16)
            entry.insert(0,default)
            entry.grid(row=1,column=col,padx=4)
            setattr(self,'load_'+str(col),entry)
        ttk.Button(form,text='Add',command=self.add_load).grid(row=1,column=5,padx=4)
        ttk.Button(form,text='Remove selected',command=self.remove_load).grid(row=1,column=6,padx=4)
        self.load_tree = ttk.Treeview(f,columns=('name','watts','hours','low','high','wh'),show='headings',height=10)
        for col in self.load_tree['columns']:
            self.load_tree.heading(col,text=col.title())
            self.load_tree.column(col,width=125)
        self.load_tree.pack(fill='x',pady=5)
        self.load_summary=tk.StringVar(value='No variable loads entered; forecasts use the simple AC load.')
        ttk.Label(f,textvariable=self.load_summary).pack(anchor='w',pady=8)

    def add_load(self):
        try:
            name=self.load_0.get().strip()
            if not name: raise ValueError('Enter a load name')
            watts=number(self.load_1.get(),'Watts')
            hours=number(self.load_2.get(),'Hours',high=24)
            low=number(self.load_3.get(),'Low multiplier')
            high=number(self.load_4.get(),'High multiplier')
            if high < low: raise ValueError('High multiplier must be at least low multiplier')
            item=(name,watts,hours,low,high)
            self.loads.append(item)
            self.load_tree.insert('', 'end', values=(*item,round(watts*hours)))
            self.update_load_summary()
        except ValueError as exc: messagebox.showerror('Check load',str(exc))

    def remove_load(self):
        indices=sorted((self.load_tree.index(i) for i in self.load_tree.selection()),reverse=True)
        for i in indices:
            del self.loads[i]
        for i in self.load_tree.selection(): self.load_tree.delete(i)
        self.update_load_summary()

    def update_load_summary(self):
        if not self.loads:
            self.load_summary.set('No variable loads entered; forecasts use the simple AC load.')
            return
        totals=[sum(w*h*m for _,w,h,lo,hi in self.loads for m in [({'low':lo,'normal':1,'high':hi}[case])]) for case in ('low','normal','high')]
        self.load_summary.set('Daily AC energy: low {:,.0f} | typical {:,.0f} | high {:,.0f} Wh'.format(*totals))

    def forecast_tab(self):
        f=self.tab('Forecast')
        bar=ttk.Frame(f);bar.pack(anchor='w',pady=5)
        ttk.Button(bar,text='Run scenarios',command=self.run_forecast).pack(side='left',padx=4)
        ttk.Button(bar,text='Export forecast CSV',command=self.export_forecast).pack(side='left',padx=4)
        ttk.Label(f,text='Scenarios use daily AC energy and selected solar output. Cloudy means the cloudy percentage on every forecast day.').pack(anchor='w',pady=5)
        cols=('scenario','date','solar_wh','load_wh','soc','unmet_wh')
        self.forecast_tree=ttk.Treeview(f,columns=cols,show='headings')
        for col,title,width in zip(cols,('Scenario','Date','Solar DC Wh','Load AC Wh','End charge %','Unserved AC Wh'),(150,130,130,130,135,155)):
            self.forecast_tree.heading(col,text=title)
            self.forecast_tree.column(col,width=width)
        self.forecast_tree.pack(fill='both',expand=True)

    def run_forecast(self):
        try:
            cap,soc,floor,eff,solar,cloud=self.config()
            days=int(self.get('days',low=1,high=365))
            if days != self.get('days'): raise ValueError('Days must be a whole number')
            base=self.get('quick_load')*24
            self.forecast=[]
            for label,mult,sun in [('Low load / normal sun','low',1),('Typical / normal sun','normal',1),('High load / normal sun','high',1),('Typical / cloudy','normal',cloud),('High load / cloudy','high',cloud)]:
                ac=sum(w*h*({'low':lo,'normal':1,'high':hi}[mult]) for _,w,h,lo,hi in self.loads) if self.loads else base*({'low':.5,'normal':1,'high':2}[mult])
                result=simulate(cap,soc,floor,0,0,eff,days,daily_load=[ac]*days,daily_solar=[solar*sun]*days)
                for offset,sw,lw,charge,unmet in result:
                    self.forecast.append((label,(date.today()+timedelta(days=offset-1)).isoformat(),round(sw),round(lw),round(charge,1),round(unmet)))
            for iid in self.forecast_tree.get_children(): self.forecast_tree.delete(iid)
            for row in self.forecast: self.forecast_tree.insert('','end',values=row)
            self.draw_chart()
        except ValueError as exc: messagebox.showerror('Check inputs',str(exc))

    def trend_tab(self):
        f=self.tab('Victron trends / measured data')
        ttk.Label(f,text='Import a CSV with a timestamp/date column and a solar power (W), solar energy (Wh), or battery voltage column.').pack(anchor='w')
        bar=ttk.Frame(f);bar.pack(anchor='w',pady=8)
        ttk.Button(bar,text='Import CSV',command=self.import_csv).pack(side='left',padx=4)
        ttk.Button(bar,text='Export normalized CSV',command=self.export_trends).pack(side='left',padx=4)
        self.trend_status=tk.StringVar(value='No measurements imported.')
        ttk.Label(f,textvariable=self.trend_status,wraplength=900,justify='left').pack(anchor='w',pady=5)
        self.trend_tree=ttk.Treeview(f,columns=('date','solar_wh','samples','volts'),show='headings')
        for col,title in [('date','Date'),('solar_wh','Solar energy (Wh)'),('samples','Power samples'),('volts','Mean battery voltage')]:
            self.trend_tree.heading(col,text=title);self.trend_tree.column(col,width=190)
        self.trend_tree.pack(fill='both',expand=True)
        ttk.Label(f,text='Power samples integrate over elapsed time; intervals above 2 hours are skipped. A single reading cannot determine daily energy.').pack(anchor='w',pady=4)

    def import_csv(self):
        path=filedialog.askopenfilename(filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if not path:return
        try:
            with open(path,encoding='utf-8-sig',newline='') as stream:
                reader=csv.DictReader(stream)
                headers=reader.fieldnames or []
                def pick(words):
                    return next((h for h in headers if any(w in h.lower().replace('_',' ') for w in words)),None)
                time_col=pick(('timestamp','date','time'))
                energy_col=pick(('solar energy','yield','pv energy','solar wh'))
                power_col=pick(('pv power','solar power','panel power','pv watt','solar watt'))
                volts_col=pick(('battery voltage','battery v','batt voltage'))
                if not time_col or not (energy_col or power_col or volts_col):
                    raise ValueError('Could not find time and solar energy/power or battery voltage columns. Rename CSV headers to Date, PV power, Solar energy, Battery voltage as needed.')
                records=list(reader)
            groups={}
            for record in records:
                stamp=self.parse_time(record.get(time_col,''))
                if stamp is None:continue
                def val(col):
                    try:return float(record[col].strip().replace(',','')) if col and record.get(col) and math.isfinite(float(record[col].strip().replace(',',''))) else None
                    except (ValueError,TypeError,KeyError):return None
                key=stamp.date().isoformat()
                groups.setdefault(key,[]).append((stamp,val(power_col),val(energy_col),val(volts_col)))
            summary=[]
            for day,measurements in sorted(groups.items()):
                measurements.sort(key=lambda row:row[0])
                energy_values=[x[2] for x in measurements if x[2] is not None]
                # Energy column is assumed to contain a daily cumulative yield if repeated.
                wh=max(energy_values) if energy_values else 0
                count=0
                if not energy_values:
                    for a,b in zip(measurements,measurements[1:]):
                        dt=(b[0]-a[0]).total_seconds()/3600
                        if a[1] is not None and b[1] is not None and 0 < dt <= 2:
                            wh += max(0,(a[1]+b[1])/2)*dt;count+=1
                volts=[x[3] for x in measurements if x[3] is not None]
                summary.append((day,round(wh,1) if (energy_values or count) else '',count,round(statistics.mean(volts),2) if volts else ''))
            if not summary: raise ValueError('No readable dated rows found')
            self.trends=summary
            for iid in self.trend_tree.get_children():self.trend_tree.delete(iid)
            for row in summary:self.trend_tree.insert('','end',values=row)
            valid=[float(row[1]) for row in summary if row[1]!='']
            avg=statistics.mean(valid) if valid else None
            self.trend_status.set(f'{len(summary)} days imported from {Path(path).name}. '+(f'Average measured solar: {avg:,.0f} Wh/day. ' if avg is not None else 'No complete solar energy intervals. ')+ 'Solar energy column treated as cumulative daily Wh; check the source units before applying.')
            if avg is not None:
                # Do not silently change assumptions; user can opt in.
                if messagebox.askyesno('Apply observed average?',f'Use {avg:,.0f} measured Wh/day as the solar input?\nThis sets useful sun hours to 1 and observed solar peak to the average energy value.'):
                    self.values['observed_peak'].set(f'{avg:.2f}')
                    self.values['sun_hours'].set('1')
            self.draw_chart()
        except (OSError,UnicodeError,ValueError,csv.Error) as exc:
            messagebox.showerror('CSV import',str(exc))

    @staticmethod
    def parse_time(raw):
        raw=(raw or '').strip()
        if not raw:return None
        try:return datetime.fromisoformat(raw.replace('Z','+00:00').replace(' ','T'))
        except ValueError:pass
        for fmt in ('%m/%d/%Y %H:%M:%S','%m/%d/%Y %H:%M','%m/%d/%Y','%Y-%m-%d'):
            try:return datetime.strptime(raw,fmt)
            except ValueError:pass
        return None

    def save_csv(self,rows,headers):
        if not rows:
            messagebox.showinfo('Nothing to export','Run a forecast or import measurements first.');return
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV files','*.csv')])
        if not path:return
        try:
            with open(path,'w',encoding='utf-8',newline='') as file:
                writer=csv.writer(file);writer.writerow(headers);writer.writerows(rows)
        except OSError as exc:messagebox.showerror('Export failed',str(exc))

    def export_forecast(self):self.save_csv(self.forecast,['scenario','date','solar_dc_wh','load_ac_wh','end_soc_percent','unserved_ac_wh'])
    def export_trends(self):self.save_csv(self.trends,['date','solar_wh','integrated_intervals','mean_battery_voltage'])

    def chart_tab(self):
        f=self.tab('Charts')
        ttk.Label(f,text='Charts update after forecasts and CSV imports. Matplotlib is optional; CSV export works without it.').pack(anchor='w')
        self.chart_area=ttk.Frame(f);self.chart_area.pack(fill='both',expand=True)
        self.chart_canvas=None
        self.draw_chart()

    def draw_chart(self):
        if not hasattr(self,'chart_area'):return
        for child in self.chart_area.winfo_children():child.destroy()
        if not self.forecast and not self.trends:
            ttk.Label(self.chart_area,text='Run scenarios or import trend data to see charts.').pack(pady=30);return
        try:
            from matplotlib.figure import Figure
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            ttk.Label(self.chart_area,text='Install matplotlib for charts: python3 -m pip install matplotlib').pack(pady=30);return
        fig=Figure(figsize=(9,5),dpi=95)
        ax=fig.add_subplot(111)
        if self.forecast:
            labels=list(dict.fromkeys(row[0] for row in self.forecast))
            for label in labels:
                rows=[r for r in self.forecast if r[0]==label]
                ax.plot([i+1 for i in range(len(rows))],[r[4] for r in rows],label=label)
            ax.set_ylabel('Battery charge (%)');ax.set_xlabel('Forecast day')
            ax.legend(fontsize=8)
        else:
            data=[r for r in self.trends if r[1]!='']
            ax.bar([r[0] for r in data],[float(r[1]) for r in data])
            ax.set_ylabel('Solar energy (Wh)');ax.tick_params(axis='x',labelrotation=45)
        ax.grid(alpha=.3);fig.tight_layout()
        canvas=FigureCanvasTkAgg(fig,master=self.chart_area)
        canvas.draw();canvas.get_tk_widget().pack(fill='both',expand=True)
        self.chart_canvas=canvas


if __name__=='__main__':
    root=tk.Tk()
    SolarApp(root)
    root.mainloop()
