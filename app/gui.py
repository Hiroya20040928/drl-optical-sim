from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
    QDoubleSpinBox,
)

from app.heatmap_view import HeatmapView
from app.opengl_view import OpenGLView
from sim.apparent_surface import estimate_apparent_surface
from sim.led_model import LEDSpec
from sim.r148 import R148_H_DEG
from sim.report import save_all_outputs
from sim.sampler import (
    SimulationConfig,
    SimulationResult,
    default_config_for_led,
    load_default_leds,
    load_default_lenses,
    run_simulation,
)


WARNING_TEXT = (
    "注意: 高輝度LEDの直視禁止 / パワーLEDは放熱必須 / "
    "このソフトは設計検討用であり，BWSC提出には実測フォトメトリ，色度測定，"
    "取付図，certifying engineer確認が必要です。"
)


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("BWSC 2025 DRL Optical Simulator")
        self.resize(1380, 860)
        self.leds = load_default_leds()
        self.lenses = load_default_lenses()
        self.result: SimulationResult | None = None

        self.opengl = OpenGLView()
        self.heatmap = HeatmapView()
        self._build_widgets()
        self._populate_databases()
        self._on_led_changed()

    def _build_widgets(self) -> None:
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self.opengl)

        right = QSplitter(Qt.Vertical)
        right.addWidget(self._build_input_panel())
        right.addWidget(self._build_result_tabs())
        right.setStretchFactor(0, 1)
        right.setStretchFactor(1, 2)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        self.setCentralWidget(splitter)
        self.statusBar().showMessage("Ready")

    def _build_input_panel(self) -> QWidget:
        panel = QWidget()
        layout = QVBoxLayout(panel)

        warning = QLabel(WARNING_TEXT)
        warning.setWordWrap(True)
        warning.setStyleSheet("QLabel { background: #fff3cd; color: #3f3200; padding: 8px; border: 1px solid #e0c36a; }")
        layout.addWidget(warning)

        group = QGroupBox("入力パラメータ")
        form = QFormLayout(group)
        form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)

        self.led_combo = QComboBox()
        self.led_combo.currentIndexChanged.connect(self._on_led_changed)
        form.addRow("LED選択", self.led_combo)

        self.led_count = self._spin(1, 64, 1, 2)
        self.led_count.valueChanged.connect(self._update_apparent_surface_preview)
        form.addRow("LED個数", self.led_count)

        self.led_spacing = self._double_spin(0.0, 100.0, 0.1, 8.0, " mm")
        self.led_spacing.valueChanged.connect(self._update_apparent_surface_preview)
        form.addRow("LED間隔", self.led_spacing)

        self.current_ma = self._double_spin(0.0, 1000.0, 1.0, 65.0, " mA")
        form.addRow("駆動電流", self.current_ma)

        self.flux_lm = self._double_spin(0.0, 2000.0, 0.1, 37.0, " lm/LED")
        form.addRow("光束", self.flux_lm)

        self.vf_v = self._double_spin(0.0, 20.0, 0.01, 2.71, " V")
        form.addRow("Vf", self.vf_v)

        self.directivity_deg = self._double_spin(1.0, 180.0, 1.0, 120.0, " deg")
        form.addRow("指向角/FWHM", self.directivity_deg)

        self.lens_combo = QComboBox()
        self.lens_combo.currentIndexChanged.connect(self._on_lens_changed)
        form.addRow("レンズ種類", self.lens_combo)

        self.lens_position = self._double_spin(0.0, 200.0, 0.5, 12.0, " mm")
        form.addRow("レンズ位置", self.lens_position)

        self.diffuser_combo = QComboBox()
        self.diffuser_combo.currentIndexChanged.connect(self._update_apparent_surface_preview)
        form.addRow("拡散板", self.diffuser_combo)

        self.apparent_width = self._double_spin(1.0, 300.0, 1.0, 60.0, " mm")
        self.apparent_width.setEnabled(False)
        form.addRow("見かけ面 幅(自動)", self.apparent_width)

        self.apparent_height = self._double_spin(1.0, 300.0, 1.0, 45.0, " mm")
        self.apparent_height.setEnabled(False)
        form.addRow("見かけ面 高さ/径(自動)", self.apparent_height)

        self.ray_count = self._spin(1000, 1_000_000, 1000, 50_000)
        form.addRow("ray数", self.ray_count)

        self.bin_deg = self._double_spin(0.25, 5.0, 0.25, 1.0, " deg")
        form.addRow("配光ビン", self.bin_deg)

        self.preview_rays = self._spin(0, 20000, 100, 1200)
        form.addRow("ray表示本数", self.preview_rays)

        self.ideal_mode = QCheckBox("R148最小配光 x1.756 の理想モード")
        form.addRow("検証モード", self.ideal_mode)

        layout.addWidget(group)
        buttons = QHBoxLayout()
        self.run_button = QPushButton("計算実行")
        self.run_button.clicked.connect(self.run_clicked)
        self.save_button = QPushButton("結果保存")
        self.save_button.clicked.connect(self.save_clicked)
        buttons.addWidget(self.run_button)
        buttons.addWidget(self.save_button)
        layout.addLayout(buttons)
        layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        return scroll

    def _build_result_tabs(self) -> QWidget:
        tabs = QTabWidget()
        results = QWidget()
        layout = QVBoxLayout(results)

        self.pass_label = QLabel("未計算")
        self.pass_label.setAlignment(Qt.AlignCenter)
        self.pass_label.setStyleSheet("QLabel { font-size: 26px; font-weight: 700; padding: 8px; background: #444; color: white; }")
        layout.addWidget(self.pass_label)

        metrics = QGroupBox("結果")
        metrics_form = QFormLayout(metrics)
        self.metric_labels: dict[str, QLabel] = {}
        for key, label in [
            ("i00", "I(0,0)"),
            ("imax", "Imax"),
            ("phi_exit", "Φexit"),
            ("efficiency", "光学効率"),
            ("source_flux", "入力光束"),
            ("area", "見かけ面積"),
        ]:
            value = QLabel("-")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.metric_labels[key] = value
            metrics_form.addRow(label, value)
        layout.addWidget(metrics)

        self.r148_table = QTableWidget(5, len(R148_H_DEG))
        self.r148_table.setHorizontalHeaderLabels([f"h={h:.0f}" for h in R148_H_DEG])
        self.r148_table.setVerticalHeaderLabels(["v=+10", "v=+5", "v=0", "v=-5", "v=-10"])
        self.r148_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.r148_table, 1)

        note = QLabel("OpenGLの明るさ表示は判定に使いません。判定は数値計算された光度[cd]で行います。")
        note.setWordWrap(True)
        layout.addWidget(note)

        tabs.addTab(results, "R148判定")
        tabs.addTab(self.heatmap, "配光ヒートマップ")
        return tabs

    def _spin(self, minimum: int, maximum: int, step: int, value: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setValue(value)
        return spin

    def _double_spin(self, minimum: float, maximum: float, step: float, value: float, suffix: str = "") -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimum, maximum)
        spin.setSingleStep(step)
        spin.setDecimals(3)
        spin.setValue(value)
        spin.setSuffix(suffix)
        return spin

    def _populate_databases(self) -> None:
        self.led_combo.clear()
        for led in self.leds:
            self.led_combo.addItem(led.name, led.id)

        self.lens_combo.clear()
        for lens in self.lenses:
            if lens.get("kind") in {"none", "thin_collimator", "spherical", "ideal_r148", "r148_lower_bound"}:
                self.lens_combo.addItem(str(lens["name"]), str(lens["id"]))

        self.diffuser_combo.clear()
        self.diffuser_combo.addItem("なし", "none")
        for lens in self.lenses:
            if lens.get("kind") in {"plane_diffuser", "milky_acrylic"}:
                self.diffuser_combo.addItem(str(lens["name"]), str(lens["id"]))

    def _current_led(self) -> LEDSpec:
        led_id = self.led_combo.currentData()
        for led in self.leds:
            if led.id == led_id:
                return led
        return self.leds[0]

    def _current_lens_spec(self) -> dict:
        lens_id = self.lens_combo.currentData()
        return next((dict(item) for item in self.lenses if item.get("id") == lens_id), {"id": "none", "name": "Lensなし"})

    def _current_diffuser_spec(self) -> dict | None:
        diffuser_id = self.diffuser_combo.currentData()
        if diffuser_id == "none":
            return None
        return next((dict(item) for item in self.lenses if item.get("id") == diffuser_id), None)

    def _update_apparent_surface_preview(self) -> None:
        if not self.leds or self.led_combo.count() == 0:
            return
        try:
            surface = estimate_apparent_surface(
                self._current_led(),
                self.led_count.value(),
                self.led_spacing.value(),
                self._current_lens_spec(),
                self._current_diffuser_spec(),
            )
        except Exception:
            return
        if surface.diameter_mm is not None:
            self.apparent_width.setValue(surface.diameter_mm)
            self.apparent_height.setValue(surface.diameter_mm)
        elif surface.width_mm is not None and surface.height_mm is not None:
            self.apparent_width.setValue(surface.width_mm)
            self.apparent_height.setValue(surface.height_mm)
        tip = f"{surface.area_cm2:.2f} cm2 / {surface.source}"
        self.apparent_width.setToolTip(tip)
        self.apparent_height.setToolTip(tip)

    def _on_led_changed(self) -> None:
        led = self._current_led()
        cfg = default_config_for_led(led)
        self.led_count.setValue(cfg.led_count)
        self.current_ma.setValue(cfg.current_ma)
        self.flux_lm.setValue(led.flux_typ_lm)
        self.vf_v.setValue(led.vf_typ_v)
        self.directivity_deg.setValue(led.directivity_deg)
        default_spacing = max(led.package_mm[0] + 2.0, 8.0)
        self.led_spacing.setValue(default_spacing)
        if led.id == "cree_xhp70b_00_0000_0d0bn440e":
            idx = self.lens_combo.findData("cree_xhp70b_r148_lower_bound_60x45")
            if idx >= 0:
                self.lens_combo.setCurrentIndex(idx)
        self._update_apparent_surface_preview()

    def _on_lens_changed(self) -> None:
        lens_id = self.lens_combo.currentData()
        lens = next((item for item in self.lenses if item.get("id") == lens_id), None)
        if lens is None:
            return
        self.ideal_mode.setChecked(lens.get("kind") == "ideal_r148")
        if "position_mm" in lens:
            self.lens_position.setValue(float(lens["position_mm"]))
        self._update_apparent_surface_preview()

    def _build_config(self) -> SimulationConfig:
        lens_id = str(self.lens_combo.currentData())
        lens = next((item for item in self.lenses if item.get("id") == lens_id), {})
        ideal = self.ideal_mode.isChecked() or lens.get("kind") == "ideal_r148"
        return SimulationConfig(
            led_id=str(self.led_combo.currentData()),
            led_count=self.led_count.value(),
            led_spacing_mm=self.led_spacing.value(),
            current_ma=self.current_ma.value(),
            flux_typ_lm=self.flux_lm.value(),
            vf_typ_v=self.vf_v.value(),
            directivity_deg=self.directivity_deg.value(),
            lens_id=lens_id,
            lens_position_mm=self.lens_position.value(),
            diffuser_id=str(self.diffuser_combo.currentData()),
            apparent_width_mm=self.apparent_width.value(),
            apparent_height_mm=self.apparent_height.value(),
            ray_count=self.ray_count.value(),
            bin_deg=self.bin_deg.value(),
            preview_ray_count=self.preview_rays.value(),
            ideal_mode=ideal,
        )

    def run_clicked(self) -> None:
        config = self._build_config()
        self.statusBar().showMessage("Calculating rays...")
        self.run_button.setEnabled(False)
        QApplication.setOverrideCursor(Qt.WaitCursor)
        QApplication.processEvents()
        try:
            self.result = run_simulation(config, self.leds, self.lenses)
        except Exception as exc:
            QMessageBox.critical(self, "計算エラー", str(exc))
            self.statusBar().showMessage("Error")
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.run_button.setEnabled(True)

        self._update_results()
        self.opengl.set_result(self.result)
        self.heatmap.update_farfield(self.result.farfield)
        self.statusBar().showMessage("Done")

    def _update_results(self) -> None:
        if self.result is None:
            return
        ff = self.result.farfield
        ev = self.result.r148
        passed = ev.overall_passed
        ideal = self.result.config.ideal_mode or self.result.config.lens_id == "ideal_r148_1p756"
        lower_bound = self.result.config.lens_id == "cree_xhp70b_r148_lower_bound_60x45"
        if ideal:
            label = "IDEAL PASS" if passed else "IDEAL FAIL"
        elif lower_bound:
            label = "TARGET PASS" if passed else "TARGET FAIL"
        else:
            label = "PASS" if passed else "FAIL"
        self.pass_label.setText(label)
        self.pass_label.setStyleSheet(
            "QLabel { font-size: 26px; font-weight: 700; padding: 8px; "
            + (
                "background: #8a6d1f; color: white; }"
                if ideal
                else "background: #4b6f9e; color: white; }"
                if lower_bound
                else ("background: #167a3b; color: white; }" if passed else "background: #a22a2a; color: white; }")
            )
        )
        self.metric_labels["i00"].setText(f"{ff.center_intensity_cd:.2f} cd")
        self.metric_labels["imax"].setText(f"{ff.imax_cd:.2f} cd / limit {ev.max_cd_limit:.0f} cd")
        self.metric_labels["phi_exit"].setText(f"{ff.phi_exit_lm:.3f} lm")
        self.metric_labels["efficiency"].setText(f"{self.result.optical_efficiency * 100.0:.2f} %")
        self.metric_labels["source_flux"].setText(f"{self.result.source_flux_lm:.3f} lm")
        self.metric_labels["area"].setText(f"{ev.apparent_area_cm2:.2f} cm2 / 25-200 cm2")
        self.metric_labels["area"].setToolTip(f"{self.result.apparent_surface.label} / {self.result.apparent_surface.source}")
        if self.result.apparent_surface.diameter_mm is not None:
            self.apparent_width.setValue(self.result.apparent_surface.diameter_mm)
            self.apparent_height.setValue(self.result.apparent_surface.diameter_mm)
        elif self.result.apparent_surface.width_mm is not None and self.result.apparent_surface.height_mm is not None:
            self.apparent_width.setValue(self.result.apparent_surface.width_mm)
            self.apparent_height.setValue(self.result.apparent_surface.height_mm)

        by_point = {(p.h_deg, p.v_deg): p for p in ev.points}
        display_v = [10.0, 5.0, 0.0, -5.0, -10.0]
        for row, v in enumerate(display_v):
            for col, h in enumerate(R148_H_DEG):
                point = by_point[(float(h), v)]
                text = f"{point.measured_cd:.1f}/{point.min_cd:.0f}\n{'PASS' if point.passed else 'FAIL'}"
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setBackground(QColor("#d6f5d6") if point.passed else QColor("#ffd6d6"))
                self.r148_table.setItem(row, col, item)
        self.r148_table.resizeRowsToContents()

    def save_clicked(self) -> None:
        if self.result is None:
            self.run_clicked()
            if self.result is None:
                return
        out_dir = QFileDialog.getExistingDirectory(self, "保存先フォルダを選択", str(Path.cwd()))
        if not out_dir:
            return
        try:
            paths = save_all_outputs(self.result, out_dir, self.opengl.save_snapshot)
        except Exception as exc:
            QMessageBox.critical(self, "保存エラー", str(exc))
            return
        QMessageBox.information(self, "保存完了", "\n".join(str(path) for path in paths.values()))
