import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import sys
import io
import contextlib
from pathlib import Path
import pytest

def get_base_dir():
    """Возвращает корневую директорию проекта (работает и в .exe)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    else:
        return Path(__file__).parent.parent

class TestRunnerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Test Runner")
        self.root.geometry("900x700")

        self.base_dir = get_base_dir()
        if str(self.base_dir) not in sys.path:
            sys.path.insert(0, str(self.base_dir))

        self.test_vars = {}
        self.all_tests = []
        self.filtered_tests = []
        self.available_markers = ["all", "slow", "fast", "integration"]
        self.current_marker = tk.StringVar(value="all")

        self.discover_tests()
        self.create_widgets()

    def discover_tests(self):
        """Получает список всех тестов через pytest.main --collect-only."""
        tests_dir = self.base_dir / "tests"
        if not tests_dir.exists():
            self.all_tests = []
            return

        capture = io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            pytest.main([str(tests_dir), "--collect-only", "-q"])

        output = capture.getvalue()
        test_names = set()
        for line in output.splitlines():
            if "::" not in line:
                continue
            if "[" in line:
                line = line.split("[")[0]
            parts = line.split("::")
            if len(parts) >= 2:
                module_file = parts[0]
                test_func = parts[1]
                module_name = Path(module_file).stem
                full_name = f"{module_name}.{test_func}"
                test_names.add(full_name)
        self.all_tests = list(test_names)

    def _get_markers_for_test(self, test_name):
        # Заглушка для маркеров
        if "slow" in test_name.lower():
            return ["slow"]
        elif "fast" in test_name.lower():
            return ["fast"]
        elif "integration" in test_name.lower():
            return ["integration"]
        else:
            return ["fast"]

    def filter_tests_by_marker(self):
        marker = self.current_marker.get()
        if marker == "all":
            self.filtered_tests = self.all_tests.copy()
        else:
            self.filtered_tests = [name for name in self.all_tests if marker in self._get_markers_for_test(name)]
        self.refresh_test_list()

    def refresh_test_list(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.test_vars.clear()
        for test_name in self.filtered_tests:
            var = tk.BooleanVar(value=True)
            self.test_vars[test_name] = var
            cb = ttk.Checkbutton(self.scrollable_frame, text=test_name, variable=var)
            cb.pack(anchor="w")
            cb.bind("<Double-Button-1>", lambda e, name=test_name: self.run_single_test(name))

    def create_widgets(self):
        top_frame = ttk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=5)
        ttk.Label(top_frame, text="Фильтр по маркеру:").pack(side="left", padx=5)
        marker_combo = ttk.Combobox(top_frame, textvariable=self.current_marker, values=self.available_markers, state="readonly")
        marker_combo.pack(side="left", padx=5)
        marker_combo.bind("<<ComboboxSelected>>", lambda e: self.filter_tests_by_marker())
        ttk.Button(top_frame, text="Применить фильтр", command=self.filter_tests_by_marker).pack(side="left", padx=5)

        select_frame = ttk.LabelFrame(self.root, text="Выберите тесты для запуска")
        select_frame.pack(fill="both", expand=True, padx=10, pady=5)

        canvas = tk.Canvas(select_frame)
        scrollbar = ttk.Scrollbar(select_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)
        self.run_btn = ttk.Button(btn_frame, text="Запустить выбранные тесты", command=self.run_selected_tests)
        self.run_btn.pack(side="left", padx=5)
        self.select_all_btn = ttk.Button(btn_frame, text="Выбрать все", command=self.select_all)
        self.select_all_btn.pack(side="left", padx=5)
        self.deselect_all_btn = ttk.Button(btn_frame, text="Снять все", command=self.deselect_all)
        self.deselect_all_btn.pack(side="left", padx=5)
        self.save_log_btn = ttk.Button(btn_frame, text="Сохранить лог", command=self.save_log)
        self.save_log_btn.pack(side="left", padx=5)

        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="indeterminate")
        self.progress.pack(pady=5)

        self.log = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=80, height=20)
        self.log.pack(fill="both", expand=True, padx=10, pady=5)
        self.log.tag_config("PASS", foreground="green")
        self.log.tag_config("FAIL", foreground="red")
        self.log.tag_config("TIME", foreground="blue")

        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.filter_tests_by_marker()

    def select_all(self):
        for var in self.test_vars.values():
            var.set(True)

    def deselect_all(self):
        for var in self.test_vars.values():
            var.set(False)

    def save_log(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.log.get(1.0, tk.END))
            self.status_var.set(f"Лог сохранён в {file_path}")

    def run_selected_tests(self):
        selected = [name for name, var in self.test_vars.items() if var.get()]
        if not selected:
            messagebox.showwarning("Нет тестов", "Не выбрано ни одного теста.")
            return
        self._run_tests(selected)

    def run_single_test(self, test_name):
        self._run_tests([test_name])

    def _run_tests(self, test_names):
        self.run_btn.config(state="disabled")
        self.select_all_btn.config(state="disabled")
        self.deselect_all_btn.config(state="disabled")
        self.save_log_btn.config(state="disabled")
        self.log.delete(1.0, tk.END)
        self.progress.start(10)
        self.status_var.set("Запуск тестов...")

        thread = threading.Thread(target=self._run_tests_thread, args=(test_names,))
        thread.daemon = True
        thread.start()

    def _run_tests_thread(self, test_names):
        tests_dir = self.base_dir / "tests"
        args = []
        for full_name in test_names:
            module_name, func_name = full_name.split(".", 1)
            module_path = tests_dir / f"{module_name}.py"
            if module_path.exists():
                args.append(f"{module_path}::{func_name}")
            else:
                self.root.after(0, lambda m=module_name: self.log.insert(tk.END, f"Ошибка: модуль {m} не найден\n", "ERROR"))

        capture = io.StringIO()
        with contextlib.redirect_stdout(capture), contextlib.redirect_stderr(capture):
            exit_code = pytest.main(args + ["-v", "--durations=0"], plugins=[])

        output = capture.getvalue()
        for line in output.splitlines():
            line = line.rstrip()
            if (line.startswith("=") or line.startswith("-") or
                line.startswith("platform") or "test session starts" in line or
                line.startswith("rootdir") or line.startswith("collected") or
                line.startswith("plugins") or line.strip() == ""):
                continue
            self.root.after(0, self._append_log_line, line)

        self.root.after(0, self._tests_finished, exit_code)

    def _append_log_line(self, line):
        if "PASSED" in line:
            self.log.insert(tk.END, line + "\n", "PASS")
        elif "FAILED" in line or "ERROR" in line:
            self.log.insert(tk.END, line + "\n", "FAIL")
        elif "seconds" in line and "durations" not in line:
            self.log.insert(tk.END, line + "\n", "TIME")
        else:
            self.log.insert(tk.END, line + "\n")
        self.log.see(tk.END)

    def _tests_finished(self, exit_code):
        self.progress.stop()
        self.progress["value"] = 100
        if exit_code == 0:
            self.status_var.set("Тесты завершены успешно")
        else:
            self.status_var.set("Тесты завершены с ошибками")
        self.run_btn.config(state="normal")
        self.select_all_btn.config(state="normal")
        self.deselect_all_btn.config(state="normal")
        self.save_log_btn.config(state="normal")

if __name__ == "__main__":
    root = tk.Tk()
    app = TestRunnerApp(root)
    root.mainloop()