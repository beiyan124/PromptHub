# -*- coding: utf-8 -*-
"""磨砂透明背景层：显示用户选择的图片（或内置默认背景），高斯模糊 + 深色遮罩。

- 原始图（_source）与模糊结果（_blurred）分离缓存：
  换图 → 重新加载；调模糊强度 → 仅重新模糊；调遮罩 → 仅重绘
- force_render() 清空缓存强制重渲染（供设置页「重新渲染」按钮与异常恢复）
- 绘制带容错，任何异常回退到深色底，不影响主流程
"""

import os

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QColor, QImage, QLinearGradient, QPainter, QPixmap
from PySide6.QtWidgets import QWidget


# ---------------------------------------------------------------------------
# 算法：模糊半径（线性曲线）与遮罩深度（0-100 线性 alpha）
# ---------------------------------------------------------------------------
def blur_radius(slider):
    """模糊强度滑块（0-50）→ 高斯模糊半径（线性）。

    采用线性曲线：y = (50/3) · x/50 = x/3
    - 全程等斜率：x=1 → 0.33（几乎无模糊），x=10 → 3.33，x=25 → 8.33
    - 拉满（50）时半径 = 线性高斯模糊（半径50）的三分之一 ≈ 16.67
    - 低档位的"突变感"由 _blur_pixmap 的浮点插值解决（1 档真的几乎无模糊）
    """
    x = max(0.0, min(50.0, float(slider)))
    return (50.0 / 3.0) * (x / 50.0)


def dim_alpha(slider):
    """遮罩深度滑块（0-100）→ 黑色遮罩 alpha（0-128）。

    0 = 无遮罩，画面亮度 = 图片本身亮度；
    100 时 alpha=128，画面亮度约为无遮罩时的一半（1 - 128/255 ≈ 0.5）。
    """
    s = max(0.0, min(100.0, float(slider)))
    return int(s * 128.0 / 100.0)


class FrostedPanel(QWidget):
    """磨砂面板容器：自绘半透明深色底。

    QSS 背景色在 WA_TranslucentBackground 下不会被绘制，因此半透明底色必须自绘，
    这是 Qt 中让面板透出底层背景图最可靠的方式。
    """

    def __init__(self, parent=None, color=(28, 23, 18, 165)):
        super().__init__(parent)
        self._frost_color = QColor(*color)
        self.setAttribute(Qt.WA_TranslucentBackground, True)  # 自绘 alpha 混合到背景层
        self.setAttribute(Qt.WA_StyledBackground, False)

    def set_frost_color(self, r, g, b, a):
        self._frost_color = QColor(r, g, b, a)
        self.update()

    def set_panel_alpha(self, alpha):
        """设置面板底色不透明度（0-255）：0 = 几乎全透明（透出背景），255 = 完全不透明。"""
        c = self._frost_color
        self._frost_color = QColor(c.red(), c.green(), c.blue(),
                                   max(0, min(255, int(alpha))))
        self.update()

    def paintEvent(self, ev):
        p = QPainter(self)
        p.fillRect(self.rect(), self._frost_color)
        p.end()


class BlurBackground(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._image_path = ""
        self._source = None        # 原始（未模糊）QPixmap
        self._blurred = None       # 模糊后的 QPixmap
        self._enabled = False
        self._blur = 24
        self._dim = 0
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

    # ---------- 配置 ----------
    def apply(self, settings, force=False):
        """根据设置更新背景。force=True 时清空缓存强制重渲染。"""
        enabled = bool(settings.get("enabled", False))
        blur = max(0, min(50, int(settings.get("blur", 24))))      # 滑块值 0-50
        dim = max(0, min(100, int(settings.get("dim", 0))))        # 滑块值 0-100（默认 0 = 无遮罩）
        path = settings.get("image", "") or ""

        # 换图 / 强制 → 重新加载原始图；加载失败或无图时用内置默认背景
        if force or path != self._image_path:
            self._image_path = path
            self._source = self._load_source(path)
            if self._source is None:
                self._source = self._make_default_source()
        if self._source is None and enabled:
            self._source = self._make_default_source()

        # 需要重新模糊：换图/强制/滑块值变化/无缓存（半径经线性曲线映射）
        need_reblur = force or self._blurred is None or blur != self._blur

        self._enabled = enabled
        self._blur = blur
        self._dim = dim
        if enabled and need_reblur and self._source is not None:
            self._blurred = self._blur_pixmap(self._source, blur_radius(blur))
        elif not enabled:
            self._blurred = None
        self.update()

    def force_render(self):
        """强制重渲染（清空缓存，下次 apply 或手动重载）。"""
        self._source = None
        self._blurred = None
        self._image_path = ""
        self.update()

    # ---------- 图片加载 ----------
    def _load_source(self, path):
        if not path or not os.path.isfile(path):
            return None
        img = QImage(path)
        if img.isNull():
            return None
        return QPixmap.fromImage(img)

    def _make_default_source(self):
        """内置默认背景：深空蓝渐变 + 光点。"""
        w, h = 900, 560
        pix = QPixmap(w, h)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        grad = QLinearGradient(0, 0, w, h)
        grad.setColorAt(0.0, QColor(24, 44, 84))
        grad.setColorAt(0.55, QColor(12, 28, 60))
        grad.setColorAt(1.0, QColor(7, 20, 48))
        p.fillRect(QRectF(0, 0, w, h), grad)
        p.setPen(Qt.NoPen)
        spots = [(150, 120, 3, QColor(70, 150, 255, 100)),
                 (700, 100, 4, QColor(0, 210, 255, 90)),
                 (780, 430, 3, QColor(70, 150, 255, 80)),
                 (120, 460, 2, QColor(0, 210, 255, 70)),
                 (450, 280, 2, QColor(100, 170, 255, 55))]
        for x, y, r, c in spots:
            p.setBrush(c)
            p.drawEllipse(x - r, y - r, r * 2, r * 2)
        p.end()
        return pix

    # ---------- 纯 Python 高斯近似模糊（3 次 box-blur，滑动窗口 O(n)） ----------
    @staticmethod
    def _box1d_slide(raw, n, stride, offset, r):
        """对通道数据做一次 1D box blur（滑动窗口，O(n)），原地写入 raw。

        raw: bytearray，通道数据位于 offset + i*stride（i=0..n-1）
        读取使用原始数据副本（避免原地写入污染滑动窗口）；
        边界用窗口收缩处理（等价反射填充），输出无位移。
        """
        vals = [raw[offset + i * stride] for i in range(n)]   # 原始副本
        window = 0
        cnt = 0
        end = min(r, n - 1)
        for i in range(end + 1):
            window += vals[i]
            cnt += 1
        for i in range(n):
            raw[offset + i * stride] = window // cnt
            add = i + 1 + r
            rem = i - r
            if add < n:
                window += vals[add]
                cnt += 1
            if rem >= 0:
                window -= vals[rem]
                cnt -= 1

    def _box_pass(self, raw, w, h, r):
        """一次 2D box blur：先水平后垂直，作用于 BGRA 四通道。"""
        for ch in range(4):
            for y in range(h):
                self._box1d_slide(raw, w, 4, y * w * 4 + ch, r)
            for x in range(w):
                self._box1d_slide(raw, h, w * 4, x * 4 + ch, r)

    @staticmethod
    def _mix_bytes(a, b, w, h, f):
        """按权重 f 线性混合两个 BGRA 字节数组（b 占 f），返回新数组。"""
        g = 1.0 - f
        n = w * h * 4
        out = bytearray(n)
        for i in range(n):
            out[i] = int(a[i] * g + b[i] * f + 0.5)
        return out

    def _blur_pixmap(self, pix, radius):
        """对 pixmap 施加高斯近似模糊（3 次 box-blur），返回与原图同尺寸结果。

        - 纯计算实现，无位移、不裁剪、边界用窗口收缩处理
        - 半径经线性曲线映射（blur_radius）：
          · radius < 2px（滑块 1~5）：肉眼不可见，直接返回原图 —— 低档位
            零模糊、零伪影（避免降采样放大插值引入额外混色/位移感）
          · 2 ≤ radius：降采样到 160px 宽工作图控制计算量（纯 Python 实时）
          · 工作图半径 < 1 时用「原图 ↔ 半径1模糊」线性混合，等效原图半径
            = r_work·k = radius，与整数半径路径连续衔接，无跳变
        """
        if radius <= 0:
            return pix
        try:
            src_w = pix.width()
            # 低档位：<2px 的模糊在屏幕上不可见，直接返回原图
            if radius < 2.0:
                return pix
            k = src_w / 160.0
            if k > 1.02:
                work = pix.scaled(160, max(1, int(pix.height() / k)),
                                  Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            else:
                work = pix
                k = 1.0
            w, h = work.width(), work.height()
            r_work = radius / k                        # 工作图上的浮点半径
            img = work.toImage().convertToFormat(QImage.Format_ARGB32)
            raw = bytearray(img.constBits())
            if r_work < 1.0:
                # 亚像素模糊：原图 ↔ 半径1模糊 线性混合（等效原图半径 = r_work·k = radius）
                f = r_work
                raw1 = bytearray(raw)
                for _ in range(3):
                    self._box_pass(raw1, w, h, 1)
                out_img = QImage(bytes(self._mix_bytes(raw, raw1, w, h, f)),
                                 w, h, w * 4, QImage.Format_ARGB32).copy()
                blurred = QPixmap.fromImage(out_img)
            else:
                r = int(r_work + 0.5)
                if r < 1:
                    r = 1
                for _ in range(3):
                    self._box_pass(raw, w, h, r)
                blurred = QPixmap.fromImage(
                    QImage(bytes(raw), w, h, w * 4, QImage.Format_ARGB32).copy())
            if k > 1.02:
                blurred = blurred.scaled(src_w, pix.height(),
                                         Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
            return blurred
        except Exception:
            return pix

    # ---------- 绘制 ----------
    def paintEvent(self, ev):
        try:
            p = QPainter(self)
            if not self._enabled or self._blurred is None:
                p.fillRect(self.rect(), "#0B0F14")
                p.end()
                return
            pw, ph = self._blurred.width(), self._blurred.height()
            if pw <= 0 or ph <= 0:
                p.fillRect(self.rect(), "#0B0F14")
                p.end()
                return
            w, h = self.width(), self.height()
            scale = max(w / pw, h / ph)
            dw, dh = int(pw * scale + 0.5), int(ph * scale + 0.5)
            x = (w - dw) // 2
            y = (h - dh) // 2
            p.drawPixmap(x, y, dw, dh, self._blurred)
            if self._dim > 0:
                p.fillRect(self.rect(), QColor(0, 0, 0, dim_alpha(self._dim)))
            p.end()
        except Exception:
            try:
                p = QPainter(self)
                p.fillRect(self.rect(), "#0B0F14")
                p.end()
            except Exception:
                pass
