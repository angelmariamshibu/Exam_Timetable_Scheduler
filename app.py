"""
ExamGrid — Exam Timetable Scheduler using Graph Coloring
=========================================================
Discrete Mathematics Application | IA2 Project

Concepts Applied:
  - Graph Theory: G = (V, E) where V = subjects, E = conflicts
  - Graph Coloring: assign colors (slots) such that no adjacent nodes share a color
  - Chromatic Number χ(G): minimum colors needed
  - Greedy Graph Coloring Algorithm
  - Adjacency Matrix: matrix representation of the conflict relation
  - Relations & Digraphs: conflict as a symmetric binary relation
  - Warshall's Algorithm: transitive closure of reachability
  - Inclusion-Exclusion: counting students in multiple exams

Author  : IA2 Project
Module  : Discrete Mathematics
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
import json

app = Flask(__name__)

# ─────────────────────────────────────────────
#  DISCRETE MATHEMATICS CORE ALGORITHMS
# ─────────────────────────────────────────────

def greedy_graph_coloring(subjects: list, conflicts: list) -> dict:
    """
    Greedy Graph Coloring Algorithm
    --------------------------------
    Given graph G = (V, E):
      V = subjects (vertices)
      E = conflicts (edges)

    For each vertex v in V (in order):
      1. Find all colors used by neighbors of v
      2. Assign the smallest color not used by any neighbor
    
    Returns: dict mapping subject -> color (0-indexed time slot)
    Time Complexity: O(V + E)
    """
    color_assignment = {}
    algorithm_steps = []
    
    algorithm_steps.append({
        "step": "INIT",
        "message": f"Graph G = (V, E) initialized",
        "detail": f"|V| = {len(subjects)} vertices, |E| = {len(conflicts)} edges"
    })

    for i, subject in enumerate(subjects):
        # Find colors used by already-colored neighbors
        neighbor_colors = set()
        neighbors_colored = []
        
        for (a, b) in conflicts:
            if a == subject and b in color_assignment:
                neighbor_colors.add(color_assignment[b])
                neighbors_colored.append(b)
            elif b == subject and a in color_assignment:
                neighbor_colors.add(color_assignment[a])
                neighbors_colored.append(a)

        # Assign smallest available color
        assigned_color = 0
        while assigned_color in neighbor_colors:
            assigned_color += 1

        color_assignment[subject] = assigned_color

        algorithm_steps.append({
            "step": f"V{i+1}",
            "message": f'Processing vertex "{subject}"',
            "detail": f'Neighbor colors used: {sorted(neighbor_colors) if neighbor_colors else ["none"]} → Assign Slot {assigned_color + 1}',
            "color": assigned_color
        })

    chromatic_number = max(color_assignment.values()) + 1 if color_assignment else 0
    algorithm_steps.append({
        "step": "DONE",
        "message": f"Coloring complete!",
        "detail": f"Chromatic number χ(G) = {chromatic_number} — minimum {chromatic_number} time slots required"
    })

    return color_assignment, chromatic_number, algorithm_steps


def build_adjacency_matrix(subjects: list, conflicts: list) -> list:
    """
    Build Adjacency Matrix for the conflict graph.
    A[i][j] = 1 if subject i and subject j conflict, else 0.
    This is the matrix representation of the binary relation R on subjects.
    """
    n = len(subjects)
    matrix = [[0] * n for _ in range(n)]
    idx = {s: i for i, s in enumerate(subjects)}
    
    for (a, b) in conflicts:
        if a in idx and b in idx:
            i, j = idx[a], idx[b]
            matrix[i][j] = 1
            matrix[j][i] = 1  # symmetric relation
    
    return matrix


def warshall_algorithm(subjects: list, conflicts: list) -> list:
    """
    Warshall's Algorithm — Transitive Closure
    ------------------------------------------
    Computes R+ (transitive closure) of the conflict relation.
    Shows which subjects are INDIRECTLY connected through shared students.
    
    Algorithm:
      for k = 1 to n:
        for i = 1 to n:
          for j = 1 to n:
            R[i][j] = R[i][j] OR (R[i][k] AND R[k][j])
    """
    n = len(subjects)
    idx = {s: i for i, s in enumerate(subjects)}
    
    # Initialize from conflict edges
    R = [[False] * n for _ in range(n)]
    for (a, b) in conflicts:
        if a in idx and b in idx:
            R[idx[a]][idx[b]] = True
            R[idx[b]][idx[a]] = True

    # Warshall's algorithm
    for k in range(n):
        for i in range(n):
            for j in range(n):
                R[i][j] = R[i][j] or (R[i][k] and R[k][j])

    return [[1 if R[i][j] else 0 for j in range(n)] for i in range(n)]


def compute_graph_stats(subjects, conflicts, color_assignment, chromatic_number):
    """Compute useful graph statistics for display."""
    n = len(subjects)
    e = len(conflicts)
    
    # Degree of each vertex
    degree = {s: 0 for s in subjects}
    for (a, b) in conflicts:
        if a in degree: degree[a] += 1
        if b in degree: degree[b] += 1
    
    max_degree = max(degree.values()) if degree else 0
    
    # Slots distribution
    slots = {}
    for s, c in color_assignment.items():
        slots.setdefault(c, []).append(s)
    
    return {
        "vertices": n,
        "edges": e,
        "chromatic_number": chromatic_number,
        "max_degree": max_degree,
        "density": round(2 * e / (n * (n - 1)), 3) if n > 1 else 0,
        "slots": {str(k): v for k, v in slots.items()},
        "degree_sequence": sorted(degree.values(), reverse=True)
    }


def generate_graph_image(subjects, conflicts, color_assignment):
    """
    Generate a beautiful NetworkX graph visualization using matplotlib.
    Returns base64-encoded PNG image.
    """
    SLOT_COLORS = [
        '#7C3AED', '#DB2777', '#0891B2', '#D97706',
        '#059669', '#DC2626', '#2563EB', '#65A30D'
    ]
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6))
    fig.patch.set_facecolor('#0D0D1A')
    
    # ── Left: Colored Conflict Graph ──
    ax = axes[0]
    ax.set_facecolor('#0D0D1A')
    ax.set_title('Conflict Graph — Colored by Time Slot', 
                 color='white', fontsize=12, fontweight='bold', pad=15,
                 fontfamily='monospace')

    G = nx.Graph()
    G.add_nodes_from(subjects)
    G.add_edges_from(conflicts)

    if len(subjects) > 0:
        # Layout
        if len(subjects) <= 3:
            pos = nx.circular_layout(G)
        else:
            try:
                pos = nx.kamada_kawai_layout(G)
            except:
                pos = nx.spring_layout(G, seed=42, k=2)

        # Node colors
        node_colors = []
        node_edge_colors = []
        for s in G.nodes():
            c = color_assignment.get(s, 0)
            node_colors.append(SLOT_COLORS[c % len(SLOT_COLORS)] + 'CC')
            node_edge_colors.append(SLOT_COLORS[c % len(SLOT_COLORS)])

        # Draw edges
        nx.draw_networkx_edges(G, pos, ax=ax,
            edge_color='#FC5C7D', alpha=0.6,
            width=2.0, style='dashed')

        # Draw nodes
        nx.draw_networkx_nodes(G, pos, ax=ax,
            node_color=node_colors,
            edgecolors=node_edge_colors,
            node_size=1800, linewidths=2.5)

        # Labels
        nx.draw_networkx_labels(G, pos, ax=ax,
            font_color='white', font_size=8,
            font_weight='bold', font_family='monospace')

        # Slot labels on nodes
        slot_labels = {s: f"S{color_assignment.get(s,0)+1}" for s in subjects}
        offset_pos = {n: (p[0], p[1] - 0.18) for n, p in pos.items()}
        nx.draw_networkx_labels(G, offset_pos, labels=slot_labels, ax=ax,
            font_color='#FFD700', font_size=7, font_family='monospace')

        # Legend
        used_colors = sorted(set(color_assignment.values()))
        patches = [mpatches.Patch(
            color=SLOT_COLORS[c % len(SLOT_COLORS)],
            label=f'Slot {c+1}'
        ) for c in used_colors]
        ax.legend(handles=patches, loc='upper left',
                 facecolor='#1A1A2E', edgecolor='#333',
                 labelcolor='white', fontsize=8)

    ax.axis('off')

    # ── Right: Adjacency Matrix Heatmap ──
    ax2 = axes[1]
    ax2.set_facecolor('#0D0D1A')
    ax2.set_title('Adjacency Matrix — Conflict Relation R',
                 color='white', fontsize=12, fontweight='bold', pad=15,
                 fontfamily='monospace')

    if len(subjects) > 0:
        matrix = build_adjacency_matrix(subjects, conflicts)
        mat_arr = np.array(matrix, dtype=float)
        
        cmap = plt.cm.colors.LinearSegmentedColormap.from_list(
            'custom', ['#0D0D1A', '#7C3AED', '#FC5C7D'])
        
        im = ax2.imshow(mat_arr, cmap=cmap, aspect='auto', vmin=0, vmax=1)
        
        # Grid lines
        ax2.set_xticks(np.arange(len(subjects)))
        ax2.set_yticks(np.arange(len(subjects)))
        short = [s[:7] + ('…' if len(s) > 7 else '') for s in subjects]
        ax2.set_xticklabels(short, rotation=45, ha='right',
                            color='#A78BFA', fontsize=8, fontfamily='monospace')
        ax2.set_yticklabels(short, color='#A78BFA', fontsize=8, fontfamily='monospace')
        
        # Cell values
        for i in range(len(subjects)):
            for j in range(len(subjects)):
                val = matrix[i][j]
                color = '#FFD700' if val == 1 else '#444466'
                ax2.text(j, i, str(val), ha='center', va='center',
                        color=color, fontsize=10, fontweight='bold',
                        fontfamily='monospace')
        
        ax2.spines[:].set_color('#333355')
        ax2.tick_params(colors='#777799')

    plt.tight_layout(pad=2.0)

    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=130,
                facecolor='#0D0D1A', bbox_inches='tight')
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
    print(" /schedule HIT")

    data = request.get_json()

    data = request.get_json()
    data = request.get_json()
    subjects = data.get('subjects', [])
    conflicts = [tuple(c) for c in data.get('conflicts', [])]

    if len(subjects) < 2:
        return jsonify({'error': 'Need at least 2 subjects'}), 400

    # Run all DM algorithms
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
        'subjects': ['Mathematics', 'Physics', 'Chemistry', 'Computer Science',
                     'English', 'Statistics', 'Biology', 'Economics'],
        'conflicts': [
            ['Mathematics', 'Physics'],
            ['Mathematics', 'Chemistry'],
            ['Physics', 'Chemistry'],
            ['Computer Science', 'Mathematics'],
            ['Computer Science', 'Statistics'],
            ['English', 'Biology'],
            ['Statistics', 'Mathematics'],
            ['Statistics', 'Economics'],
            ['Biology', 'Chemistry'],
            ['Economics', 'English']
        ]
    })


if __name__ == '__main__':
    print("\n" + "="*55)
    print("  ExamGrid — Discrete Mathematics IA2 Project")
    print("  Graph Coloring Exam Timetable Scheduler")
    print("="*55)
    print("  Open your browser at: http://127.0.0.1:5000")
    print("="*55 + "\n")
    app.run(debug=True)
