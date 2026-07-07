# DSA Auto-Detect Visualizer v3 🚀

A premium, interactive Data Structures and Algorithms (DSA) visualizer built in Python using `tkinter`. This tool goes beyond basic visualization by automatically detecting the algorithm you type and providing real-time visual feedback, complete with a modern, dark-themed UI.

## 📸 Screenshots

*(Replace these placeholders with your actual screenshots)*

![Main Interface](
<img width="959" height="505" alt="image" src="https://github.com/user-attachments/assets/d4259d65-0c3f-446b-a26c-0ccdb5cbffb1" />

![Algorithm Detection]
<img width="959" height="504" alt="image" src="https://github.com/user-attachments/assets/1a1e285f-a91d-4547-96c4-ce06835f19b2" />

![Graph Rendering]
<img width="959" height="503" alt="image" src="https://github.com/user-attachments/assets/2f23e3c7-9988-4347-a4a7-4e318ff413d2" />

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![Tkinter](https://img.shields.io/badge/GUI-Tkinter-orange.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## ✨ Premium UI Overhaul (New in v3)
Version 3 introduces a massive design overhaul inspired by modern developer tools (like GitHub Dark mode), focusing on aesthetics, readability, and user experience.

* **3-Panel Layout:** Code Editor (Left) | Large Visualization Canvas (Center) | Info/Stats Sidebar (Right).
* **High-DPI Awareness:** Crisp, sharp text rendering on high-resolution displays.
* **Modern Color Palette:** GitHub-Dark color tokens with vivid neon accents for highlights.
* **Code Editor Enhancements:** Integrated synchronized line-number gutter and syntax awareness.
* **Interactive Elements:** Smooth hover-color transitions on buttons (`HoverButton`).
* **Visual Upgrades:**
  * **Graphs:** Arrow-head edges for directed graphs.
  * **Arrays/Sorting:** Bar charts with value + index labels, and neon glow effects on changed bars/pivots.
* **Live Sidebar:** Real-time variable inspector, mini progress bar, and algorithm complexity reference cards (Big-O notation).
* **Status Pill:** Color-coded status indicator (Green/Red/Blue/Amber) to show execution state.

## 🧠 Auto-Detection Engine
You don't need to manually tell the visualizer what algorithm you are running. The built-in Abstract Syntax Tree (AST) parser analyzes your Python code, detects structural patterns (like `heappop` for Dijkstra, or specific recursive pivot patterns for Quick Sort), and automatically configures the visualizer for that specific algorithm!

## 🛠️ Supported Algorithms

### Sorting
* Bubble Sort
* Selection Sort
* Insertion Sort
* Merge Sort
* Quick Sort

### Searching
* Linear Search
* Binary Search

### Graph Algorithms
* Breadth-First Search (BFS)
* Depth-First Search (DFS)
* Dijkstra's Shortest Path (Weighted Graphs)

## 🎮 Keyboard Shortcuts
Navigate through algorithm steps seamlessly without taking your hands off the keyboard:
* <kbd>Left Arrow</kbd> / <kbd>Right Arrow</kbd>: Step backward / forward
* <kbd>Space</kbd>: Play / Pause auto-playback
* <kbd>R</kbd>: Restart visualization from the beginning

## 🚀 How to Run

### Prerequisites
* Python 3.8 or higher.
* No external dependencies required! (Uses standard libraries: `tkinter`, `ast`, `ctypes`, etc.)

### Execution
Clone the repository or download the script, then simply run it from your terminal:
```bash
python dsa_visualizer_v3.py
```

### Usage
1. **Choose an Algorithm:** Select a pre-written sample from the "Sample" dropdown, OR paste your own Python code into the editor.
2. **Detect:** Click "Detect Algorithm" to let the engine analyze your code.
3. **Configure Data:** Use the "Inputs" section to generate random arrays/graphs or type your own custom data.
4. **Visualize:** Click "Run & Visualize" and use the playback controls or arrow keys to step through the execution!

---
*Built with ❤️ for algorithmic learners and visual thinkers.*
