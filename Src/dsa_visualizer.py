"""
DSA Auto-Detect Visualizer  v3  --  Premium UI Overhaul
=========================================================
NEW in v3:
  1400x880 window centered on screen, min 1100x680
  3-panel layout: Code editor | Large canvas | Info/Stats sidebar
  GitHub-Dark color tokens, vivid neon accents
  HoverButton with smooth hover-color transitions
  CodeEditor with synchronized line-number gutter
  COMPLEXITY reference card (Big-O per algorithm)
  Arrow-head edges on directed graphs
  Bar chart with value+index labels, glow on changed bars
  Live variable inspector + mini progress bar in sidebar
  Keyboard shortcuts: Left/Right=Step, Space=Play/Pause, R=Restart
  Color-coded status pill (green/red/blue/amber)

Algorithmic core (Sections 1-4) unchanged from v2.
"""

import ast
import io
import json
import math
import sys
import random
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import ctypes
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# ----------------------------------------------------------------------
# 1. SAMPLE CODE TEMPLATES
# ----------------------------------------------------------------------

SAMPLES = {
    "Bubble Sort": '''def bubble_sort(arr):
    n = len(arr)
    for i in range(n):
        for j in range(0, n - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr''',

    "Selection Sort": '''def selection_sort(arr):
    n = len(arr)
    for i in range(n):
        min_idx = i
        for j in range(i + 1, n):
            if arr[j] < arr[min_idx]:
                min_idx = j
        arr[i], arr[min_idx] = arr[min_idx], arr[i]
    return arr''',

    "Insertion Sort": '''def insertion_sort(arr):
    for i in range(1, len(arr)):
        key = arr[i]
        j = i - 1
        while j >= 0 and arr[j] > key:
            arr[j + 1] = arr[j]
            j -= 1
        arr[j + 1] = key
    return arr''',

    "Merge Sort": '''def merge_sort(arr):
    if len(arr) > 1:
        mid = len(arr) // 2
        left = arr[:mid]
        right = arr[mid:]
        merge_sort(left)
        merge_sort(right)
        i = j = k = 0
        while i < len(left) and j < len(right):
            if left[i] < right[j]:
                arr[k] = left[i]
                i += 1
            else:
                arr[k] = right[j]
                j += 1
            k += 1
        while i < len(left):
            arr[k] = left[i]
            i += 1
            k += 1
        while j < len(right):
            arr[k] = right[j]
            j += 1
            k += 1
    return arr''',

    "Quick Sort": '''def quick_sort(arr, low=0, high=None):
    if high is None:
        high = len(arr) - 1
    if low < high:
        pivot = arr[high]
        i = low - 1
        for j in range(low, high):
            if arr[j] <= pivot:
                i += 1
                arr[i], arr[j] = arr[j], arr[i]
        arr[i + 1], arr[high] = arr[high], arr[i + 1]
        quick_sort(arr, low, i)
        quick_sort(arr, i + 2, high)
    return arr''',

    "Linear Search": '''def linear_search(arr, target):
    for i in range(len(arr)):
        if arr[i] == target:
            return i
    return -1''',

    "Binary Search": '''def binary_search(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        elif arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1''',

    "BFS": '''def bfs(graph, start):
    visited = set([start])
    queue = [start]
    order = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)
    return order''',

    "DFS": '''def dfs(graph, start):
    visited = set()
    stack = [start]
    order = []
    while stack:
        node = stack.pop()
        if node not in visited:
            visited.add(node)
            order.append(node)
            for neighbor in reversed(graph.get(node, [])):
                if neighbor not in visited:
                    stack.append(neighbor)
    return order''',

    "Dijkstra": '''import heapq

def dijkstra(graph, start):
    dist = {node: float('inf') for node in graph}
    dist[start] = 0
    visited = set()
    pq = [(0, start)]
    while pq:
        d, node = heapq.heappop(pq)
        if node in visited:
            continue
        visited.add(node)
        for neighbor, weight in graph.get(node, {}).items():
            new_dist = d + weight
            if new_dist < dist[neighbor]:
                dist[neighbor] = new_dist
                heapq.heappush(pq, (new_dist, neighbor))
    return dist''',
}

GRAPH_ALGOS = {"BFS", "DFS", "Dijkstra"}
SEARCH_ALGOS = {"Linear Search", "Binary Search"}
SORT_ALGOS = {"Bubble Sort", "Selection Sort", "Insertion Sort", "Merge Sort", "Quick Sort"}

DEFAULT_ARRAY = "8, 3, 5, 1, 9, 2, 7, 4, 6"
DEFAULT_TARGET = "7"
DEFAULT_GRAPH = "A:B,C; B:D; C:D; D:E; E:"
DEFAULT_WEIGHTED_GRAPH = "A:B-4,C-1; B:D-1; C:B-2,D-5; D:E-3; E:"
DEFAULT_START_NODE = "A"

SPEED_PRESETS = {"Slow": 900, "Normal": 400, "Fast": 150, "Turbo": 50}


# ----------------------------------------------------------------------
# 2. ALGORITHM DETECTOR  (AST heuristics + confidence scoring)
# ----------------------------------------------------------------------

class AlgoFeatures(ast.NodeVisitor):
    def __init__(self):
        self.func_name = None
        self.uses_heapq = False
        self.uses_deque = False
        self.has_recursion = False
        self.has_swap = False
        self.has_visited = False
        self.has_pivot = False
        self.has_mid = False
        self.has_stack_pop_last = False
        self.has_queue_pop_zero = False
        self.max_nested_loops = 0
        self.has_key_var = False
        self.has_low_high = False
        self.n_returns = 0
        self._loop_depth = 0

    def visit_FunctionDef(self, node):
        if self.func_name is None:
            self.func_name = node.name
        self.generic_visit(node)

    def _enter_loop(self, node):
        self._loop_depth += 1
        self.max_nested_loops = max(self.max_nested_loops, self._loop_depth)
        self.generic_visit(node)
        self._loop_depth -= 1

    def visit_For(self, node):
        self._enter_loop(node)

    def visit_While(self, node):
        self._enter_loop(node)

    def visit_Return(self, node):
        self.n_returns += 1
        self.generic_visit(node)

    def visit_Call(self, node):
        fname = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if fname == self.func_name:
            self.has_recursion = True
        if fname in ("heappush", "heappop", "heapify"):
            self.uses_heapq = True
        if fname == "deque":
            self.uses_deque = True
        if fname == "pop":
            if node.args:
                arg0 = node.args[0]
                if isinstance(arg0, ast.Constant) and arg0.value == 0:
                    self.has_queue_pop_zero = True
            else:
                self.has_stack_pop_last = True
        self.generic_visit(node)

    def visit_Assign(self, node):
        if isinstance(node.targets[0], ast.Tuple) and isinstance(node.value, ast.Tuple):
            self.has_swap = True
        self.generic_visit(node)

    def visit_Name(self, node):
        if node.id == "visited":
            self.has_visited = True
        if node.id == "pivot":
            self.has_pivot = True
        if node.id in ("mid", "middle"):
            self.has_mid = True
        if node.id == "key":
            self.has_key_var = True
        if node.id in ("low", "high"):
            self.has_low_high = True
        self.generic_visit(node)


def score_algorithm(code_str):
    """Returns a list of (label, score 0-100, reason) sorted best-first."""
    try:
        tree = ast.parse(code_str)
    except SyntaxError as e:
        return [], f"Syntax error while parsing: {e}"

    f = AlgoFeatures()
    f.visit(tree)
    src = code_str.lower()
    scores = {}

    def add(label, pts, reason):
        cur = scores.get(label, (0, []))
        scores[label] = (cur[0] + pts, cur[1] + [reason])

    if f.uses_heapq:
        add("Dijkstra", 90, "uses heapq (priority queue)")
    if "dist" in src and "float('inf')" in src.replace('"', "'"):
        add("Dijkstra", 40, "dist dict initialised with infinity")

    if f.uses_deque or f.has_queue_pop_zero:
        add("BFS", 80, "FIFO pattern: deque / .pop(0)")
    if "queue" in src:
        add("BFS", 15, "variable named 'queue'")

    if f.has_visited and (f.has_stack_pop_last or "stack" in src):
        add("DFS", 75, "visited-set + stack (.pop()) pattern")
    if "stack" in src:
        add("DFS", 15, "variable named 'stack'")

    if f.has_recursion and f.has_mid and "merge" in src:
        add("Merge Sort", 85, "recursion + mid-split + merge step")
    elif f.has_recursion and f.has_mid:
        add("Merge Sort", 55, "recursion + mid-split (divide & conquer)")

    if f.has_recursion and f.has_pivot:
        add("Quick Sort", 80, "recursion + pivot variable")
    if "pivot" in src:
        add("Quick Sort", 10, "mentions 'pivot'")

    if f.max_nested_loops >= 2 and f.has_swap:
        if "min_idx" in src or "min_index" in src:
            add("Selection Sort", 75, "nested loops + tracked minimum index")
        else:
            add("Bubble Sort", 65, "nested loops + adjacent element swap")

    if f.has_key_var and f.max_nested_loops >= 1 and "while" in src:
        add("Insertion Sort", 70, "shifting elements with a 'key' variable")

    if f.max_nested_loops >= 1 and f.has_low_high and (f.has_mid or "mid" in src):
        add("Binary Search", 75, "low/high/mid halving pattern")

    if f.max_nested_loops >= 1 and f.n_returns >= 2 and "==" in src and not f.has_low_high:
        add("Linear Search", 55, "single loop + equality check + early return")

    if not scores:
        return [], "Could not confidently detect the algorithm. Pick one manually below."

    ranked = sorted(
        [(label, min(100, pts), "; ".join(reasons)) for label, (pts, reasons) in scores.items()],
        key=lambda t: t[1], reverse=True,
    )
    return ranked, None


# ----------------------------------------------------------------------
# 3. GENERIC TRACER
# ----------------------------------------------------------------------

def deep_snapshot(value):
    if isinstance(value, list):
        return list(value)
    if isinstance(value, set):
        return set(value)
    if isinstance(value, dict):
        return dict(value)
    return value


def trace_call(func, args, kwargs=None):
    kwargs = kwargs or {}
    snapshots = []
    target_code = func.__code__

    def tracer(frame, event, arg):
        if frame.f_code is target_code and event == "line":
            snap_vars = {}
            for name, val in frame.f_locals.items():
                if isinstance(val, (list, set, dict)):
                    snap_vars[name] = deep_snapshot(val)
            if snap_vars:
                snapshots.append({"line": frame.f_lineno, "vars": snap_vars})
        return tracer

    old_trace = sys.gettrace()
    sys.settrace(tracer)
    result, error = None, None
    try:
        result = func(*args, **kwargs)
    except Exception as e:
        error = str(e)
    finally:
        sys.settrace(old_trace)
    return snapshots, result, error


def load_user_function(code_str):
    namespace = {}
    exec(compile(code_str, "<user_code>", "exec"), namespace)
    for node in ast.walk(ast.parse(code_str)):
        if isinstance(node, ast.FunctionDef):
            return namespace[node.name], node.name
    return None, None


# ----------------------------------------------------------------------
# 4. INPUT PARSERS (with friendlier errors)
# ----------------------------------------------------------------------

def parse_array(text):
    text = text.strip()
    if not text:
        raise ValueError("Array is empty. Enter comma-separated numbers, e.g. 5, 2, 9, 1")
    out = []
    for chunk in text.split(","):
        chunk = chunk.strip()
        if not chunk:
            continue
        try:
            out.append(int(chunk))
        except ValueError:
            raise ValueError(f"'{chunk}' is not a whole number. Use commas to separate values.")
    if not out:
        raise ValueError("No valid numbers found in the array field.")
    return out


def parse_unweighted_graph(text):
    graph = {}
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"'{part}' is missing a ':' -- format is node:neighbor,neighbor")
        node, _, rest = part.partition(":")
        node = node.strip()
        if not node:
            raise ValueError("Found an empty node name before ':'.")
        neighbors = [n.strip() for n in rest.split(",") if n.strip()]
        graph[node] = neighbors
        for n in neighbors:
            graph.setdefault(n, [])
    if not graph:
        raise ValueError("Graph is empty. Format: A:B,C; B:D; C:")
    return graph


def parse_weighted_graph(text):
    graph = {}
    for part in text.split(";"):
        part = part.strip()
        if not part:
            continue
        if ":" not in part:
            raise ValueError(f"'{part}' is missing a ':' -- format is node:neighbor-weight,...")
        node, _, rest = part.partition(":")
        node = node.strip()
        edges = {}
        for edge in rest.split(","):
            edge = edge.strip()
            if not edge:
                continue
            if "-" not in edge:
                raise ValueError(f"'{edge}' is missing a '-weight' suffix, e.g. B-4")
            n, _, w = edge.partition("-")
            try:
                edges[n.strip()] = float(w.strip())
            except ValueError:
                raise ValueError(f"Weight '{w}' on edge to '{n}' is not a number.")
        graph[node] = edges
        for n in edges:
            graph.setdefault(n, {})
    if not graph:
        raise ValueError("Graph is empty. Format: A:B-4,C-1; B:D-1; C:")
    return graph


# ----------------------------------------------------------------------
# 5. THEME
# ----------------------------------------------------------------------

# =============================================================================
# 5. DESIGN TOKENS  (GitHub-Dark neon palette)
# =============================================================================

class T:
    base     = "#0d1117"
    surface  = "#161b22"
    elevated = "#21262d"
    hover    = "#30363d"
    fg       = "#e6edf3"
    fg2      = "#8b949e"
    fg3      = "#484f58"
    blue     = "#58a6ff"
    blue_d   = "#1f6feb"
    purple   = "#bc8cff"
    green    = "#3fb950"
    green_d  = "#1a472a"
    amber    = "#d29922"
    red      = "#f85149"
    border   = "#30363d"
    bar_n    = "#1f6feb"
    bar_c    = "#f85149"
    bar_p    = "#bc8cff"
    nd_idle  = "#21262d"
    nd_start = "#f85149"
    nd_vis   = "#3fb950"
    nd_front = "#d29922"
    nd_text  = "#e6edf3"


COMPLEXITY = {
    "Bubble Sort":    ("O(n^2)",     "O(1)",     T.red,   "Stable, in-place"),
    "Selection Sort": ("O(n^2)",     "O(1)",     T.red,   "Unstable, in-place"),
    "Insertion Sort": ("O(n^2)",     "O(1)",     T.red,   "Stable, adaptive"),
    "Merge Sort":     ("O(n log n)", "O(n)",     T.amber, "Stable, divide & conquer"),
    "Quick Sort":     ("O(n log n)", "O(log n)", T.amber, "Unstable, in-place"),
    "Linear Search":  ("O(n)",       "O(1)",     T.amber, "Works on unsorted"),
    "Binary Search":  ("O(log n)",   "O(1)",     T.green, "Requires sorted array"),
    "BFS":            ("O(V+E)",     "O(V)",     T.amber, "Shortest path (unweighted)"),
    "DFS":            ("O(V+E)",     "O(V)",     T.amber, "Topological sort / cycles"),
    "Dijkstra":       ("O(E log V)", "O(V)",     T.amber, "Shortest path (weighted>=0)"),
}


# =============================================================================
# 6. CUSTOM WIDGETS
# =============================================================================

class HoverButton(tk.Button):
    """tk.Button with smooth hover-color transition."""
    def __init__(self, master, *, bg, fg, hover_bg, hover_fg=None, **kw):
        self._bg = bg; self._fg = fg
        self._hbg = hover_bg; self._hfg = hover_fg or fg
        super().__init__(master, bg=bg, fg=fg,
                         activebackground=hover_bg,
                         activeforeground=self._hfg,
                         relief="flat", bd=0, cursor="hand2", **kw)
        self.bind("<Enter>", lambda _: self.config(bg=self._hbg, fg=self._hfg))
        self.bind("<Leave>", lambda _: self.config(bg=self._bg,  fg=self._fg))


class CodeEditor(tk.Frame):
    """Text widget with a synchronized line-number gutter."""
    def __init__(self, master, **kw):
        super().__init__(master, bg=T.base, **kw)
        self._gutter = tk.Text(
            self, width=4, state="disabled",
            bg=T.elevated, fg=T.fg3, font=("Consolas", 10),
            relief="flat", bd=0, padx=6, pady=6, cursor="arrow")
        self._gutter.pack(side="left", fill="y")
        self.text = tk.Text(
            self, font=("Consolas", 10), wrap="none",
            bg=T.surface, fg=T.fg, insertbackground=T.blue,
            relief="flat", bd=0, padx=8, pady=6, undo=True,
            selectbackground=T.blue_d, selectforeground=T.fg)
        vsb = tk.Scrollbar(self, orient="vertical", bg=T.elevated,
                           troughcolor=T.surface, command=self._scroll)
        self.text.config(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.text.pack(side="left", fill="both", expand=True)
        self.text.bind("<<Modified>>", lambda _: (self.text.edit_modified(False), self._upd()))
        self.text.bind("<KeyRelease>", lambda _: self._upd())
        self._upd()

    def _scroll(self, *a):
        self.text.yview(*a)
        self._gutter.yview_moveto(self.text.yview()[0])

    def _upd(self):
        n = self.text.get("1.0", "end-1c").count("\n") + 1
        self._gutter.config(state="normal")
        self._gutter.delete("1.0", "end")
        self._gutter.insert("1.0", "\n".join(str(i) for i in range(1, n + 1)))
        self._gutter.config(state="disabled")
        self._gutter.yview_moveto(self.text.yview()[0])

    def get(self):        return self.text.get("1.0", "end")
    def clear(self):      self.text.delete("1.0", "end"); self._upd()
    def insert(self, s):  self.text.insert("1.0", s); self._upd()


# =============================================================================
# 7. MAIN APPLICATION
# =============================================================================

class App:

    def __init__(self, root):
        self.root = root
        self.root.title("DSA Auto-Detect Visualizer  v3")
        self.root.configure(bg=T.base)
        self.root.minsize(1100, 680)
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        root.geometry(f"1400x880+{(sw-1400)//2}+{max(0,(sh-880)//2-30)}")

        # State
        self.snaps   = []; self.step  = 0; self.playing = False
        self.mode    = None; self.guesses = []; self.orig = []
        self.edges   = {}; self.pos   = {}; self.algo = None
        self.speed   = tk.IntVar(value=350)

        self._ui()
        self._keys()
        self.root.after(80, self._defaults)

    # -------------------------------------------------------------------------
    # UI construction
    # -------------------------------------------------------------------------

    def _ui(self):
        self._header()
        self._inputs()
        self._body()

    def _header(self):
        h = tk.Frame(self.root, bg=T.surface, height=56)
        h.pack(fill="x"); h.pack_propagate(False)
        tk.Label(h, text="  DSA Auto-Detect Visualizer  v3",
                 bg=T.surface, fg=T.fg, font=("Segoe UI Semibold", 15)).pack(side="left", padx=10)
        tk.Label(h, text="  Left/Right: Step    Space: Play/Pause    R: Restart  ",
                 bg=T.surface, fg=T.fg3, font=("Segoe UI", 8)).pack(side="right", padx=8)
        self._sf = tk.Frame(h, bg=T.elevated, padx=16, pady=5)
        self._sf.pack(side="right", padx=12, pady=11)
        self._sl = tk.Label(self._sf, text="Paste code -> Detect",
                             bg=T.elevated, fg=T.fg2, font=("Segoe UI", 9))
        self._sl.pack()

    def _inputs(self):
        s = tk.Frame(self.root, bg=T.surface, pady=7)
        s.pack(fill="x", padx=8)
        tk.Label(s, text="Inputs:", bg=T.surface, fg=T.blue,
                 font=("Segoe UI Semibold", 9)).pack(side="left", padx=(4, 12))

        def lbl(t):
            return tk.Label(s, text=t, bg=T.surface, fg=T.fg2, font=("Segoe UI", 9))

        def ent(d, w):
            e = tk.Entry(s, width=w, bg=T.elevated, fg=T.fg,
                         insertbackground=T.fg, relief="flat",
                         font=("Consolas", 9), bd=0,
                         highlightthickness=1, highlightcolor=T.blue,
                         highlightbackground=T.border)
            e.insert(0, d)
            return e

        lbl("Array:").pack(side="left")
        self.arr_e = ent(DEFAULT_ARRAY, 22); self.arr_e.pack(side="left", ipady=4, padx=(2, 2))
        lbl("Target:").pack(side="left", padx=(8, 0))
        self.tgt_e = ent(DEFAULT_TARGET, 5); self.tgt_e.pack(side="left", ipady=4, padx=(2, 2))
        lbl("Graph:").pack(side="left", padx=(10, 0))
        self.gph_e = ent(DEFAULT_GRAPH, 26); self.gph_e.pack(side="left", ipady=4, padx=(2, 2))
        lbl("Start:").pack(side="left", padx=(8, 0))
        self.srt_e = ent(DEFAULT_START_NODE, 4); self.srt_e.pack(side="left", ipady=4, padx=(2, 8))

        HoverButton(s, text="Rnd Array", bg=T.elevated, fg=T.fg2, hover_bg=T.hover, hover_fg=T.fg,
                    font=("Segoe UI", 9), padx=8, pady=4, command=self._rnd_arr).pack(side="left", padx=2)
        HoverButton(s, text="Rnd Graph", bg=T.elevated, fg=T.fg2, hover_bg=T.hover, hover_fg=T.fg,
                    font=("Segoe UI", 9), padx=8, pady=4, command=self._rnd_gph).pack(side="left", padx=2)

        self._ierr = tk.Label(s, text="", bg=T.surface, fg=T.red, font=("Segoe UI", 8))
        self._ierr.pack(side="left", padx=8)

    def _body(self):
        b = tk.Frame(self.root, bg=T.base)
        b.pack(fill="both", expand=True, padx=8, pady=(6, 0))
        L = tk.Frame(b, bg=T.base, width=380); L.pack(side="left", fill="y", padx=(0, 6)); L.pack_propagate(False)
        R = tk.Frame(b, bg=T.base, width=240); R.pack(side="right", fill="y", padx=(6, 0)); R.pack_propagate(False)
        C = tk.Frame(b, bg=T.base); C.pack(side="left", fill="both", expand=True)
        self._code_panel(L); self._info_panel(R); self._canvas_panel(C)

    def _sec(self, p, t):
        tk.Label(p, text=t, bg=T.base, fg=T.blue,
                 font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(4, 3))

    def _code_panel(self, p):
        self._sec(p, "Code Editor")
        row = tk.Frame(p, bg=T.surface, pady=6); row.pack(fill="x")
        tk.Label(row, text="  Sample:", bg=T.surface, fg=T.fg2, font=("Segoe UI", 9)).pack(side="left")
        self.smpv = tk.StringVar()
        sty = ttk.Style()
        try: sty.theme_use("clam")
        except Exception: pass
        sty.configure("TCombobox", fieldbackground=T.elevated, background=T.elevated,
                      foreground=T.fg, arrowcolor=T.fg2, bordercolor=T.border)
        sty.map("TCombobox", fieldbackground=[("readonly", T.elevated)])
        sty.configure("Horizontal.TScale", background=T.surface,
                      troughcolor=T.elevated, sliderlength=16)
        cb = ttk.Combobox(row, textvariable=self.smpv, values=list(SAMPLES.keys()),
                          state="readonly", width=16, font=("Segoe UI", 9))
        cb.pack(side="left", padx=6); cb.bind("<<ComboboxSelected>>", self._load_sample)

        self.editor = CodeEditor(p); self.editor.pack(fill="both", expand=True, pady=(4, 0))

        dr = tk.Frame(p, bg=T.surface, pady=7, padx=8); dr.pack(fill="x")
        HoverButton(dr, text="Detect Algorithm",
                    bg=T.blue_d, fg=T.fg, hover_bg=T.blue, hover_fg="#000",
                    font=("Segoe UI Semibold", 10), padx=14, pady=7,
                    command=self._detect).pack(fill="x", expand=True)

        self._glbl = tk.Label(p, text="(no detection yet)", bg=T.base, fg=T.fg2,
                               font=("Segoe UI", 8), justify="left", wraplength=360, anchor="w")
        self._glbl.pack(fill="x", padx=8, pady=(4, 2))

        rr = tk.Frame(p, bg=T.surface, pady=4, padx=8); rr.pack(fill="x", pady=(7, 2))
        tk.Label(rr, text="Override:", bg=T.surface, fg=T.fg2, font=("Segoe UI", 9)).pack(side="left")
        self.manv = tk.StringVar()
        ttk.Combobox(rr, textvariable=self.manv, values=list(SAMPLES.keys()),
                     state="readonly", width=14, font=("Segoe UI", 9)).pack(side="left", padx=6)
        
        vr = tk.Frame(p, bg=T.surface, pady=4, padx=8); vr.pack(fill="x", pady=(2, 7))
        HoverButton(vr, text="Run & Visualize",
                    bg=T.green_d, fg=T.green, hover_bg=T.green, hover_fg="#000",
                    font=("Segoe UI Semibold", 10), padx=12, pady=7,
                    command=self._run).pack(fill="x", expand=True)

    def _canvas_panel(self, p):
        self._sec(p, "Visualization")
        wrap = tk.Frame(p, bg=T.border, bd=1); wrap.pack(fill="both", expand=True)
        self.cv = tk.Canvas(wrap, bg=T.surface, highlightthickness=0)
        self.cv.pack(fill="both", expand=True)
        self._com = tk.Label(p, text="Run an algorithm to see step-by-step commentary.",
                              bg=T.elevated, fg=T.amber, font=("Segoe UI", 9, "italic"),
                              anchor="w", padx=10, pady=7, wraplength=760)
        self._com.pack(fill="x", pady=(4, 0))
        self._playback(p)

    def _playback(self, p):
        ctrl = tk.Frame(p, bg=T.surface, pady=10); ctrl.pack(fill="x", pady=(4, 8))
        br = tk.Frame(ctrl, bg=T.surface); br.pack()
        bkw = dict(font=("Segoe UI", 10), padx=12, pady=6)
        HoverButton(br, text="<< Prev", bg=T.elevated, fg=T.fg, hover_bg=T.hover,
                    command=self._prev, **bkw).pack(side="left", padx=4)
        self._pb = HoverButton(br, text="  Play  ", bg=T.blue_d, fg=T.fg,
                                hover_bg=T.blue, hover_fg="#000",
                                font=("Segoe UI Semibold", 10), padx=20, pady=6,
                                command=self._playpause)
        self._pb.pack(side="left", padx=4)
        HoverButton(br, text="Next >>", bg=T.elevated, fg=T.fg, hover_bg=T.hover,
                    command=self._next, **bkw).pack(side="left", padx=4)
        HoverButton(br, text="Restart", bg=T.elevated, fg=T.fg2, hover_bg=T.hover,
                    command=self._restart, **bkw).pack(side="left", padx=(22, 4))
        tk.Label(br, text="Speed:", bg=T.surface, fg=T.fg2,
                 font=("Segoe UI", 9)).pack(side="left", padx=(14, 4))
        for nm, ms in [("Slow", 900), ("Normal", 350), ("Fast", 100), ("Turbo", 30)]:
            HoverButton(br, text=nm, bg=T.elevated, fg=T.fg2, hover_bg=T.hover, hover_fg=T.fg,
                        font=("Segoe UI", 9), padx=9, pady=6,
                        command=lambda m=ms: self.speed.set(m)).pack(side="left", padx=2)
        HoverButton(br, text="Export JSON", bg=T.elevated, fg=T.fg2, hover_bg=T.hover,
                    command=self._export, font=("Segoe UI", 9), padx=9, pady=6).pack(side="right", padx=8)
        self._slbl = tk.Label(br, text="Step  0 / 0", bg=T.surface, fg=T.blue, font=("Consolas", 10))
        self._slbl.pack(side="right", padx=14)
        self._scr = ttk.Scale(ctrl, from_=0, to=0, orient="horizontal", command=self._scrub)
        self._scr.pack(fill="x", padx=14, pady=(8, 0))

    def _info_panel(self, p):
        self._sec(p, "Info & Stats")
        cf = tk.LabelFrame(p, text=" Complexity ", bg=T.surface, fg=T.fg3,
                           font=("Segoe UI", 8), bd=1, relief="solid")
        cf.pack(fill="x", padx=4, pady=(0, 8))
        self._cxn = tk.Label(cf, text="--", bg=T.surface, fg=T.fg, font=("Segoe UI Semibold", 11))
        self._cxn.pack(anchor="w", padx=10, pady=(8, 2))
        self._cxt = tk.Label(cf, text="Time:  --", bg=T.surface, fg=T.green, font=("Consolas", 10))
        self._cxt.pack(anchor="w", padx=10)
        self._cxs = tk.Label(cf, text="Space: --", bg=T.surface, fg=T.blue, font=("Consolas", 10))
        self._cxs.pack(anchor="w", padx=10)
        self._cxo = tk.Label(cf, text="", bg=T.surface, fg=T.fg2,
                              font=("Segoe UI", 8), wraplength=210, justify="left")
        self._cxo.pack(anchor="w", padx=10, pady=(2, 10))

        vf = tk.LabelFrame(p, text=" Variables ", bg=T.surface, fg=T.fg3,
                           font=("Segoe UI", 8), bd=1, relief="solid")
        vf.pack(fill="x", padx=4, pady=(0, 8))
        self._vt = tk.Text(vf, height=12, bg=T.surface, fg=T.fg2,
                            font=("Consolas", 8), relief="flat", bd=0,
                            padx=8, pady=6, state="disabled", wrap="word")
        self._vt.pack(fill="both")

        pf = tk.LabelFrame(p, text=" Progress ", bg=T.surface, fg=T.fg3,
                           font=("Segoe UI", 8), bd=1, relief="solid")
        pf.pack(fill="x", padx=4, pady=(0, 8))
        self._pg = tk.Canvas(pf, bg=T.elevated, height=18, highlightthickness=0)
        self._pg.pack(fill="x", padx=6, pady=8)

        lf = tk.LabelFrame(p, text=" Node Legend ", bg=T.surface, fg=T.fg3,
                           font=("Segoe UI", 8), bd=1, relief="solid")
        lf.pack(fill="x", padx=4)
        for lbl, col in [("Start", T.nd_start), ("Visited", T.nd_vis),
                          ("Frontier", T.nd_front), ("Idle", T.nd_idle)]:
            row = tk.Frame(lf, bg=T.surface); row.pack(fill="x", padx=8, pady=3)
            dot = tk.Canvas(row, bg=T.surface, width=16, height=16, highlightthickness=0)
            dot.create_oval(2, 2, 14, 14, fill=col, outline=T.fg2)
            dot.pack(side="left")
            tk.Label(row, text=f"  {lbl}", bg=T.surface, fg=T.fg2,
                     font=("Segoe UI", 8)).pack(side="left")
        tk.Frame(lf, bg=T.surface, height=4).pack()

    # -------------------------------------------------------------------------
    # Helpers
    # -------------------------------------------------------------------------

    def _status(self, text, k="info"):
        pal = {"info": (T.elevated, T.fg2), "good": ("#1a472a", T.green),
               "bad": ("#4a1010", T.red), "accent": ("#0d2045", T.blue)}
        bg, fg = pal.get(k, pal["info"])
        self._sf.config(bg=bg); self._sl.config(bg=bg, fg=fg, text=text)

    def _keys(self):
        self.root.bind("<Left>",  lambda _: self._prev())
        self.root.bind("<Right>", lambda _: self._next())
        self.root.bind("<space>", lambda _: self._playpause())
        self.root.bind("<r>",     lambda _: self._restart())
        self.root.bind("<R>",     lambda _: self._restart())

    def _defaults(self):
        self.editor.insert(SAMPLES["Bubble Sort"])
        self.smpv.set("Bubble Sort"); self.manv.set("Bubble Sort")
        self._cx("Bubble Sort")

    def _cx(self, algo):
        if algo not in COMPLEXITY: return
        tc, sc, col, note = COMPLEXITY[algo]
        self._cxn.config(text=algo)
        self._cxt.config(text=f"Time:  {tc}", fg=col)
        self._cxs.config(text=f"Space: {sc}")
        self._cxo.config(text=note)

    def _upd_vars(self, sn):
        self._vt.config(state="normal"); self._vt.delete("1.0", "end")
        for k, v in sn["vars"].items():
            if isinstance(v, set):
                val = "{" + ", ".join(str(x) for x in sorted(v, key=str)) + "}"
            elif isinstance(v, dict):
                items = list(v.items())[:5]
                val = "{" + ", ".join(f"{a}:{b}" for a, b in items) + \
                      ("..." if len(v) > 5 else "") + "}"
            elif isinstance(v, list):
                val = str(v[:8]) + ("..." if len(v) > 8 else "")
            else:
                val = str(v)[:40]
            self._vt.insert("end", f"{k}:\n  {val}\n\n")
        self._vt.config(state="disabled")

    def _upd_prog(self):
        if not self.snaps: return
        pct = (self.step + 1) / len(self.snaps)
        c = self._pg; c.delete("all"); w = c.winfo_width() or 220
        c.create_rectangle(0, 0, w, 18, fill=T.elevated, outline="")
        c.create_rectangle(0, 0, int(w * pct), 18, fill=T.blue, outline="")
        c.create_text(w // 2, 9, fill=T.fg, font=("Segoe UI", 7),
                      text=f"{self.step + 1}/{len(self.snaps)}")

    # -------------------------------------------------------------------------
    # Events
    # -------------------------------------------------------------------------

    def _load_sample(self, _=None):
        name = self.smpv.get()
        if name in SAMPLES:
            self.editor.clear(); self.editor.insert(SAMPLES[name])
            if name in GRAPH_ALGOS:
                self.gph_e.delete(0, "end")
                self.gph_e.insert(0, DEFAULT_WEIGHTED_GRAPH if name == "Dijkstra" else DEFAULT_GRAPH)
            self.manv.set(name); self._cx(name)

    def _rnd_arr(self):
        vals = random.sample(range(1, 60), random.randint(8, 14))
        self.arr_e.delete(0, "end"); self.arr_e.insert(0, ", ".join(str(v) for v in vals))

    def _rnd_gph(self):
        nodes = ["A", "B", "C", "D", "E", "F"][:random.randint(4, 6)]
        w = self.manv.get() == "Dijkstra"; parts = []
        for i, n in enumerate(nodes):
            later = nodes[i + 1:]
            picks = random.sample(later, min(len(later), random.randint(0, 2))) if later else []
            edges = ",".join(f"{p}-{random.randint(1,9)}" if w else p for p in picks)
            parts.append(f"{n}:{edges}")
        self.gph_e.delete(0, "end"); self.gph_e.insert(0, "; ".join(parts))
        self.srt_e.delete(0, "end"); self.srt_e.insert(0, nodes[0])

    def _detect(self):
        ranked, err = score_algorithm(self.editor.get()); self.guesses = ranked
        if ranked:
            bl, bs, _ = ranked[0]; self.manv.set(bl)
            self._glbl.config(
                text="\n".join(f"#{i+1}  {l}  ({sc}%)" for i, (l, sc, _) in enumerate(ranked[:3])),
                fg=T.green)
            self._status(f"Detected: {bl}  ({bs}%)", "good"); self._cx(bl)
        else:
            self._glbl.config(text=err or "No confident match.", fg=T.red)
            self._status("Detection unsure", "bad")

    def _algo(self):
        return self.manv.get() or (self.guesses[0][0] if self.guesses else None)

    def _run(self):
        self._ierr.config(text="")
        algo = self._algo()
        if not algo:
            self._detect(); algo = self._algo()
        if not algo:
            messagebox.showwarning("No algorithm", "Pick one from Override."); return
        code = self.editor.get()
        try:
            func, fname = load_user_function(code)
        except Exception as e:
            messagebox.showerror("Code error", str(e)); return
        if not func:
            messagebox.showerror("Code error", "No function found."); return
        try:
            if algo in SORT_ALGOS:
                self.mode = "sort"; arr = parse_array(self.arr_e.get()); self.orig = list(arr)
                snaps, result, err2 = trace_call(func, (arr,))
            elif algo in SEARCH_ALGOS:
                self.mode = "search"; arr = parse_array(self.arr_e.get())
                if algo == "Binary Search": arr = sorted(arr)
                self.orig = list(arr)
                snaps, result, err2 = trace_call(func, (arr, int(self.tgt_e.get())))
            elif algo == "Dijkstra":
                self.mode = "graph"; graph = parse_weighted_graph(self.gph_e.get())
                self.edges = {n: list(e.keys()) for n, e in graph.items()}
                snaps, result, err2 = trace_call(func, (graph, self.srt_e.get().strip()))
            elif algo in ("BFS", "DFS"):
                self.mode = "graph"; graph = parse_unweighted_graph(self.gph_e.get())
                self.edges = graph
                snaps, result, err2 = trace_call(func, (graph, self.srt_e.get().strip()))
            else:
                messagebox.showerror("Unsupported", f"'{algo}' not wired up."); return
        except ValueError as e:
            self._ierr.config(text=f"  {e}"); return
        except Exception as e:
            messagebox.showerror("Input error", str(e)); return
        if err2:
            messagebox.showerror("Runtime error", err2); return
        if not snaps:
            messagebox.showwarning("No steps",
                "No list/set/dict locals found to trace.\n"
                "Make sure your function uses arr / visited / queue / dist."); return
        if self.mode == "graph": self._calc_pos()
        self.snaps = snaps; self.step = 0; self.playing = False; self.algo = algo
        self._pb.config(text="  Play  ")
        self._scr.config(to=max(0, len(snaps) - 1)); self._scr.set(0)
        self._status(f"'{fname}'  ->  {algo}  |  {len(snaps)} steps  |  result: {result}", "accent")
        self._cx(algo); self.render()

    def _prev(self):
        if self.snaps and self.step > 0:
            self.step -= 1; self._scr.set(self.step); self.render()

    def _next(self):
        if self.snaps and self.step < len(self.snaps) - 1:
            self.step += 1; self._scr.set(self.step); self.render()

    def _restart(self):
        if self.snaps:
            self.step = 0; self.playing = False
            self._pb.config(text="  Play  ")
            self._scr.set(0); self.render()

    def _scrub(self, v):
        idx = int(float(v))
        if idx != self.step: self.step = idx; self.render()

    def _playpause(self):
        if not self.snaps: return
        self.playing = not self.playing
        self._pb.config(text="  Pause  " if self.playing else "  Play  ")
        if self.playing: self._tick()

    def _tick(self):
        if not self.playing: return
        if self.step < len(self.snaps) - 1:
            self.step += 1; self._scr.set(self.step); self.render()
            self.root.after(self.speed.get(), self._tick)
        else:
            self.playing = False; self._pb.config(text="  Play  ")

    def _export(self):
        if not self.snaps:
            messagebox.showinfo("Nothing to export", "Run an algorithm first."); return
        path = filedialog.asksaveasfilename(defaultextension=".json",
                                             filetypes=[("JSON files", "*.json")],
                                             initialfile="dsa_trace.json")
        if not path: return
        out = []
        for sn in self.snaps:
            vout = {}
            for k, v in sn["vars"].items():
                if isinstance(v, set): vout[k] = list(v)
                elif isinstance(v, dict):
                    vout[k] = {str(kk): (None if vv == float("inf") else vv)
                                for kk, vv in v.items()}
                else: vout[k] = v
            out.append({"line": sn["line"], "vars": vout})
        with io.open(path, "w", encoding="utf-8") as fp:
            json.dump({"algorithm": self.algo, "steps": out}, fp, indent=2)
        self._status(f"Exported -> {path.split('/')[-1]}", "good")

    # -------------------------------------------------------------------------
    # Rendering
    # -------------------------------------------------------------------------

    def render(self):
        self.cv.delete("all")
        if not self.snaps: return
        sn = self.snaps[self.step]; total = len(self.snaps)
        self._slbl.config(text=f"Step  {self.step + 1} / {total}")
        self._upd_vars(sn); self._upd_prog()
        if self.mode in ("sort", "search"): self._bars(sn)
        elif self.mode == "graph": self._graph(sn)

    def _pick(self, vars_):
        for k, v in vars_.items():
            if isinstance(v, list) and len(v) == len(self.orig) \
               and all(isinstance(x, (int, float)) for x in v):
                return k, v
        for k, v in vars_.items():
            if isinstance(v, list): return k, v
        return None, None

    def _bars(self, sn):
        c = self.cv
        w = c.winfo_width() or 700
        h = c.winfo_height() or 420
        name, arr = self._pick(sn["vars"])
        if arr is None or not arr:
            c.create_text(w // 2, h // 2, text="No array snapshot at this step",
                          fill=T.fg3, font=("Segoe UI", 12)); return
        n = len(arr); px = 36; pt = 36; pb = 44; gap = 5
        bw = max(8, (w - 2*px - gap*(n-1)) / n)
        uh = h - pt - pb
        mx = max((abs(v) for v in arr), default=1) or 1
        parr = None
        if self.step > 0: _, parr = self._pick(self.snaps[self.step - 1]["vars"])
        pv = sn["vars"].get("pivot")
        if not isinstance(pv, (int, float)): pv = None
        ch = set()
        if parr and len(parr) == n:
            ch = {i for i in range(n) if parr[i] != arr[i]}
        comments = []
        for i, v in enumerate(arr):
            bh = max(4, (abs(v) / mx) * uh)
            x0 = px + i * (bw + gap); y1 = h - pb; y0 = y1 - bh; x1 = x0 + bw
            if pv is not None and v == pv:
                fill = T.bar_p; out = T.purple; wd = 2
            elif i in ch:
                fill = T.bar_c; out = T.red; wd = 2
            else:
                fill = T.bar_n; out = T.blue; wd = 1
            c.create_rectangle(x0, y0, x1, y1, fill=fill, outline=out, width=wd)
            if bw > 14:
                c.create_text((x0+x1)/2, y0 - 10, text=str(v), fill=T.fg,
                              font=("Consolas", max(7, min(10, int(bw * 0.6)))))
                c.create_text((x0+x1)/2, y1 + 14, text=str(i), fill=T.fg3,
                              font=("Consolas", 7))
        c.create_text(px, 16, anchor="w", text=f"var: {name}", fill=T.fg3,
                      font=("Consolas", 8, "italic"))
        lx = w - 250
        for lbl, col in [("Normal", T.bar_n), ("Changed", T.bar_c), ("Pivot", T.bar_p)]:
            c.create_rectangle(lx, 11, lx+12, 23, fill=col, outline="")
            c.create_text(lx+17, 17, anchor="w", text=lbl, fill=T.fg2, font=("Segoe UI", 8))
            lx += 85
        if ch: comments.append(f"Indices {sorted(ch)} changed")
        if pv is not None: comments.append(f"Pivot = {pv}")
        self._com.config(text=" | ".join(comments) if comments else "Comparing / scanning...")

    def _calc_pos(self):
        nodes = list(self.edges.keys()); n = max(len(nodes), 1)
        cw = self.cv.winfo_width() or 680; ch = self.cv.winfo_height() or 420
        cx = cw // 2; cy = ch // 2; r = min(cw, ch) // 2 - 70
        self.pos = {}
        for i, nd in enumerate(nodes):
            a = 2 * math.pi * i / n - math.pi / 2
            self.pos[nd] = (cx + r * math.cos(a), cy + r * math.sin(a))

    @staticmethod
    def _arrow(c, x0, y0, x1, y1, col, wd, nr=28):
        dx = x1 - x0; dy = y1 - y0; ln = math.hypot(dx, dy) or 1
        ex = x1 - dx / ln * nr; ey = y1 - dy / ln * nr
        c.create_line(x0, y0, ex, ey, fill=col, width=wd,
                      arrow="last", arrowshape=(12, 15, 5))

    def _ff(self, vars_, kind, names):
        for nm in names:
            if nm in vars_ and isinstance(vars_[nm], kind): return vars_[nm]
        for v in vars_.values():
            if isinstance(v, kind): return v
        return None

    def _graph(self, sn):
        c = self.cv
        visited  = self._ff(sn["vars"], (set, dict), ["visited", "dist"])
        frontier = self._ff(sn["vars"], list, ["queue", "stack", "pq"])
        fn = set()
        if frontier:
            for item in frontier:
                fn.add(item[-1] if isinstance(item, (tuple, list)) and len(item) >= 2 else item)
        vn = set()
        if isinstance(visited, dict):
            vn = {k for k, v in visited.items() if v != float("inf")}
        elif isinstance(visited, set):
            vn = set(visited)
        self._calc_pos(); start = self.srt_e.get().strip(); nr = 28
        for nd, nbrs in self.edges.items():
            if nd not in self.pos: continue
            x0, y0 = self.pos[nd]
            for nb in nbrs:
                if nb not in self.pos: continue
                x1, y1 = self.pos[nb]
                act = nd in vn and nb in (vn | fn)
                self._arrow(c, x0, y0, x1, y1, T.amber if act else T.border, 3 if act else 1, nr)
        for nd, (x, y) in self.pos.items():
            if nd == start: fill = T.nd_start
            elif nd in vn: fill = T.nd_vis
            elif nd in fn: fill = T.nd_front
            else: fill = T.nd_idle
            if nd in vn or nd in fn:
                rr = nr + 5
                c.create_oval(x-rr, y-rr, x+rr, y+rr, fill="", outline=fill, width=2)
            c.create_oval(x-nr, y-nr, x+nr, y+nr, fill=fill, outline=T.fg, width=2)
            c.create_text(x, y, text=nd, fill=T.nd_text, font=("Segoe UI Semibold", 12))
            if isinstance(visited, dict) and nd in visited and isinstance(visited[nd], (int, float)) and visited[nd] != float("inf"):
                c.create_text(x, y + nr + 16, text=f"d={visited[nd]:g}",
                              fill=T.amber, font=("Consolas", 9))
        self._com.config(
            text=f"Frontier: {sorted(fn, key=str) or '--'}   |   Visited: {sorted(vn, key=str) or '--'}")


# =============================================================================
# ENTRY POINT
# =============================================================================

def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
