import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Cursor
from scipy.interpolate import make_interp_spline

# 设置时间点和初始振幅（直线）
time = np.arange(24)  # 24小时
amplitude = np.zeros(24)  # 初始化为0的直线

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(10, 6))

# 绘制初始的平坦曲线（无点，仅线）
line, = ax.plot(time, amplitude, linestyle='-', color='b', label="Emotion Curve")
ax.set_title("Interactive Emotion Curve")
ax.set_xlabel("Time (t) [hours]")
ax.set_ylabel("Amplitude (a)")
ax.grid(False)  # 关闭背景表格

# 存储当前被拖拽的点的索引
dragging_index = None

def update_smooth_curve():
    # 使用样条插值平滑曲线
    xnew = np.linspace(time.min(), time.max(), 200)
    spline = make_interp_spline(time, amplitude, k=3)
    ynew = spline(xnew)
    line.set_data(xnew, ynew)
    # 不再绘制原始点

# 鼠标点击事件，开始拖拽
def on_click(event):
    global dragging_index
    if event.button is MouseButton.LEFT and event.xdata is not None:
        distances = np.abs(time - event.xdata)
        dragging_index = np.argmin(distances)
        print(f"Start dragging point {dragging_index} at time {time[dragging_index]}")

# 鼠标拖动事件，修改选中点的振幅
def on_drag(event):
    if dragging_index is not None and event.ydata is not None:
        amplitude[dragging_index] = event.ydata
        update_smooth_curve()
        fig.canvas.draw()

# 鼠标释放事件，结束拖拽
def on_release(event):
    global dragging_index
    dragging_index = None
    print("Released drag")

# 连接鼠标事件
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('motion_notify_event', on_drag)
fig.canvas.mpl_connect('button_release_event', on_release)

# 初始平滑曲线
update_smooth_curve()

# 显示图形
plt.show()
