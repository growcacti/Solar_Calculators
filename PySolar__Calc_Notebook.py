import tkinter as tk
from tkinter import ttk
from math import ceil

class SolarCalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Solar Calculator Suite")
        self.root.geometry("800x600")

        # Create notebook
        notebook = ttk.Notebook(root)
        notebook.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")

        # Create tabs
        self.create_kwh_tab(notebook)
        self.create_savings_tab(notebook)
        self.create_payback_tab(notebook)
        self.create_energy_tab(notebook)
        self.create_battery_tab(notebook)
        self.create_inverter_tab(notebook)

    def create_kwh_tab(self, notebook):
        """Tab for kWh Calculator."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="kWh Calculator")

        tk.Label(tab, text="Annual Electricity Needs (kWh):").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.kwh_entry = tk.Entry(tab, bd=12,bg="azure")
        self.kwh_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(tab, text="Peak Sun Hours (hours/day):").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.sun_hours_entry = tk.Entry(tab, bd=12,bg="azure")
        self.sun_hours_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate", command=self.calculate_kwh).grid(row=2, column=0, columnspan=2, pady=10)

        self.kwh_result_label = tk.Label(tab, text="")
        self.kwh_result_label.grid(row=3, column=0, columnspan=2, pady=5)

    def calculate_kwh(self):
        try:
            annual_kwh = float(self.kwh_entry.get())
            sun_hours = float(self.sun_hours_entry.get())
            solar_size = round(annual_kwh / (sun_hours * 365), 2)
            self.kwh_result_label.config(text=f"Solar System Size Needed: {solar_size} kW")
        except ValueError:
            self.kwh_result_label.config(text="Invalid input. Please enter numeric values.")

    def create_savings_tab(self, notebook):
        """Tab for Savings Calculator."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="Savings Calculator")

        tk.Label(tab, text="Solar System Size (kW):").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.size_entry = tk.Entry(tab, bd=12,bg="azure")
        self.size_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(tab, text="Peak Sun Hours (hours/day):").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.sun_hours_entry2 = tk.Entry(tab, bd=12,bg="azure")
        self.sun_hours_entry2.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(tab, text="Electricity Cost ($/kWh):").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.cost_entry = tk.Entry(tab, bd=12,bg="azure")
        self.cost_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate", command=self.calculate_savings).grid(row=3, column=0, columnspan=2, pady=10)

        self.savings_result_label = tk.Label(tab, text="")
        self.savings_result_label.grid(row=4, column=0, columnspan=2, pady=5)

    def calculate_savings(self):
        try:
            solar_size = float(self.size_entry.get())
            sun_hours = float(self.sun_hours_entry2.get())
            electricity_cost = float(self.cost_entry.get())
            annual_savings = round(solar_size * sun_hours * 365 * electricity_cost, 2)
            self.savings_result_label.config(text=f"Annual Savings: ${annual_savings}")
        except ValueError:
            self.savings_result_label.config(text="Invalid input. Please enter numeric values.")

    def create_payback_tab(self, notebook):
        """Tab for Payback Calculator."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="Payback Calculator")

        tk.Label(tab, text="Cost of Solar System ($):").grid(row=0, column=0, padx=10, pady=5, sticky='w')
        self.cost_system_entry = tk.Entry(tab, bd=12,bg="azure")
        self.cost_system_entry.grid(row=0, column=1, padx=10, pady=5)

        tk.Label(tab, text="Rebates ($):").grid(row=1, column=0, padx=10, pady=5, sticky='w')
        self.rebate_entry = tk.Entry(tab, bd=12,bg="azure")
        self.rebate_entry.grid(row=1, column=1, padx=10, pady=5)

        tk.Label(tab, text="Annual Savings ($):").grid(row=2, column=0, padx=10, pady=5, sticky='w')
        self.payback_savings_entry = tk.Entry(tab, bd=12,bg="azure")
        self.payback_savings_entry.grid(row=2, column=1, padx=10, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate", command=self.calculate_payback).grid(row=3, column=0, columnspan=2, pady=10)

        self.payback_result_label = tk.Label(tab, text="")
        self.payback_result_label.grid(row=4, column=0, columnspan=2, pady=5)

    def calculate_payback(self):
        try:
            system_cost = float(self.cost_system_entry.get())
            rebates = float(self.rebate_entry.get())
            annual_savings = float(self.payback_savings_entry.get())
            net_cost = system_cost - rebates
            payback_years = round(net_cost / annual_savings, 2)
            self.payback_result_label.config(text=f"Payback Period: {payback_years} years")
        except ValueError:
            self.payback_result_label.config(text="Invalid input. Please enter numeric values.")

    def create_energy_tab(self, notebook):
        """Tab for calculating solar panel needs."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="Solar Panel Calculator")

        tk.Label(tab, text="Daily Energy Consumption (Wh or kWh):").grid(row=0, column=0, sticky="w", pady=5)
        self.daily_energy_entry = tk.Entry(tab, bd=12,bg="azure")
        self.daily_energy_entry.grid(row=0, column=1, pady=5)

        tk.Label(tab, text="Peak Sunlight Hours (hours):").grid(row=1, column=0, sticky="w", pady=5)
        self.sunlight_hours_entry = tk.Entry(tab, bd=12,bg="azure")
        self.sunlight_hours_entry.grid(row=1, column=1, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate Solar Panel Needs", command=self.calculate_solar_panels).grid(
            row=2, column=0, columnspan=2, pady=10
        )

        self.solar_panel_result = tk.Label(tab, text="")
        self.solar_panel_result.grid(row=3, column=0, columnspan=2, pady=10)

    def calculate_solar_panels(self):
        try:
            daily_energy = float(self.daily_energy_entry.get())
            sunlight_hours = float(self.sunlight_hours_entry.get())
            panel_output = ceil(daily_energy / sunlight_hours * 1.25)  # Adding 25% inefficiency buffer
            self.solar_panel_result.config(text=f"Required Solar Panel Output: {panel_output} W")
        except ValueError:
            self.solar_panel_result.config(text="Invalid input. Please enter numbers only.")

    def create_battery_tab(self, notebook):
        """Tab for calculating battery bank size."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="Battery Bank Calculator")

        tk.Label(tab, text="Daily Energy Consumption (Wh):").grid(row=0, column=0, sticky="w", pady=5)
        self.battery_energy_entry = tk.Entry(tab, bd=12,bg="azure")
        self.battery_energy_entry.grid(row=0, column=1, pady=5)

        tk.Label(tab, text="Days of Autonomy:").grid(row=1, column=0, sticky="w", pady=5)
        self.autonomy_days_entry = tk.Entry(tab, bd=12,bg="azure")
        self.autonomy_days_entry.grid(row=1, column=1, pady=5)

        tk.Label(tab, text="Depth of Discharge (%):").grid(row=2, column=0, sticky="w", pady=5)
        self.dod_entry = tk.Entry(tab, bd=12,bg="azure")
        self.dod_entry.grid(row=2, column=1, pady=5)

        tk.Label(tab, text="System Voltage (V):").grid(row=3, column=0, sticky="w", pady=5)
        self.voltage_entry = tk.Entry(tab, bd=12,bg="azure")
        self.voltage_entry.grid(row=3, column=1, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate Battery Bank", command=self.calculate_battery_bank).grid(
            row=4, column=0, columnspan=2, pady=10
        )

        self.battery_result = tk.Label(tab, text="")
        self.battery_result.grid(row=5, column=0, columnspan=2, pady=10)

    def calculate_battery_bank(self):
        try:
            energy = float(self.battery_energy_entry.get())
            days = int(self.autonomy_days_entry.get())
            dod = float(self.dod_entry.get()) / 100
            voltage = int(self.voltage_entry.get())

            battery_capacity = ceil((energy * days) / (dod * voltage))
            self.battery_result.config(text=f"Battery Bank Capacity: {battery_capacity} Ah")
        except ValueError:
            self.battery_result.config(text="Invalid input. Please enter numbers only.")

    def create_inverter_tab(self, notebook):
        """Tab for inverter size calculation."""
        tab = tk.Frame(notebook, bg="lavender",bd=5)
        notebook.add(tab, text="Inverter Size Calculator")

        tk.Label(tab, text="Peak Demand (W):").grid(row=0, column=0, sticky="w", pady=5)
        self.peak_demand_entry = tk.Entry(tab, bd=12,bg="azure")
        self.peak_demand_entry.grid(row=0, column=1, pady=5)

        tk.Button(tab,bd=7,bg="bisque", text="Calculate Inverter Size", command=self.calculate_inverter_size).grid(
            row=1, column=0, columnspan=2, pady=10
        )

        self.inverter_result = tk.Label(tab, text="")
        self.inverter_result.grid(row=2, column=0, columnspan=2, pady=10)

    def calculate_inverter_size(self):
        try:
            peak_demand = float(self.peak_demand_entry.get())
            inverter_size = ceil(peak_demand * 1.2)  # Adding 20% buffer
            self.inverter_result.config(text=f"Recommended Inverter Size: {inverter_size} W")
        except ValueError:
            self.inverter_result.config(text="Invalid input. Please enter numbers only.")


if __name__ == "__main__":
    root = tk.Tk()
    app = SolarCalculatorApp(root)
    root.mainloop()
