import tkinter as tk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.patches as mpatches  # 新增
from matplotlib.widgets import Slider  # 新增

# Create the main window
root = tk.Tk()
root.title("Emotion Curve Generator")
root.geometry("900x600")

# Set up initial parameters
baseline = 250  # Horizontal middle of the canvas
slider_x = 880  # 固定在右侧
slider_y = baseline  # Start in the middle vertically
curve_points = []  # To store the curve points
is_dragging = False  # To track dragging state

# Create the figure and canvas for drawing the curve
fig, ax = plt.subplots(figsize=(9, 5))
ax.set_xlim(0, 900)
ax.set_ylim(0, 500)
ax.set_facecolor('#eef3f8')

def draw_curve(view_offset=None):
    """Draw the emotion curve and the slider."""
    ax.clear()
    ax.axis('off')
    ax.axhline(baseline, color='#bbb', linewidth=1)

    # Plot the curve
    if curve_points:
        curve_points_x = [p[0] for p in curve_points]
        curve_points_y = [p[1] for p in curve_points]
        end_x = curve_points_x[-1]

        # 始终让末端与滑块重合：右端始终显示曲线终点
        view_offset = max(0, end_x - slider_x)

        x_min = view_offset
        x_max = view_offset + 900
        visible_points = [(x, y) for x, y in zip(curve_points_x, curve_points_y) if x_min <= x <= x_max]
        if visible_points:
            vx, vy = zip(*visible_points)
            ax.fill_between(vx, vy, baseline, where=(np.array(vy) >= baseline), color='#ffd6a3', alpha=0.6)
            ax.fill_between(vx, vy, baseline, where=(np.array(vy) < baseline), color='#8ecbff', alpha=0.6)
            ax.plot(vx, vy, color="#2c6ecb", linewidth=2)

        # Draw the slider (末端重合)
        slider_circle = mpatches.Circle((slider_x + view_offset, curve_points_y[-1]), 14, facecolor="#4a90e2", edgecolor="#fff", lw=2, zorder=10)
        ax.add_patch(slider_circle)
    else:
        view_offset = 0
        slider_circle = mpatches.Circle((slider_x, slider_y), 14, facecolor="#4a90e2", edgecolor="#fff", lw=2, zorder=10)
        ax.add_patch(slider_circle)

    ax.set_title("Drag the slider to generate emotion curve")
    ax.set_xlim(view_offset, view_offset + 900)
    ax.set_ylim(0, 500)
    canvas.draw()

def on_view_slider(val):
    # 禁用自由滑动，始终自动对齐末端
    draw_curve()

def on_drag(event):
    global slider_y, curve_points
    if is_dragging and event.ydata is not None:
        slider_y = np.clip(event.ydata, 10, 490)
        v = baseline - slider_y
        if curve_points:
            new_x = curve_points[-1][0] + 5
        else:
            new_x = 0
        curve_points.append((new_x, baseline - v))
        # 动态调整滑块最大值
        end_x = curve_points[-1][0]
        max_offset = max(0, end_x - 900)
        try:
            view_slider.valmax = max_offset if max_offset > 0 else 1
            view_slider.ax.set_xlim(view_slider.valmin, view_slider.valmax)
            # 若曲线超出右侧，自动对齐末端
            if new_x > 900:
                view_slider.set_val(min(new_x - 900, view_slider.valmax))
                draw_curve(view_offset=min(new_x - 900, view_slider.valmax))
            else:
                draw_curve(view_offset=view_slider.val)
        except Exception:
            draw_curve()

def start_drag(event):
    """Activate dragging on mouse click."""
    global is_dragging
    if event.xdata is not None and event.ydata is not None:
        dist = np.hypot(event.xdata - slider_x, event.ydata - slider_y)
        if dist <= 20:  # Check if the click is near the slider
            is_dragging = True

def end_drag(event):
    """Deactivate dragging on mouse release."""
    global is_dragging
    is_dragging = False

# Bind mouse events to start and stop dragging
canvas_frame = tk.Frame(root)
canvas_frame.pack(fill=tk.BOTH, expand=True)
canvas = FigureCanvasTkAgg(fig, canvas_frame)
canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

canvas.mpl_connect('button_press_event', start_drag)
canvas.mpl_connect('motion_notify_event', on_drag)
canvas.mpl_connect('button_release_event', end_drag)

# 在matplotlib中添加底部滑块
slider_ax = fig.add_axes([0.12, 0.04, 0.76, 0.03])  # [left, bottom, width, height]
view_slider = Slider(slider_ax, 'View', 0, 1, valinit=0, valstep=1)
view_slider.on_changed(on_view_slider)

draw_curve()
root.mainloop()
canvas.mpl_connect('button_press_event', start_drag)
canvas.mpl_connect('motion_notify_event', on_drag)
canvas.mpl_connect('button_release_event', end_drag)

# 在matplotlib中添加底部滑块
slider_ax = fig.add_axes([0.12, 0.04, 0.76, 0.03])  # [left, bottom, width, height]
view_slider = Slider(slider_ax, 'View', 0, 1, valinit=0, valstep=1)
view_slider.on_changed(on_view_slider)

draw_curve()
root.mainloop()
