from __future__ import annotations

import math
from pathlib import Path

from PySide6.QtCore import QPoint, Qt
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import QWidget

try:
    from OpenGL.GL import (
        GL_BLEND,
        GL_COLOR_BUFFER_BIT,
        GL_DEPTH_BUFFER_BIT,
        GL_DEPTH_TEST,
        GL_LINES,
        GL_LINE_LOOP,
        GL_MODELVIEW,
        GL_ONE_MINUS_SRC_ALPHA,
        GL_PROJECTION,
        GL_QUADS,
        GL_SRC_ALPHA,
        glBegin,
        glBlendFunc,
        glClear,
        glClearColor,
        glColor4f,
        glEnable,
        glEnd,
        glLineWidth,
        glLoadIdentity,
        glMatrixMode,
        glPopMatrix,
        glPushMatrix,
        glRotatef,
        glTranslatef,
        glVertex3f,
        glViewport,
    )
    from OpenGL.GLU import gluPerspective

    OPENGL_AVAILABLE = True
except Exception:
    OPENGL_AVAILABLE = False

from sim.led_model import led_array_positions_mm
from sim.sampler import SimulationResult


class OpenGLView(QOpenGLWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumSize(560, 420)
        self.result: SimulationResult | None = None
        self.x_rot = -22.0
        self.y_rot = 32.0
        self.zoom = 135.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.last_pos = QPoint()

    def set_result(self, result: SimulationResult | None) -> None:
        self.result = result
        self.update()

    def initializeGL(self) -> None:
        if not OPENGL_AVAILABLE:
            return
        glClearColor(0.05, 0.055, 0.06, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    def resizeGL(self, width: int, height: int) -> None:
        if not OPENGL_AVAILABLE:
            return
        height = max(1, height)
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(40.0, width / height, 1.0, 1000.0)
        glMatrixMode(GL_MODELVIEW)

    def paintGL(self) -> None:
        if not OPENGL_AVAILABLE:
            return
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        glTranslatef(self.pan_x, self.pan_y, -self.zoom)
        glRotatef(self.x_rot, 1.0, 0.0, 0.0)
        glRotatef(self.y_rot, 0.0, 1.0, 0.0)
        self._draw_axes()
        self._draw_board_and_leds()
        self._draw_optics()
        self._draw_rays()

    def _draw_axes(self) -> None:
        glLineWidth(2.0)
        glBegin(GL_LINES)
        glColor4f(0.95, 0.25, 0.2, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(30, 0, 0)
        glColor4f(0.2, 0.85, 0.35, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 30, 0)
        glColor4f(0.25, 0.45, 1.0, 1.0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 45)
        glEnd()
        glLineWidth(1.0)

    def _draw_rect_xy(self, cx: float, cy: float, z: float, w: float, h: float, color: tuple[float, float, float, float]) -> None:
        glColor4f(*color)
        glBegin(GL_QUADS)
        glVertex3f(cx - w / 2.0, cy - h / 2.0, z)
        glVertex3f(cx + w / 2.0, cy - h / 2.0, z)
        glVertex3f(cx + w / 2.0, cy + h / 2.0, z)
        glVertex3f(cx - w / 2.0, cy + h / 2.0, z)
        glEnd()

    def _draw_rect_outline_xy(self, z: float, w: float, h: float, color: tuple[float, float, float, float]) -> None:
        glColor4f(*color)
        glBegin(GL_LINE_LOOP)
        glVertex3f(-w / 2.0, -h / 2.0, z)
        glVertex3f(w / 2.0, -h / 2.0, z)
        glVertex3f(w / 2.0, h / 2.0, z)
        glVertex3f(-w / 2.0, h / 2.0, z)
        glEnd()

    def _draw_board_and_leds(self) -> None:
        if self.result is None:
            self._draw_rect_xy(0, 0, -0.8, 70, 36, (0.12, 0.22, 0.20, 1.0))
            return
        cfg = self.result.config
        led = self.result.led_spec
        surface_w = self.result.apparent_surface.diameter_mm or self.result.apparent_surface.width_mm or cfg.apparent_width_mm
        board_w = max(surface_w, abs(cfg.led_spacing_mm) * max(1, cfg.led_count - 1) + 18.0)
        board_h = max(24.0, led.package_mm[1] + 14.0)
        self._draw_rect_xy(0, 0, -0.9, board_w, board_h, (0.10, 0.22, 0.18, 1.0))
        positions = led_array_positions_mm(cfg.led_count, cfg.led_spacing_mm)
        for x, y, _ in positions:
            self._draw_rect_xy(float(x), float(y), 0.0, led.package_mm[0], led.package_mm[1], (0.92, 0.86, 0.56, 1.0))
            self._draw_rect_xy(float(x), float(y), 0.15, led.emitter_mm[0] * 0.55, led.emitter_mm[1] * 0.55, (1.0, 0.98, 0.72, 1.0))

    def _draw_optics(self) -> None:
        if self.result is None:
            return
        cfg = self.result.config
        z = cfg.lens_position_mm if cfg.lens_position_mm is not None else 12.0
        surface = self.result.apparent_surface
        surface_w = surface.diameter_mm or surface.width_mm or cfg.apparent_width_mm
        surface_h = surface.diameter_mm or surface.height_mm or cfg.apparent_height_mm
        if cfg.lens_id != "none" and not cfg.ideal_mode:
            glColor4f(0.42, 0.72, 1.0, 0.48)
            glBegin(GL_LINE_LOOP)
            radius = min(surface_w, surface_h) / 2.0
            for i in range(80):
                a = 2.0 * math.pi * i / 80.0
                glVertex3f(math.cos(a) * radius, math.sin(a) * radius, z)
            glEnd()
        if cfg.diffuser_id != "none":
            self._draw_rect_outline_xy(z + 6.0, surface_w, surface_h, (0.75, 0.95, 1.0, 0.8))
        self._draw_rect_outline_xy(z + 10.0, surface_w, surface_h, (1.0, 0.78, 0.25, 0.75))

    def _draw_rays(self) -> None:
        if self.result is None or self.result.preview_rays is None:
            return
        rays = self.result.preview_rays
        glLineWidth(1.0)
        glBegin(GL_LINES)
        for origin, direction, alive in zip(rays.origins_mm, rays.directions, rays.alive):
            if not alive:
                continue
            end = origin + direction * 80.0
            glColor4f(1.0, 0.86, 0.26, 0.22)
            glVertex3f(float(origin[0]), float(origin[1]), float(origin[2]))
            glVertex3f(float(end[0]), float(end[1]), float(end[2]))
        glEnd()

    def mousePressEvent(self, event) -> None:  # type: ignore[override]
        self.last_pos = event.position().toPoint()

    def mouseMoveEvent(self, event) -> None:  # type: ignore[override]
        pos = event.position().toPoint()
        dx = pos.x() - self.last_pos.x()
        dy = pos.y() - self.last_pos.y()
        buttons = event.buttons()
        if buttons & Qt.LeftButton:
            self.x_rot += dy * 0.4
            self.y_rot += dx * 0.4
        elif buttons & (Qt.RightButton | Qt.MiddleButton):
            self.pan_x += dx * 0.08
            self.pan_y -= dy * 0.08
        self.last_pos = pos
        self.update()

    def wheelEvent(self, event) -> None:  # type: ignore[override]
        delta = event.angleDelta().y() / 120.0
        self.zoom = min(500.0, max(20.0, self.zoom * (0.9 ** delta)))
        self.update()

    def save_snapshot(self, path: str | Path) -> None:
        self.makeCurrent()
        image = self.grabFramebuffer()
        image.save(str(path))
