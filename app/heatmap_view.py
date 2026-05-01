from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from sim.farfield import FarFieldResult


class HeatmapView(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.figure = Figure(figsize=(5.0, 3.5), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.canvas)
        self._draw_empty()

    def _draw_empty(self) -> None:
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        ax.set_xlabel("h [deg]")
        ax.set_ylabel("v [deg]")
        ax.set_title("Far-field luminous intensity [cd]")
        ax.grid(True, alpha=0.25)
        self.canvas.draw_idle()

    def update_farfield(self, farfield: FarFieldResult | None) -> None:
        if farfield is None:
            self._draw_empty()
            return
        self.figure.clear()
        ax = self.figure.add_subplot(111)
        image = ax.imshow(
            farfield.intensity_cd,
            origin="lower",
            extent=[
                farfield.h_edges_deg[0],
                farfield.h_edges_deg[-1],
                farfield.v_edges_deg[0],
                farfield.v_edges_deg[-1],
            ],
            aspect="auto",
            cmap="inferno",
        )
        ax.set_xlabel("Horizontal angle h [deg]")
        ax.set_ylabel("Vertical angle v [deg]")
        ax.set_title("Far-field luminous intensity [cd]")
        ax.axhline(0.0, color="white", linewidth=0.6, alpha=0.55)
        ax.axvline(0.0, color="white", linewidth=0.6, alpha=0.55)
        self.figure.colorbar(image, ax=ax, label="cd")
        self.figure.tight_layout()
        self.canvas.draw_idle()

