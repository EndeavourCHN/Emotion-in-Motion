import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Cursor
# Change: Import PchipInterpolator instead of make_interp_spline
from scipy.interpolate import PchipInterpolator 

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'FangSong', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置时间点和初始振幅（直线）
time = np.arange(24)  # 24小时
amplitude = np.zeros(24)  # 初始化为0的直线

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(10, 6))

# 绘制初始的平坦曲线（无点，仅线）
# 修改: 将初始颜色从'yellow'改为'gray'
line, = ax.plot(time, amplitude, linestyle='-', color='gray', label="Emotion Curve")
# 添加: 在y=0处绘制浅灰色虚线作为基准线
ax.axhline(y=0, color='lightgray', linestyle='--', linewidth=1)
ax.set_title("Interactive Emotion Curve (Fixed with Pchip)") # Changed title for clarity
ax.set_xlabel("Time (t) [hours]")
ax.set_ylabel("Amplitude (a)")
ax.grid(False)  # 关闭背景表格

# 修改: 去除外侧坐标框线
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)

# 修改: 更改左侧坐标标签为难过、一般、高兴
ax.set_yticks([-2, 0, 2])
ax.set_yticklabels(['难过', '一般', '高兴'])

# 存储当前被拖拽的点的索引
dragging_index = None

# 添加一个变量来存储当前的LineCollection对象
current_lc = None

def update_smooth_curve():
    global current_lc
    # Change: Use PchipInterpolator for a shape-preserving, non-oscillatory curve
    xnew = np.linspace(time.min(), time.max(), 200)
    # Change: Create the Pchip interpolator object
    spline = PchipInterpolator(time, amplitude)
    # Change: Evaluate the Pchip interpolator at the new points
    ynew = spline(xnew)
    
    # 根据振幅值改变曲线颜色 - 使用渐变色
    # 修改: 实现基于点高度的连续颜色渐变
    colors = []
    # 确定y值范围用于颜色映射
    y_min, y_max = ynew.min(), ynew.max()
    # 如果所有值相同，使用默认灰色
    if y_min == y_max:
        colors = ['gray'] * len(ynew)
    else:
        # 创建颜色映射: 负值为蓝色，零值为灰色，正值为绿色
        for val in ynew:
            # 归一化值到[0, 1]范围
            norm_val = (val - y_min) / (y_max - y_min)
            # 使用matplotlib的colormap实现平滑渐变
            if val < 0:
                # 负值: 灰色到蓝色渐变
                t = abs(val) / max(abs(y_min), abs(y_max), 1e-5)  # 防止除零
                # 灰色RGB(0.5, 0.5, 0.5) 到 蓝色RGB(0, 0, 1)
                r = 0.5 * (1 - t)
                g = 0.5 * (1 - t)
                b = 0.5 * (1 - t) + t
            elif val > 0:
                # 正值: 灰色到绿色渐变
                t = val / max(abs(y_min), abs(y_max), 1e-5)  # 防止除零
                # 灰色RGB(0.5, 0.5, 0.5) 到 绿色RGB(0, 1, 0)
                r = 0.5 * (1 - t)
                g = 0.5 * (1 - t) + t
                b = 0.5 * (1 - t)
            else:
                # 零值: 灰色
                r, g, b = 0.5, 0.5, 0.5
            colors.append((r, g, b))
    
    # 如果所有颜色都是灰色(初始状态)，则保持线条为灰色
    # 修改: 将判断条件从'brown'改为'gray'
    if all(c == 'gray' for c in colors):
        # 删除之前添加的LineCollection
        if current_lc is not None:
            current_lc.remove()
            current_lc = None
        line.set_data(xnew, ynew)
        line.set_color('gray')
    else:
        # 设置颜色映射
        # 修改: 改进颜色处理逻辑，创建颜色数组用于线段着色
        # 由于matplotlib line不直接支持多色线段，我们保持使用单一颜色或使用颜色映射
        # 修改: 实现根据数值变化的颜色渲染功能
        # 使用Collection来实现多色线条
        from matplotlib.collections import LineCollection
        points = np.array([xnew, ynew]).T.reshape(-1, 1, 2)
        segments = np.concatenate([points[:-1], points[1:]], axis=1)
        
        # 删除之前添加的LineCollection
        if current_lc is not None:
            current_lc.remove()
        
        lc = LineCollection(segments, colors=colors[:-1], linewidths=2)
        ax.add_collection(lc)
        current_lc = lc
        
        # 移除旧的线条
        line.set_data([], [])
        
        # 重新绘制
        ax.relim()
        ax.autoscale_view()

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
        # Clamp the ydata to prevent the amplitude from going too far
        # This is optional but can also help visually
        # amplitude[dragging_index] = np.clip(event.ydata, -5, 5) 
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