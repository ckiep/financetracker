import tkinter as tk
from tkinter import simpledialog, messagebox
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


class DataTable(tk.Frame):
    def __init__(self, master, num_rows, num_columns):
        super().__init__(master)
        self.num_rows = num_rows
        self.num_columns = num_columns
        self.create_widgets()

    def create_widgets(self):
        # Create labels for columns
        column_labels = ["Y", "K", "L"]
        for i, label_text in enumerate(column_labels):
            label = tk.Label(self, text=label_text)
            label.grid(row=0, column=i + 1, padx=5, pady=5)

        # Create entries for data input
        self.entries = []
        for i in range(self.num_rows):
            row_entries = []
            for j in range(self.num_columns):
                entry = tk.Entry(self)
                entry.grid(row=i + 1, column=j + 1, padx=5, pady=5)
                row_entries.append(entry)
            self.entries.append(row_entries)

    def get_data(self):
        data = []
        for i in range(self.num_rows):
            row_data = []
            for j in range(self.num_columns):
                value = self.entries[i][j].get()
                if value:
                    row_data.append(float(value))
                else:
                    messagebox.showerror("Error", "Please fill all cells.")
                    return None
            data.append(row_data)
        return data


class CobbDouglasCalculator:
    def __init__(self, master):
        self.master = master
        self.master.title("Cobb-Douglas Calculator")

        self.num_values_label = tk.Label(master, text="Number of Values for Each Category:")
        self.num_values_label.grid(row=0, column=0, sticky="e")

        self.num_values_entry = tk.Entry(master)
        self.num_values_entry.grid(row=0, column=1)

        self.create_data_table_button = tk.Button(master, text="Create Table", command=self.create_data_table)
        self.create_data_table_button.grid(row=1, column=0, columnspan=2)

        self.calculate_button = tk.Button(master, text="Calculate", command=self.calculate)
        self.calculate_button.grid(row=2, column=0, columnspan=2)

        self.clear_plot_button = tk.Button(master, text="Clear Plot", command=self.clear_plot)
        self.clear_plot_button.grid(row=3, column=0, columnspan=2)

        self.data_table_frame = tk.Frame(master)
        self.data_table_frame.grid(row=4, column=0, rowspan=4)

        self.figure = None
        self.plot_frame = tk.Frame(master)
        self.plot_frame.grid(row=4, column=1, rowspan=4)

        self.plot_canvas = tk.Canvas(self.plot_frame)
        self.plot_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.plot_frame, orient=tk.VERTICAL, command=self.plot_canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.plot_canvas.config(yscrollcommand=self.scrollbar.set)
        self.plot_canvas.bind('<Configure>', self._on_configure)
        self.plot_canvas.bind_all("<MouseWheel>", self._on_mousewheel)

    def _on_configure(self, event):
        self.plot_canvas.configure(scrollregion=self.plot_canvas.bbox('all'))

    def _on_mousewheel(self, event):
        self.plot_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def create_data_table(self):
        num_values = self.num_values_entry.get()
        try:
            num_values = int(num_values)
            self.data_table = DataTable(self.data_table_frame, num_values, 3)
            self.data_table.pack()
        except ValueError:
            messagebox.showerror("Error", "Please enter a valid number for the count.")

    def calculate(self):
        try:
            data = self.data_table.get_data()
            if data is None:
                return
            Y_values = [row[0] for row in data]
            K_values = [row[1] for row in data]
            L_values = [row[2] for row in data]
            t_values = list(range(len(data)))

            log_Y_values = self.log_values(Y_values)
            log_N_values = self.log_values(K_values)
            log_D_values = self.log_values(L_values)

            A, alpha, beta, lambda_val = self.find_coefficients(log_Y_values, log_N_values, log_D_values, t_values)

            self.print_coefficients(A, alpha, beta, lambda_val)

            estimates = self.calculate_estimates(A, alpha, beta, lambda_val, K_values, L_values, t_values)
            discontinuity_point = self.find_discontinuity_point(estimates)

            self.print_estimates(Y_values, K_values, L_values, t_values, A, alpha, beta, lambda_val)
            self.plot_comparison(Y_values, estimates, discontinuity_point)


        except AttributeError:
            messagebox.showerror("Error", "Please create a table first.")

    def clear_plot(self):
        if hasattr(self, 'figure'):
            plt.close(self.figure)
        if hasattr(self, 'plot_canvas'):
            self.plot_canvas.destroy()
        self.plot_canvas = tk.Canvas(self.plot_frame, width=400, height=300)
        self.plot_canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.figure = None

    def log_values(self, values):
        logarithms = [math.log(value) for value in values]
        return logarithms

    def find_coefficients(self, Y_values, N_values, D_values, t_values):
        X = np.array([N_values, D_values, t_values, np.ones(len(N_values))]).T
        y = np.array(Y_values)
        coefficients, residuals, _, _ = np.linalg.lstsq(X, y, rcond=None)
        alpha, beta, lambda_val, A = coefficients
        return A, alpha, beta, lambda_val

    def print_coefficients(self, A, alpha, beta, lambda_val):
        coefficients_text = f"A: {math.exp(A)}, alpha: {alpha}, beta: {beta}, lambda: {lambda_val}"

        if hasattr(self, 'coeff_label'):
            self.coeff_label.destroy()

        self.coeff_label = tk.Label(self.plot_frame, text=coefficients_text)
        self.coeff_label.pack()
        messagebox.showinfo("Coefficients", f"A: {math.exp(A)}, alpha: {alpha}, beta: {beta}, lambda: {lambda_val}")

    def calculate_estimates(self, A, alpha, beta, lambda_val, N_values, D_values, t_values):
        estimates = [math.exp(A + alpha * math.log(N) + beta * math.log(D) + lambda_val * t) for N, D, t in
                     zip(N_values, D_values, t_values)]
        return estimates

    def print_estimates(self, Y_values, N_values, D_values, t_values, A, alpha, beta, lambda_val):
        estimates = self.calculate_estimates(A, alpha, beta, lambda_val, N_values, D_values, t_values)
        result = "\n".join([f"Category {i + 1}: {estimate}" for i, estimate in enumerate(estimates)])
        messagebox.showinfo("Estimates", "Estimated values:\n" + result)

    def find_discontinuity_point(self, estimates):
        max_difference = 0
        discontinuity_point = None
        for i in range(1, len(estimates)):
            difference = abs(estimates[i] - estimates[i - 1])
            if difference > max_difference:
                max_difference = difference
                discontinuity_point = i
        return discontinuity_point

    def plot_comparison(self, Y_values, estimates, discontinuity_point):
        if hasattr(self, 'figure') and self.figure:
            plt.close(self.figure)
        self.figure, ax = plt.subplots(figsize=(6, 4))
        ax.plot(Y_values, label='Given Y values')
        ax.plot(estimates, label='Calculated Y values')
        ax.set_xlabel('Category')
        ax.set_ylabel('Y Value')
        ax.set_title('Comparison of Given and Calculated Y Values')
        ax.legend()

        if discontinuity_point is not None:
            ax.annotate(f'Discontinuity at category {discontinuity_point + 1}',
                        xy=(discontinuity_point, estimates[discontinuity_point]),
                        xytext=(discontinuity_point + 1, estimates[discontinuity_point] - 5),
                        arrowprops=dict(facecolor='black', arrowstyle='->'),
                        fontsize=10)

        canvas = FigureCanvasTkAgg(self.figure, master=self.plot_canvas)
        canvas.draw()
        canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)


def main():
    root = tk.Tk()
    app = CobbDouglasCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
