import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Slider
from scipy.interpolate import PchipInterpolator
from matplotlib.collections import LineCollection
# 新增: 导入必要的库
import matplotlib.patheffects as pe # 用于让标签更清晰
import time as time_module # 避免与numpy的time冲突

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei', 'FangSong', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

# 设置时间点和初始振幅（直线）
time = np.arange(24)  # 24小时
amplitude = np.zeros(24)  # 初始化为0的直线

# 添加: 创建整体偏移量变量
offset = 0.0  # 整体偏移量，默认为0

# 新增数据结构: 存储心情标签 {time_index: {'title': str, 'content': str, 'annotation': artist_object}}
emotion_labels = {}

# 创建图形和坐标轴
fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(bottom=0.2)  # 为滑动条留出空间

# 绘制初始的平坦曲线（无点，仅线）
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

# 添加: 创建滑动条轴和滑动条
ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03], facecolor='lightgoldenrodyellow')
offset_slider = Slider(ax_slider, 'Offset', -2, 2, valinit=0.0)

# 存储当前被拖拽的点的索引
dragging_index = None

# 添加一个变量来存储当前的LineCollection和imshow对象
current_lc = None
gradient_image = None

# 存储上次点击时间，用于判断双击
last_click_time = 0.0
DOUBLE_CLICK_TIME = 0.3 # 双击时间间隔（秒）

# --- 标签管理函数 ---

def draw_labels():
    """清除并重新绘制所有心情标签的标题。"""
    # 移除旧的 Annotation 对象
    for index in emotion_labels:
        if 'annotation' in emotion_labels[index] and emotion_labels[index]['annotation'] in ax.texts:
            emotion_labels[index]['annotation'].remove()

    # 绘制新的 Annotation 对象
    for index, data in emotion_labels.items():
        # 获取当前时间点的 y 值 (应用了偏移量)
        x_val = time[index]
        y_val = amplitude[index] + offset
        title = data['title']
        
        # 绘制 Annotation
        anno = ax.annotate(
            title, 
            (x_val, y_val), # 标签位置在数据点上
            xytext=(0, 10), # 向上偏移10个点
            textcoords="offset points",
            ha='center', va='bottom',
            fontsize=10, 
            color='black',
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.6, ec="orange", lw=1),
            # 增加轮廓效果，让标签更清晰
            path_effects=[pe.withStroke(linewidth=2, foreground="white")]
        )
        data['annotation'] = anno # 存储 Annotation 对象以便后续移除和点击检测

# --- 曲线绘制函数（更新后） ---

# 定义颜色映射的绝对范围
MIN_Y_VAL = -3.0
MAX_Y_VAL = 3.0

def update_smooth_curve():
    global current_lc, gradient_image
    
    # --- 1. 插值和数据准备 ---
    xnew = np.linspace(time.min(), time.max(), 300) # Increased resolution for smoother look
    y_values = amplitude + offset
    
    extended_time = np.concatenate([[time[0]-1e-10], time, [time[-1]+1e-10]])
    extended_y = np.concatenate([[y_values[0]], y_values, [y_values[-1]]])
    
    spline = PchipInterpolator(extended_time, extended_y)
    ynew = spline(xnew)
    
    # --- 2. 颜色映射设置 ---
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    
    # 定义 Colormap 的节点：-3(Blue) -> 0(Grey) -> 3(Green)
    cmap_nodes = [
        (0.0, 'blue'),    # Y = -3
        (0.5, 'gray'),    # Y = 0
        (1.0, 'green')    # Y = 3
    ]
    custom_cmap = LinearSegmentedColormap.from_list("emotion_cmap", cmap_nodes)
    norm = Normalize(vmin=MIN_Y_VAL, vmax=MAX_Y_VAL) 
    
    # --- 3. 移除旧的图形元素 ---
    if gradient_image is not None:
        gradient_image.remove()
        gradient_image = None

    if current_lc is not None:
        current_lc.remove()
        current_lc = None
        
    line.set_data([], [])

    # --- 4. 绘制填充区域（使用 imshow 和 Alpha 蒙版实现平滑渐变） ---
    y_res = 100
    x_res = len(xnew)

    # 创建一个代表Y坐标的网格
    y_coords = np.linspace(MIN_Y_VAL, MAX_Y_VAL, y_res)
    Y_grid = np.tile(y_coords.reshape(-1, 1), (1, x_res))

    # 使用 colormap 将Y坐标网格转换为 RGBA 图像
    rgba_image = custom_cmap(norm(Y_grid))

    # 创建一个布尔蒙版，标记出曲线和y=0基准线之间的区域
    # 通过广播 ynew (shape: 1, x_res) 到 Y_grid (shape: y_res, x_res) 进行比较
    is_above_baseline = (Y_grid > 0) & (Y_grid <= ynew)
    is_below_baseline = (Y_grid < 0) & (Y_grid >= ynew)
    fill_mask = is_above_baseline | is_below_baseline

    # 根据Y值的幅度计算透明度
    abs_amp_norm = np.abs(Y_grid) / MAX_Y_VAL
    alpha_values = 0.2 + 0.6 * abs_amp_norm

    # 应用蒙版：只在填充区域内设置透明度，其他区域完全透明 (alpha=0)
    final_alpha = np.where(fill_mask, alpha_values, 0)
    rgba_image[:, :, 3] = final_alpha

    # 使用 imshow 绘制带透明度的渐变图像
    gradient_image = ax.imshow(
        rgba_image,
        aspect='auto',
        origin='lower',
        extent=(xnew.min(), xnew.max(), MIN_Y_VAL, MAX_Y_VAL),
        zorder=-1
    )

    # --- 5. 绘制平滑曲线（使用 LineCollection 实现精确纵向渐变） ---
    points = np.array([xnew, ynew]).T
    segments_line = np.concatenate([points[:-1].reshape(-1, 1, 2), points[1:].reshape(-1, 1, 2)], axis=1)

    lc = LineCollection(
        segments_line, 
        cmap=custom_cmap,
        norm=norm,
        linewidths=3, 
        zorder=1
    ) 
    lc.set_array(ynew) 
    ax.add_collection(lc)
    current_lc = lc
    
    # 重新设置Y轴范围
    ax.relim()
    ax.set_ylim(-3, 3) 
    
    # 每次曲线更新时，也更新标签位置
    draw_labels()

# --- 滑动条更新函数 ---

def update_offset(val):
    global offset
    offset = val
    update_smooth_curve()
    fig.canvas.draw()

# --- 鼠标事件处理函数 ---

# 鼠标点击事件，开始拖拽 或 检查双击
def on_click(event):
    global dragging_index, last_click_time
    
    current_time = time_module.time()
    # 判断是否为双击
    if current_time - last_click_time < DOUBLE_CLICK_TIME:
        on_double_click(event)
        last_click_time = 0.0 # 重置，避免三击
        return
    
    last_click_time = current_time

    # 1. 尝试点击标签
    if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
        for index, data in emotion_labels.items():
            anno = data.get('annotation')
            if anno and anno.contains(event)[0]: # 检查点击是否在 Annotation 对象的边界内
                on_label_click(index, data)
                return # 标签被点击，不进行拖拽逻辑

    # 2. 尝试拖拽数据点
    if event.button is MouseButton.LEFT and event.xdata is not None:
        # 只在曲线所在的坐标轴内进行操作
        if event.inaxes == ax:
            distances = np.abs(time - event.xdata)
            dragging_index = np.argmin(distances)
            print(f"Start dragging point {dragging_index} at time {time[dragging_index]}")

# 鼠标双击事件：添加心情标签
def on_double_click(event):
    if event.inaxes == ax and event.xdata is not None and event.ydata is not None:
        # 确定最近的时间点索引
        distances = np.abs(time - event.xdata)
        time_index = np.argmin(distances)
        
        print(f"\n--- Adding/Editing Label for Time {time[time_index]} ---")
        
        # 检查是否已存在标签
        current_title = emotion_labels.get(time_index, {}).get('title', '')
        current_content = emotion_labels.get(time_index, {}).get('content', '')

        # 使用 input() 模拟对话框
        title = input(f"Enter Title for {int(time[time_index])}h (Current: '{current_title}'): ").strip()
        content = input(f"Enter Details for {int(time[time_index])}h (Current: '{current_content}'): ").strip()

        if title:
            # 更新或新增标签
            emotion_labels[time_index] = {'title': title, 'content': content}
            print(f"Label added/updated: {title}")
        elif time_index in emotion_labels:
            # 标题为空，删除标签
            if input("Title is empty. Do you want to DELETE this label? (y/n): ").lower() == 'y':
                if 'annotation' in emotion_labels[time_index]:
                    emotion_labels[time_index]['annotation'].remove()
                del emotion_labels[time_index]
                print(f"Label at {int(time[time_index])}h deleted.")
        
        update_smooth_curve()
        fig.canvas.draw()
        print("--------------------------------------------------\n")

# 鼠标单击标签事件：查看并允许修改
def on_label_click(index, data):
    print(f"\n--- View/Edit Label at Time {int(time[index])}h ---")
    print(f"Title: {data['title']}")
    print(f"Content: {data['content']}")
    
    # 询问是否修改
    if input("Do you want to MODIFY this label? (y/n): ").lower() == 'y':
        # 调用双击逻辑来处理修改
        # 构造一个模拟事件（只需要time_index）
        class MockEvent:
            def __init__(self, xdata):
                self.inaxes = ax
                self.xdata = xdata
                self.ydata = amplitude[index] # ydata不重要，但需要是非None
        
        on_double_click(MockEvent(time[index]))
    print("--------------------------------------------------\n")

# 鼠标拖动事件，修改选中点的振幅
def on_drag(event):
    if dragging_index is not None and event.ydata is not None and event.inaxes == ax:
        amplitude[dragging_index] = event.ydata
        update_smooth_curve()
        fig.canvas.draw()

# 鼠标释放事件，结束拖拽
def on_release(event):
    global dragging_index
    dragging_index = None
    # print("Released drag")

# 连接鼠标事件
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('motion_notify_event', on_drag)
fig.canvas.mpl_connect('button_release_event', on_release)

# 添加: 连接滑动条事件
offset_slider.on_changed(update_offset)

# 初始平滑曲线
update_smooth_curve()

# 显示图形
plt.show()
