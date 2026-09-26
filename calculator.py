"""A desktop scientific calculator with a built-in function graphing view.

Run with ``python calculator.py``.  The calculation engine deliberately uses a
restricted AST evaluator instead of ``eval`` so expressions entered in the UI
cannot execute Python code.
"""

from __future__ import annotations

import ast
import math
import re
import tkinter as tk
from dataclasses import dataclass
from tkinter import messagebox, ttk
from typing import Callable


class CalculationError(ValueError):
    """Raised when an expression is invalid or cannot be calculated."""


@dataclass
class CalculatorEngine:
    """Safe, reusable expression evaluator used by the calculator and graph."""

    degrees: bool = True
    answer: float = 0.0

    def _angle_in(self, value: float) -> float:
        return math.radians(value) if self.degrees else value

    def _angle_out(self, value: float) -> float:
        return math.degrees(value) if self.degrees else value

    def functions(self) -> dict[str, Callable[[float], float]]:
        return {
            "sin": lambda x: math.sin(self._angle_in(x)),
            "cos": lambda x: math.cos(self._angle_in(x)),
            "tan": lambda x: math.tan(self._angle_in(x)),
            "asin": lambda x: self._angle_out(math.asin(x)),
            "acos": lambda x: self._angle_out(math.acos(x)),
            "atan": lambda x: self._angle_out(math.atan(x)),
            "sqrt": math.sqrt,
            "log": math.log10,
            "ln": math.log,
            "abs": abs,
            "floor": math.floor,
            "ceil": math.ceil,
            "fact": lambda x: math.factorial(self._integer(x, "factorial")),
        }

    @staticmethod
    def _integer(value: float, operation: str) -> int:
        if not float(value).is_integer() or value < 0:
            raise CalculationError(f"{operation.title()} requires a non-negative integer")
        return int(value)

    def evaluate(self, expression: str, x: float | None = None) -> float:
        """Evaluate an arithmetic expression and save it as the current answer."""
        expression = expression.strip().replace("^", "**").replace("π", "pi")
        if not expression:
            raise CalculationError("Enter an expression")
        # A calculator input may say 2x or 2(3); make those familiar forms work.
        expression = re.sub(r"(?<=[0-9)])(?=x|pi|e|[a-zA-Z](?=\())", "*", expression)
        expression = re.sub(r"(?<=[0-9xpie)])(?=\()", "*", expression)
        expression = re.sub(r"(?<=[0-9)xpie])(?=(?:sin|cos|tan|asin|acos|atan|sqrt|log|ln|abs|floor|ceil|fact)\()", "*", expression)
        try:
            tree = ast.parse(expression, mode="eval")
            result = self._evaluate_node(tree.body, x)
            result = float(result)
            if not math.isfinite(result):
                raise CalculationError("Result is not a finite number")
        except (ArithmeticError, OverflowError, ValueError, SyntaxError) as error:
            raise CalculationError("Invalid expression") from error
        self.answer = result
        return result

    def _evaluate_node(self, node: ast.AST, x: float | None) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.Name):
            constants = {"pi": math.pi, "e": math.e, "ans": self.answer}
            if x is not None:
                constants["x"] = x
            if node.id in constants:
                return constants[node.id]
            raise CalculationError(f"Unknown value: {node.id}")
        if isinstance(node, ast.UnaryOp) and type(node.op) in (ast.UAdd, ast.USub):
            value = self._evaluate_node(node.operand, x)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left, right = self._evaluate_node(node.left, x), self._evaluate_node(node.right, x)
            operations = {
                ast.Add: lambda: left + right, ast.Sub: lambda: left - right,
                ast.Mult: lambda: left * right, ast.Div: lambda: left / right,
                ast.Pow: lambda: left ** right, ast.Mod: lambda: left % right,
            }
            operation = operations.get(type(node.op))
            if operation:
                return operation()
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and len(node.args) == 1:
            function = self.functions().get(node.func.id)
            if function:
                return function(self._evaluate_node(node.args[0], x))
        raise CalculationError("Unsupported expression")


def display_number(value: float) -> str:
    """Format a result cleanly without hiding useful precision."""
    return str(int(value)) if value.is_integer() else f"{value:.12g}"


class CalculatorApp(tk.Tk):
    """Tkinter user interface for standard, scientific, and graph functions."""

    def __init__(self) -> None:
        super().__init__()
        self.title("Python Scientific Calculator")
        self.minsize(760, 600)
        self.configure(bg="#172033")
        self.engine, self.memory, self.history = CalculatorEngine(), 0.0, []
        self.expression = tk.StringVar()
        self.status = tk.StringVar(value="Ready")
        self._build_ui()
        self.bind("<Return>", lambda _: self.calculate())
        self.bind("<Escape>", lambda _: self.clear())
        self.bind_all("<Key>", self._key_input)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TNotebook", background="#172033", borderwidth=0)
        style.configure("TNotebook.Tab", background="#273551", foreground="white", padding=(18, 8))
        style.map("TNotebook.Tab", background=[("selected", "#415a8a")])
        book = ttk.Notebook(self)
        book.pack(fill="both", expand=True, padx=14, pady=14)
        calculator, graph = tk.Frame(book, bg="#172033"), tk.Frame(book, bg="#172033")
        book.add(calculator, text="Calculator")
        book.add(graph, text="Graph")
        self._build_calculator(calculator)
        self._build_graph(graph)

    def _build_calculator(self, parent: tk.Frame) -> None:
        heading = tk.Frame(parent, bg="#172033")
        heading.pack(fill="x", padx=12, pady=(12, 3))
        tk.Label(heading, text="SCIENTIFIC CALCULATOR", bg="#172033", fg="#a9c5ff", font=("Arial", 11, "bold")).pack(side="left")
        tk.Button(heading, text="History", command=self.show_history, bg="#273551", fg="white", relief="flat").pack(side="right")
        entry = tk.Entry(parent, textvariable=self.expression, justify="right", font=("Consolas", 26), bg="#0d1422", fg="white", insertbackground="white", relief="flat")
        entry.pack(fill="x", padx=12, ipady=15)
        entry.focus_set()
        tk.Label(parent, textvariable=self.status, anchor="e", bg="#172033", fg="#a9c5ff").pack(fill="x", padx=15, pady=5)
        body = tk.Frame(parent, bg="#172033")
        body.pack(fill="both", expand=True, padx=12, pady=(2, 12))
        keys = [
            ("MC", self.memory_clear), ("MR", self.memory_recall), ("M+", lambda: self.memory_add(1)), ("M−", lambda: self.memory_add(-1)), ("⌫", self.backspace), ("C", self.clear),
            ("sin", lambda: self.insert("sin(")), ("cos", lambda: self.insert("cos(")), ("tan", lambda: self.insert("tan(")), ("log", lambda: self.insert("log(")), ("ln", lambda: self.insert("ln(")), ("MS", self.memory_store),
            ("asin", lambda: self.insert("asin(")), ("acos", lambda: self.insert("acos(")), ("atan", lambda: self.insert("atan(")), ("√", lambda: self.insert("sqrt(")), ("x²", lambda: self.insert("^2")), ("÷", lambda: self.insert("/")),
            ("π", lambda: self.insert("π")), ("e", lambda: self.insert("e")), ("xʸ", lambda: self.insert("^")), ("(", lambda: self.insert("(")), (")", lambda: self.insert(")")), ("×", lambda: self.insert("*")),
            ("7", lambda: self.insert("7")), ("8", lambda: self.insert("8")), ("9", lambda: self.insert("9")), ("%", self.percent), ("fact", lambda: self.insert("fact(")), ("−", lambda: self.insert("-")),
            ("4", lambda: self.insert("4")), ("5", lambda: self.insert("5")), ("6", lambda: self.insert("6")), ("Ans", lambda: self.insert("ans")), ("DEG", self.toggle_angle), ("+", lambda: self.insert("+")),
            ("1", lambda: self.insert("1")), ("2", lambda: self.insert("2")), ("3", lambda: self.insert("3")), ("0", lambda: self.insert("0")), (".", lambda: self.insert(".")), ("=", self.calculate),
        ]
        for index, (label, command) in enumerate(keys):
            row, column = divmod(index, 6)
            button = tk.Button(body, text=label, command=command, font=("Arial", 12, "bold"), relief="flat", bd=0, bg="#293956", fg="white", activebackground="#5676ae", activeforeground="white")
            button.grid(row=row, column=column, sticky="nsew", padx=3, pady=3, ipady=12)
        for index in range(6): body.columnconfigure(index, weight=1)
        for index in range(7): body.rowconfigure(index, weight=1)

    def _build_graph(self, parent: tk.Frame) -> None:
        controls = tk.Frame(parent, bg="#172033")
        controls.pack(fill="x", padx=12, pady=12)
        self.function, self.x_min, self.x_max = tk.StringVar(value="sin(x)"), tk.StringVar(value="-10"), tk.StringVar(value="10")
        for label, variable, width in (("f(x) =", self.function, 30), ("x min", self.x_min, 8), ("x max", self.x_max, 8)):
            tk.Label(controls, text=label, bg="#172033", fg="white").pack(side="left", padx=(0, 5))
            tk.Entry(controls, textvariable=variable, width=width, font=("Consolas", 12), bg="#0d1422", fg="white", insertbackground="white").pack(side="left", padx=(0, 12), ipady=5)
        tk.Button(controls, text="Plot graph", command=self.plot, bg="#4b75bb", fg="white", relief="flat", font=("Arial", 11, "bold"), padx=15).pack(side="left")
        self.canvas = tk.Canvas(parent, bg="#0d1422", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.canvas.bind("<Configure>", lambda _: self.plot())

    def insert(self, text: str) -> None: self.expression.set(self.expression.get() + text)
    def clear(self) -> None: self.expression.set(""); self.status.set("Cleared")
    def backspace(self) -> None: self.expression.set(self.expression.get()[:-1])
    def calculate(self) -> None:
        try:
            source = self.expression.get(); result = self.engine.evaluate(source)
            self.history.append((source, result)); self.expression.set(display_number(result)); self.status.set(f"Answer: {display_number(result)}")
        except CalculationError as error: self.status.set(str(error)); self.bell()
    def percent(self) -> None:
        try: self.expression.set(display_number(self.engine.evaluate(self.expression.get()) / 100))
        except CalculationError as error: self.status.set(str(error))
    def memory_clear(self) -> None: self.memory = 0.0; self.status.set("Memory cleared")
    def memory_store(self) -> None:
        try: self.memory = self.engine.evaluate(self.expression.get()); self.status.set(f"Memory: {display_number(self.memory)}")
        except CalculationError as error: self.status.set(str(error))
    def memory_recall(self) -> None: self.insert(display_number(self.memory)); self.status.set("Memory recalled")
    def memory_add(self, direction: int) -> None:
        try: self.memory += direction * self.engine.evaluate(self.expression.get()); self.status.set(f"Memory: {display_number(self.memory)}")
        except CalculationError as error: self.status.set(str(error))
    def toggle_angle(self) -> None:
        self.engine.degrees = not self.engine.degrees; self.status.set("Degree mode" if self.engine.degrees else "Radian mode")
    def show_history(self) -> None:
        window = tk.Toplevel(self); window.title("Calculation history"); window.configure(bg="#172033"); window.geometry("430x330")
        history = tk.Listbox(window, bg="#0d1422", fg="white", font=("Consolas", 12), borderwidth=0)
        history.pack(fill="both", expand=True, padx=12, pady=12)
        for source, result in reversed(self.history): history.insert("end", f"{source} = {display_number(result)}")
        if not self.history: history.insert("end", "No calculations yet")
    def _key_input(self, event: tk.Event) -> None:
        if event.char in "0123456789.+-*/^()": self.insert(event.char)
    def plot(self) -> None:
        canvas = self.canvas
        canvas.delete("all")
        try:
            low, high = float(self.x_min.get()), float(self.x_max.get())
            if low >= high: raise ValueError
        except ValueError:
            return
        width, height = max(canvas.winfo_width(), 2), max(canvas.winfo_height(), 2)
        values = []
        for pixel in range(width):
            x = low + (high - low) * pixel / (width - 1)
            try: values.append((pixel, self.engine.evaluate(self.function.get(), x)))
            except CalculationError: values.append((pixel, None))
        visible = [y for _, y in values if y is not None and abs(y) < 1e6]
        if not visible: canvas.create_text(width / 2, height / 2, text="No plottable values", fill="white", font=("Arial", 14)); return
        y_low, y_high = min(visible), max(visible)
        if y_low == y_high: y_low, y_high = y_low - 1, y_high + 1
        pad = (y_high - y_low) * .1; y_low -= pad; y_high += pad
        x_zero = (0 - low) / (high - low) * width; y_zero = height - (0 - y_low) / (y_high - y_low) * height
        canvas.create_line(0, y_zero, width, y_zero, fill="#50627f"); canvas.create_line(x_zero, 0, x_zero, height, fill="#50627f")
        points = []
        for pixel, y in values:
            if y is None or y < y_low - (y_high-y_low) or y > y_high + (y_high-y_low):
                if len(points) > 1: canvas.create_line(*points, fill="#69a6ff", width=2, smooth=True)
                points = []; continue
            points.extend((pixel, height - (y - y_low) / (y_high - y_low) * height))
        if len(points) > 1: canvas.create_line(*points, fill="#69a6ff", width=2, smooth=True)
        canvas.create_text(8, 8, text=f"{self.function.get()}   x: {low:g} to {high:g}", anchor="nw", fill="#d9e7ff", font=("Arial", 11))


if __name__ == "__main__":
    CalculatorApp().mainloop()
