import matplotlib.pyplot as plt
import numpy as np
from matplotlib.backend_bases import MouseButton
from matplotlib.widgets import Slider
from scipy.interpolate import PchipInterpolator
from matplotlib.collections import LineCollection
import matplotlib.patheffects as pe
import time as time_module
import os

# --- New: Import tkinter and additional matplotlib components ---
import tkinter as tk
from tkinter import simpledialog, messagebox, filedialog
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

# --- New: Helper function to find available icons ---
def get_available_icons():
    """Scans the 'icons' subdirectory and returns a list of filenames."""
    icon_dir = 'icons'
    if not os.path.isdir(icon_dir):
        return []
    try:
        # Return a list of files in the directory
        return [f for f in os.listdir(icon_dir) if os.path.isfile(os.path.join(icon_dir, f))]
    except Exception as e:
        print(f"Error reading icons directory: {e}")
        return []

# --- Updated: Custom Dialog Class for Label Input ---
class LabelDialog(simpledialog.Dialog):
    """A custom dialog to get a title, content, and an icon filename."""
    def __init__(self, parent, title=None, current_title="", current_content="", current_icon=""):
        self.current_title = current_title
        self.current_content = current_content
        self.current_icon = current_icon
        self.result = None
        self.available_icons = get_available_icons()
        super().__init__(parent, title=title)

    def body(self, master):
        # Title Entry
        tk.Label(master, text="Title:", anchor="w").grid(row=0, column=0, padx=5, sticky="w")
        self.title_entry = tk.Entry(master, width=50)
        self.title_entry.grid(row=1, column=0, padx=5, pady=(0, 10))
        self.title_entry.insert(0, self.current_title)

        # Content Text
        tk.Label(master, text="Details:", anchor="w").grid(row=2, column=0, padx=5, sticky="w")
        self.content_text = tk.Text(master, width=50, height=5)
        self.content_text.grid(row=3, column=0, padx=5, pady=(0, 10))
        self.content_text.insert("1.0", self.current_content)

        # Icon Entry
        tk.Label(master, text="Icon (e.g., happy.gif):", anchor="w").grid(row=4, column=0, padx=5, sticky="w")
        self.icon_frame = tk.Frame(master)
        self.icon_frame.grid(row=5, column=0, padx=5, pady=(0, 5), sticky="w")
        
        self.icon_entry = tk.Entry(self.icon_frame, width=40)
        self.icon_entry.pack(side=tk.LEFT)
        self.icon_entry.insert(0, self.current_icon)
        
        self.browse_button = tk.Button(self.icon_frame, text="Browse...", command=self.browse_icon)
        self.browse_button.pack(side=tk.LEFT, padx=(5, 0))
        
        # Display available icons
        if self.available_icons:
            icon_list_str = "Available: " + ", ".join(self.available_icons)
            tk.Label(master, text=icon_list_str, wraplength=300, justify="left").grid(row=6, column=0, padx=5, sticky="w")
        else:
            tk.Label(master, text="No 'icons' folder found or it is empty.", justify="left").grid(row=6, column=0, padx=5, sticky="w")

        return self.title_entry # Initial focus

    def browse_icon(self):
        """Open file dialog to select a GIF file as icon."""
        file_path = filedialog.askopenfilename(
            title="Select Icon File",
            filetypes=[("GIF files", "*.gif"), ("All files", "*.*")]
        )
        if file_path:
            # Store the full path in the entry field
            self.icon_entry.delete(0, tk.END)
            self.icon_entry.insert(0, file_path)

    def apply(self):
        title = self.title_entry.get().strip()
        content = self.content_text.get("1.0", "end-1c").strip()
        icon = self.icon_entry.get().strip()
        self.result = (title, content, icon)

# --- Main script setup ---
plt.rcParams['font.sans-serif'] = ['SimHei', 'FangSong', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

time = np.arange(24)
amplitude = np.zeros(24)
offset = 0.0
emotion_labels = {}

fig, ax = plt.subplots(figsize=(10, 6))
plt.subplots_adjust(bottom=0.2)

line, = ax.plot(time, amplitude, linestyle='-', color='gray')
ax.axhline(y=0, color='lightgray', linestyle='--', linewidth=1)
ax.set_title("Interactive Emotion Curve")
ax.set_xlabel("Time (t) [hours]")
ax.set_ylabel("Amplitude (a)")
ax.grid(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['bottom'].set_visible(False)
ax.spines['left'].set_visible(False)
ax.set_yticks([-2, 0, 2])
ax.set_yticklabels(['难过', '一般', '高兴'])

ax_slider = plt.axes([0.2, 0.1, 0.6, 0.03], facecolor='lightgoldenrodyellow')
offset_slider = Slider(ax_slider, 'Offset', -2, 2, valinit=0.0)

dragging_index = None
current_lc = None
gradient_image = None
last_click_time = 0.0
DOUBLE_CLICK_TIME = 0.3

# --- Updated: Label Drawing Function ---
def draw_labels():
    """Clear and redraw all text labels and icons."""
    # Remove old artists first
    for index in list(emotion_labels.keys()):
        if 'annotation' in emotion_labels[index] and emotion_labels[index]['annotation'] in ax.texts:
            emotion_labels[index]['annotation'].remove()
        if 'icon_artist' in emotion_labels[index] and emotion_labels[index]['icon_artist'] in ax.artists:
            emotion_labels[index]['icon_artist'].remove()

    # Draw new artists
    for index, data in emotion_labels.items():
        x_val = time[index]
        y_val = amplitude[index] + offset
        
        # 1. Draw Text Annotation ( positioned below the icon )
        anno = ax.annotate(
            data['title'], (x_val, y_val), xytext=(0, 0), textcoords="offset points",
            ha='center', va='top', fontsize=10, color='black',
            bbox=dict(boxstyle="round,pad=0.3", fc="yellow", alpha=0.6, ec="orange", lw=1),
            path_effects=[pe.withStroke(linewidth=2, foreground="white")]
        )
        data['annotation'] = anno

        # 2. Draw Icon ( positioned above where the text will be )
        icon_filename = data.get('icon')
        if icon_filename:
            # Check if it's a full path or just a filename
            if os.path.exists(icon_filename):
                icon_path = icon_filename  # It's a full path
            else:
                icon_path = os.path.join('icons', icon_filename)  # Assume it's in icons folder
            
            if os.path.exists(icon_path):
                try:
                    img = plt.imread(icon_path)
                    # 修改图标缩放比例，使其与文字大小更匹配
                    imagebox = OffsetImage(img, zoom=0.05) # 从0.5调整为0.15，使图标更小
                    ab = AnnotationBbox(imagebox, (x_val, y_val),
                                        xybox=(0., 30), # Position icon above the point
                                        xycoords='data',
                                        boxcoords="offset points",
                                        frameon=False,
                                        pad=0)
                    ax.add_artist(ab)
                    data['icon_artist'] = ab
                except Exception as e:
                    print(f"Could not load or display icon '{icon_path}': {e}")
            else:
                print(f"Warning: Icon file not found: {icon_path}")


# --- Curve Drawing and Core Logic (largely unchanged) ---
MIN_Y_VAL = -3.0
MAX_Y_VAL = 3.0

def update_smooth_curve():
    global current_lc, gradient_image
    from matplotlib.colors import LinearSegmentedColormap, Normalize
    
    xnew = np.linspace(time.min(), time.max(), 300)
    y_values = amplitude + offset
    spline = PchipInterpolator(np.concatenate([[time[0]-1e-10], time, [time[-1]+1e-10]]), 
                               np.concatenate([[y_values[0]], y_values, [y_values[-1]]]))
    ynew = spline(xnew)
    
    cmap_nodes = [(0.0, 'blue'), (0.5, 'gray'), (1.0, 'green')]
    custom_cmap = LinearSegmentedColormap.from_list("emotion_cmap", cmap_nodes)
    norm = Normalize(vmin=MIN_Y_VAL, vmax=MAX_Y_VAL) 
    
    if gradient_image: gradient_image.remove()
    if current_lc: current_lc.remove()
    line.set_data([], [])

    y_res, x_res = 100, len(xnew)
    y_coords = np.linspace(MIN_Y_VAL, MAX_Y_VAL, y_res)
    Y_grid = np.tile(y_coords.reshape(-1, 1), (1, x_res))
    rgba_image = custom_cmap(norm(Y_grid))
    fill_mask = ((Y_grid > 0) & (Y_grid <= ynew)) | ((Y_grid < 0) & (Y_grid >= ynew))
    alpha_values = 0.2 + 0.6 * (np.abs(Y_grid) / MAX_Y_VAL)
    rgba_image[:, :, 3] = np.where(fill_mask, alpha_values, 0)
    gradient_image = ax.imshow(rgba_image, aspect='auto', origin='lower',
                               extent=(xnew.min(), xnew.max(), MIN_Y_VAL, MAX_Y_VAL), zorder=-1)

    points = np.array([xnew, ynew]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    lc = LineCollection(segments, cmap=custom_cmap, norm=norm, linewidths=3, zorder=1)
    lc.set_array(ynew)
    ax.add_collection(lc)
    current_lc = lc
    
    ax.relim()
    ax.set_ylim(-3, 3) 
    draw_labels()

def update_offset(val):
    global offset
    offset = val
    update_smooth_curve()
    fig.canvas.draw()
    
# --- Updated: Centralized Label Editing Logic ---
def handle_label_edit(time_index):
    """Opens a dialog to edit a label for a given time index."""
    root = tk.Tk()
    root.withdraw()

    current_data = emotion_labels.get(time_index, {})
    current_title = current_data.get('title', '')
    current_content = current_data.get('content', '')
    current_icon = current_data.get('icon', '')

    dialog = LabelDialog(root, title=f"Edit Label for {int(time[time_index])}h",
                         current_title=current_title, current_content=current_content, current_icon=current_icon)
    
    if dialog.result:
        title, content, icon = dialog.result
        
        if title:
            emotion_labels[time_index] = {'title': title, 'content': content, 'icon': icon}
            print(f"Label at {int(time[time_index])}h updated to '{title}'")
        elif time_index in emotion_labels:
            if messagebox.askyesno("Confirm Delete", "Title is empty. Do you want to DELETE this label?"):
                del emotion_labels[time_index]
                print(f"Label at {int(time[time_index])}h deleted.")
        
        update_smooth_curve()
        fig.canvas.draw()
    root.destroy()

# --- Event Handlers (Updated) ---
def on_click(event):
    global dragging_index, last_click_time
    current_time = time_module.time()
    if current_time - last_click_time < DOUBLE_CLICK_TIME:
        on_double_click(event)
        last_click_time = 0.0
        return
    last_click_time = current_time

    if event.inaxes == ax and event.xdata is not None:
        for index, data in emotion_labels.items():
            anno = data.get('annotation')
            if anno and anno.contains(event)[0]:
                on_label_click(index)
                return

    if event.button is MouseButton.LEFT and event.xdata is not None and event.inaxes == ax:
        dragging_index = np.argmin(np.abs(time - event.xdata))

def on_double_click(event):
    if event.inaxes == ax and event.xdata is not None:
        time_index = np.argmin(np.abs(time - event.xdata))
        handle_label_edit(time_index)

def on_label_click(index):
    data = emotion_labels[index]
    root = tk.Tk()
    root.withdraw()
    should_modify = messagebox.askyesno(
        title=f"Label at {int(time[index])}h",
        message=f"Title: {data['title']}\nIcon: {data.get('icon', 'N/A')}\n\nDetails: {data['content']}\n\nDo you want to modify this label?"
    )
    root.destroy()
    if should_modify:
        handle_label_edit(index)

def on_drag(event):
    if dragging_index is not None and event.ydata is not None and event.inaxes == ax:
        amplitude[dragging_index] = event.ydata
        update_smooth_curve()
        fig.canvas.draw()

def on_release(event):
    global dragging_index
    if event.button is MouseButton.LEFT:
        dragging_index = None

# --- Connect events and show plot ---
fig.canvas.mpl_connect('button_press_event', on_click)
fig.canvas.mpl_connect('motion_notify_event', on_drag)
fig.canvas.mpl_connect('button_release_event', on_release)
offset_slider.on_changed(update_offset)
update_smooth_curve()
plt.show()
