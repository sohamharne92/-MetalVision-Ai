"""
METALVISION AI - CNN Pipeline Visualization Module
Vintage Industrial Theme — aged copper · amber glow · worn steel
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import streamlit as st

# ── Vintage palette ────────────────────────────────────────────────────────────
BG       = "#1a1108"
BG2      = "#221608"
PANEL    = "#2a1e0e"
BORDER   = "#5a3a18"
COPPER   = "#b87333"
COPPER_L = "#d4904a"
COPPER_D = "#8a5520"
AMBER    = "#f59e0b"
TEXT     = "#e8d5b0"
TEXT2    = "#a08060"
ACCEPT   = "#4ade80"
REJECT   = "#f87171"
INDIGO   = "#818cf8"

PIPELINE_STAGES = [
    {"name": "Input\nImage",      "desc": "Raw camera frame\n640×480 RGB",     "color": COPPER_D},
    {"name": "Channel\nSplit",    "desc": "RGB → Grayscale\n+ Edge Map",        "color": "#7a5a30"},
    {"name": "Conv\nLayer 1",     "desc": "32 filters 3×3\nReLU activation",   "color": COPPER},
    {"name": "Pool\nLayer 1",     "desc": "MaxPool 2×2\nStride 2",             "color": COPPER_D},
    {"name": "Conv\nLayer 2",     "desc": "64 filters 3×3\nReLU activation",   "color": COPPER},
    {"name": "Pool\nLayer 2",     "desc": "MaxPool 2×2\nStride 2",             "color": COPPER_D},
    {"name": "Fully\nConnected",  "desc": "512 neurons\nDropout 0.5",          "color": INDIGO},
    {"name": "Output\nClass",     "desc": "4 classes\nSoftmax",                "color": ACCEPT},
]

STEP_COLORS = [COPPER_D, "#7a5a30", COPPER, COPPER_D, COPPER, COPPER_D, AMBER, ACCEPT]

PLOTLY_BASE = dict(
    paper_bgcolor=BG2,
    plot_bgcolor=BG2,
    font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
    margin=dict(l=10, r=10, t=46, b=10),
)


class DualChannelCNNVisualizer:
    """All CNN pipeline visualizations — vintage industrial style."""

    # ── Pipeline flowchart ────────────────────────────────────────────────────
    def create_pipeline_flowchart(self) -> go.Figure:
        fig = go.Figure()
        n = len(PIPELINE_STAGES)
        x_pos = [i * 1.3 for i in range(n)]
        y0, box_w, box_h = 0.0, 0.9, 0.6

        for i, stage in enumerate(PIPELINE_STAGES):
            x = x_pos[i]
            # Box fill
            fig.add_shape(
                type="rect",
                x0=x - box_w/2, y0=y0 - box_h/2,
                x1=x + box_w/2, y1=y0 + box_h/2,
                fillcolor=stage["color"],
                line=dict(color=COPPER_L, width=1),
                opacity=0.9,
            )
            # Label
            fig.add_annotation(
                x=x, y=y0 + 0.05,
                text=f"<b>{stage['name']}</b>",
                showarrow=False,
                font=dict(color="white", size=10, family="Space Grotesk"),
                align="center",
            )
            # Description below
            fig.add_annotation(
                x=x, y=y0 - box_h/2 - 0.22,
                text=stage["desc"],
                showarrow=False,
                font=dict(color=TEXT2, size=7.5, family="JetBrains Mono"),
                align="center",
            )
            # Arrow
            if i < n - 1:
                fig.add_annotation(
                    x=x_pos[i+1] - box_w/2 - 0.02, y=y0,
                    ax=x + box_w/2 + 0.02,           ay=y0,
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True, arrowhead=2, arrowsize=1,
                    arrowwidth=2, arrowcolor=AMBER,
                )

        fig.update_layout(
            **PLOTLY_BASE,
            title=dict(
                text="Dual-Channel CNN Pipeline — 8 Stages",
                font=dict(color=COPPER_L, size=13, family="Space Grotesk"),
                x=0.5,
            ),
            xaxis=dict(range=[-0.8, x_pos[-1]+0.8], visible=False),
            yaxis=dict(range=[-0.8, 0.7], visible=False),
            height=280,
        )
        return fig

    # ── Processing steps ──────────────────────────────────────────────────────
    def create_processing_steps_diagram(self) -> go.Figure:
        steps = [
            ("1", "Capture",    "Camera frame"),
            ("2", "Preprocess", "Normalise + resize"),
            ("3", "Edge Detect","Sobel / Canny"),
            ("4", "Augment",    "Flip / rotate"),
            ("5", "Extract",    "Feature maps"),
            ("6", "Classify",   "4-class CNN"),
            ("7", "Threshold",  "Confidence ≥ 0.7"),
            ("8", "Decision",   "ACCEPT / REJECT"),
        ]
        fig = go.Figure()
        n, xs = len(steps), list(range(len(steps)))

        for i, (num, title, desc) in enumerate(steps):
            fig.add_trace(go.Scatter(
                x=[xs[i]], y=[0.6],
                mode="markers+text",
                marker=dict(size=44, color=STEP_COLORS[i],
                            line=dict(color=COPPER_L, width=1.5)),
                text=[f"<b>{num}</b>"],
                textfont=dict(color="white", size=14, family="JetBrains Mono"),
                textposition="middle center",
                showlegend=False, hoverinfo="skip",
            ))
            fig.add_annotation(x=xs[i], y=0.14,
                text=f"<b>{title}</b>", showarrow=False,
                font=dict(color=COPPER_L, size=9, family="Space Grotesk"))
            fig.add_annotation(x=xs[i], y=-0.1,
                text=desc, showarrow=False,
                font=dict(color=TEXT2, size=7.5, family="JetBrains Mono"))
            if i < n - 1:
                fig.add_annotation(
                    x=xs[i+1]-0.45, y=0.6,
                    ax=xs[i]+0.45,  ay=0.6,
                    xref="x", yref="y", axref="x", ayref="y",
                    showarrow=True, arrowhead=2, arrowsize=1,
                    arrowwidth=1.5, arrowcolor=AMBER,
                )

        fig.update_layout(
            **PLOTLY_BASE,
            title=dict(text="Processing Steps",
                       font=dict(color=COPPER_L, size=13, family="Space Grotesk"), x=0.5),
            xaxis=dict(range=[-0.6, n-0.4], visible=False),
            yaxis=dict(range=[-0.3, 1.0], visible=False),
            height=220,
        )
        return fig

    # ── Channel comparison ────────────────────────────────────────────────────
    def create_channel_comparison(self, width: int = 64, height: int = 64) -> go.Figure:
        rng = np.random.default_rng(42)

        original = np.zeros((height, width))
        for row in range(height):
            original[row] = np.linspace(0.2, 0.8, width) + rng.normal(0, 0.05, width)
        original = np.clip(original, 0, 1)

        edge = np.zeros((height, width))
        for row in range(height):
            edge[row] = np.clip(np.abs(np.gradient(original[row])) * 10, 0, 1)
        for _ in range(3):
            r = rng.integers(5, height-5)
            cs, ce = rng.integers(5, width//2), rng.integers(width//2, width-5)
            edge[r, cs:ce] = np.clip(edge[r, cs:ce] + rng.uniform(0.5, 1.0), 0, 1)

        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Ch 1 — Original (Grayscale)", "Ch 2 — Edge Map"),
        )
        # Update subplot title fonts
        for ann in fig.layout.annotations:
            ann.font = dict(color=COPPER_L, family="Space Grotesk", size=11)

        fig.add_trace(go.Heatmap(z=original, colorscale=[
            [0, BG], [1, COPPER_L]], showscale=False, hoverinfo="skip"), row=1, col=1)
        fig.add_trace(go.Heatmap(z=edge, colorscale=[
            [0, BG2], [0.5, AMBER], [1, REJECT]], showscale=False, hoverinfo="skip"), row=1, col=2)

        fig.update_layout(
            paper_bgcolor=BG2,
            plot_bgcolor=BG2,
            font=dict(color=TEXT, family="Space Grotesk, sans-serif"),
            title=dict(
                text="Dual-Channel CNN Input Visualisation",
                font=dict(color=COPPER_L, size=13, family="Space Grotesk"), x=0.5,
            ),
            height=300,
            margin=dict(l=10, r=10, t=60, b=10),
        )
        for axis in ["xaxis", "xaxis2", "yaxis", "yaxis2"]:
            fig.update_layout(**{axis: dict(visible=False)})
        return fig

    # ── Inline HTML pipeline strip ────────────────────────────────────────────
    def render_pipeline_html(self) -> str:
        stages_html = ""
        for i, stage in enumerate(PIPELINE_STAGES):
            arrow = f"<div style='color:{AMBER};font-size:16px;font-weight:700;'>→</div>" \
                    if i < len(PIPELINE_STAGES) - 1 else ""
            stages_html += f"""
            <div style='background:{stage["color"]}33;border:1px solid {stage["color"]};
                        border-radius:3px;padding:8px 10px;text-align:center;
                        min-width:72px;font-family:Oswald,sans-serif;font-size:10px;
                        color:white;font-weight:600;letter-spacing:0.08em;
                        text-transform:uppercase;'>
              {stage["name"].replace(chr(10), "<br>")}
            </div>
            {arrow}
            """
        return f"""
        <div style='display:flex;align-items:center;flex-wrap:wrap;gap:4px;
                    background:{BG2};padding:12px 14px;border-radius:4px;
                    border:1px solid {BORDER};'>
          {stages_html}
        </div>"""

    # ── Streamlit render entry point ──────────────────────────────────────────
    def display_cnn_pipeline_visualization(self):
        st.markdown(
            f"<div class='v-section-title'>Dual-Channel CNN Pipeline</div>",
            unsafe_allow_html=True,
        )

        tab1, tab2, tab3 = st.tabs(
            ["Pipeline Flowchart", "Processing Steps", "Channel Comparison"]
        )
        with tab1:
            st.plotly_chart(self.create_pipeline_flowchart(), use_container_width=True)
        with tab2:
            st.plotly_chart(self.create_processing_steps_diagram(), use_container_width=True)
        with tab3:
            st.plotly_chart(self.create_channel_comparison(), use_container_width=True)
            st.markdown(
                f"""<div style='font-family:Share Tech Mono,monospace;font-size:0.72rem;
                color:{TEXT2};padding:8px 12px;background:{BG2};border:1px solid {BORDER};
                border-left:3px solid {AMBER};border-radius:3px;margin-top:6px;'>
                The CNN processes two parallel channels: the raw grayscale image and a
                Sobel/Canny edge map. Feature maps from both channels are concatenated
                before the fully-connected layers to improve defect localisation.
                </div>""",
                unsafe_allow_html=True,
            )
