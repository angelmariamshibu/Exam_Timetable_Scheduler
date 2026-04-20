```python
"""
ExamGrid — Exam Timetable Scheduler using Graph Coloring
=========================================================
Discrete Mathematics Application | IA2 Project
"""

from flask import Flask, render_template, request, jsonify
import networkx as nx
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io
import base64
import os

# ✅ SINGLE Flask App
app = Flask(__name__)

# ─────────────────────────────────────────────
#  DISCRETE MATHEMATICS CORE ALGORITHMS
# ─────────────────────────────────────────────

def greedy_graph_coloring(subjects, conflicts):
    color_assignment = {}
    algorithm_steps = []

    for i, subject in enumerate(subjects):
        neighbor_colors = set()

        for (a, b) in conflicts:
            if a == subject and b in color_assignment:
                neighbor_colors.add(color_assignment[b])
            elif b == subject and a in color_assignment:
                neighbor_colors.add(color_assignment[a])

        color = 0
        while color in neighbor_colors:
            color += 1

        color_assignment[subject] = color

        algorithm_steps.append({
            "step": f"V{i+1}",
            "message": f"{subject} assigned Slot {color+1}"
        })

    chromatic_number = max(color_assignment.values()) + 1 if color_assignment else 0

    return color_assignment, chromatic_number, algorithm_steps


def build_adjacency_matrix(subjects, conflicts):
    n = len(subjects)
    matrix = [[0]*n for _ in range(n)]
    idx = {s: i for i, s in enumerate(subjects)}

    for (a, b) in conflicts:
        if a in idx and b in idx:
            i, j = idx[a], idx[b]
            matrix[i][j] = 1
            matrix[j][i] = 1

    return matrix


def warshall_algorithm(subjects, conflicts):
    n = len(subjects)
    idx = {s: i for i, s in enumerate(subjects)}

    R = [[0]*n for _ in range(n)]

    for (a, b) in conflicts:
        if a in idx and b in idx:
            R[idx[a]][idx[b]] = 1
            R[idx[b]][idx[a]] = 1

    for k in range(n):
        for i in range(n):
            for j in range(n):
                R[i][j] = R[i][j] or (R[i][k] and R[k][j])

    return R


def compute_graph_stats(subjects, conflicts, color_assignment, chromatic_number):
    n = len(subjects)
    e = len(conflicts)

    degree = {s: 0 for s in subjects}
    for (a, b) in conflicts:
        degree[a] += 1
        degree[b] += 1

    max_degree = max(degree.values()) if degree else 0

    return {
        "vertices": n,
        "edges": e,
        "chromatic_number": chromatic_number,
        "max_degree": max_degree,
        "density": round(2 * e / (n * (n - 1)), 3) if n > 1 else 0
    }


def generate_graph_image(subjects, conflicts, color_assignment):
    SLOT_COLORS = ['#7C3AED', '#DB2777', '#0891B2', '#D97706',
                   '#059669', '#DC2626', '#2563EB', '#65A30D']

    fig, ax = plt.subplots(figsize=(6,5))
    fig.patch.set_facecolor('#0D0D1A')

    G = nx.Graph()
    G.add_nodes_from(subjects)
    G.add_edges_from(conflicts)

    pos = nx.spring_layout(G, seed=42)

    node_colors = []
    for s in G.nodes():
        c = color_assignment.get(s, 0)
        node_colors.append(SLOT_COLORS[c % len(SLOT_COLORS)])

    nx.draw(G, pos, ax=ax,
            with_labels=True,
            node_color=node_colors,
            edge_color='#FC5C7D',
            node_size=1500,
            font_color='white')

    ax.set_facecolor('#0D0D1A')
    ax.set_title("Exam Schedule Graph", color='white')

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=120, bbox_inches='tight')
    plt.close()
    buf.seek(0)

    return base64.b64encode(buf.read()).decode('utf-8')


# ─────────────────────────────────────────────
#  FLASK ROUTES
# ─────────────────────────────────────────────

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/schedule', methods=['POST'])
def schedule():
    data = request.get_json()

    subjects = data.get('subjects', [])
    conflicts = [tuple(c) for c in data.get('conflicts', [])]

    if len(subjects) < 2:
        return jsonify({'error': 'Need at least 2 subjects'}), 400

    color_assignment, chromatic_number, algo_steps = greedy_graph_coloring(subjects, conflicts)
    adjacency_matrix = build_adjacency_matrix(subjects, conflicts)
    transitive_closure = warshall_algorithm(subjects, conflicts)
    stats = compute_graph_stats(subjects, conflicts, color_assignment, chromatic_number)
    graph_image = generate_graph_image(subjects, conflicts, color_assignment)

    return jsonify({
        'color_assignment': color_assignment,
        'chromatic_number': chromatic_number,
        'algorithm_steps': algo_steps,
        'adjacency_matrix': adjacency_matrix,
        'transitive_closure': transitive_closure,
        'stats': stats,
        'graph_image': graph_image,
        'subjects': subjects
    })


@app.route('/sample')
def sample():
    return jsonify({
        'subjects': ['Mathematics', 'Physics', 'Chemistry', 'CS'],
        'conflicts': [
            ['Mathematics', 'Physics'],
            ['Physics', 'Chemistry'],
            ['CS', 'Mathematics']
        ]
    })


# ─────────────────────────────────────────────
#  RUN CONFIG (LOCAL + RENDER)
# ─────────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
```

