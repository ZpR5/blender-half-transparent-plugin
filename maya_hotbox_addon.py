bl_info = {
    "name": "Maya Hotbox 快捷键热区",
    "author": "Copilot",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "description": "Maya 式快捷键热区（Hotbox）和 Shift+左键菜单",
    "category": "Navigation",
}

import bpy
import gpu
from gpu_extras.batch import batch_for_shader
from mathutils import Vector
import math


# ============= Hotbox 菜单（快捷键热区）=============

class HotboxMenu:
    """快捷键热区菜单系统"""
    
    def __init__(self):
        self.visible = False
        self.mouse_x = 0
        self.mouse_y = 0
        self.radius = 120  # 热区半径
        self.selected_zone = None
        
        # 定义 8 个方向的菜单项
        self.zones = {
            "top": {"label": "移动 (W)", "key": "W", "angle": 90},
            "top_right": {"label": "旋转 (E)", "key": "E", "angle": 45},
            "right": {"label": "缩放 (R)", "key": "R", "angle": 0},
            "bottom_right": {"label": "删除 (Delete)", "key": "DEL", "angle": -45},
            "bottom": {"label": "复制 (Ctrl+D)", "key": "D", "angle": -90},
            "bottom_left": {"label": "隐藏 (H)", "key": "H", "angle": -135},
            "left": {"label": "选择 (Q)", "key": "Q", "angle": 180},
            "top_left": {"label": "显示 (Shift+H)", "key": "SHIFT_H", "angle": 135},
        }
        
        self.center_x = 0
        self.center_y = 0
    
    def show(self, x, y):
        self.visible = True
        self.mouse_x = x
        self.mouse_y = y
        self.center_x = x
        self.center_y = y
    
    def hide(self):
        self.visible = False
        self.selected_zone = None
    
    def update_mouse(self, x, y):
        if not self.visible:
            return
        
        self.mouse_x = x
        self.mouse_y = y
        
        # 计算鼠标相对于中心的距离和角度
        dx = x - self.center_x
        dy = y - self.center_y
        distance = math.sqrt(dx**2 + dy**2)
        
        if distance > self.radius * 0.3:  # 只有离中心足够远才选中
            angle = math.degrees(math.atan2(dy, dx))
            
            # 查找最近的区域
            for zone_name, zone_data in self.zones.items():
                zone_angle = zone_data["angle"]
                # 计算角度差（考虑循环）
                angle_diff = abs(angle - zone_angle)
                if angle_diff > 180:
                    angle_diff = 360 - angle_diff
                
                if angle_diff < 22.5:  # 45度范围的一半
                    self.selected_zone = zone_name
                    break
        else:
            self.selected_zone = None
    
    def get_selected_action(self):
        if self.selected_zone and self.selected_zone in self.zones:
            return self.zones[self.selected_zone]["key"]
        return None


hotbox = HotboxMenu()


# ============= Shift+左键 上下文菜单 =============

class VIEW3D_OT_shift_lmb_menu(bpy.types.Operator):
    """Shift+左键打开上下文菜单"""
    bl_idname = "view3d.shift_lmb_menu"
    bl_label = "上下文菜单"
    
    def execute(self, context):
        return {'FINISHED'}
    
    def invoke(self, context, event):
        return context.window_manager.invoke_popup_menu(self.draw_menu, width=200)
    
    def draw_menu(self, menu, context):
        layout = menu.layout
        layout.label(text="Maya 菜单")
        layout.separator()
        
        layout.operator("wm.tool_set_by_id", text="选择工具 (Q)").name = "builtin.select_box"
        layout.operator("wm.tool_set_by_id", text="移动工具 (W)").name = "builtin.move"
        layout.operator("wm.tool_set_by_id", text="旋转工具 (E)").name = "builtin.rotate"
        layout.operator("wm.tool_set_by_id", text="缩放工具 (R)").name = "builtin.scale"
        
        layout.separator()
        
        layout.operator("object.duplicate_move", text="复制 (Ctrl+D)")
        layout.operator("object.delete", text="删除 (Delete)")
        layout.operator("object.hide_view_set", text="隐藏 (H)").unselected = False
        layout.operator("object.hide_view_clear", text="显示所有 (Shift+H)")


# ============= 快捷键映射 =============

class VIEW3D_OT_hotbox_modal(bpy.types.Operator):
    """显示快捷键热区菜单"""
    bl_idname = "view3d.hotbox_modal"
    bl_label = "Hotbox 菜单"
    
    _timer = None
    
    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            hotbox.update_mouse(event.mouse_x, event.mouse_y)
        
        elif event.type == 'SPACE' and event.value == 'RELEASE':
            # 松开空格键，执行选中的操作
            action = hotbox.get_selected_action()
            hotbox.hide()
            
            if action:
                self.execute_action(context, action)
            
            if self._timer:
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
            
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            return {'FINISHED'}
        
        elif event.type == 'TIMER':
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
        
        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            hotbox.hide()
            if self._timer:
                wm = context.window_manager
                wm.event_timer_remove(self._timer)
            
            for area in context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()
            
            return {'FINISHED'}
        
        return {'RUNNING_MODAL'}
    
    def execute_action(self, context, action):
        """执行对应的快捷键操作"""
        if action == "Q":
            bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        elif action == "W":
            bpy.ops.wm.tool_set_by_id(name="builtin.move")
        elif action == "E":
            bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
        elif action == "R":
            bpy.ops.wm.tool_set_by_id(name="builtin.scale")
        elif action == "D":
            bpy.ops.object.duplicate_move()
        elif action == "DEL":
            bpy.ops.object.delete(use_global=False)
        elif action == "H":
            bpy.ops.object.hide_view_set(unselected=False)
        elif action == "SHIFT_H":
            bpy.ops.object.hide_view_clear()
    
    def execute(self, context):
        wm = context.window_manager
        self._timer = wm.event_timer_add(0.016, window=context.window)
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


# ============= 快捷键绑定 =============

def register_modal_keymaps():
    """注册快捷键"""
    wm = bpy.context.window_manager
    
    # 空格键 = 打开 Hotbox
    if "3D View" not in wm.keyconfigs.addon.keymaps:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    else:
        km = wm.keyconfigs.addon.keymaps["3D View"]
    
    kmi = km.keymap_items.new("view3d.hotbox_modal", 'SPACE', 'PRESS')
    
    return km, kmi


def register_context_keymaps():
    """注册 Shift+左键菜单快捷键"""
    wm = bpy.context.window_manager
    
    if "3D View" not in wm.keyconfigs.addon.keymaps:
        km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')
    else:
        km = wm.keyconfigs.addon.keymaps["3D View"]
    
    kmi = km.keymap_items.new("view3d.shift_lmb_menu", 'LEFTMOUSE', 'PRESS', shift=True)
    
    return km, kmi


# ============= Draw 回调（绘制 Hotbox）=============

def draw_hotbox():
    """在视口中绘制 Hotbox UI"""
    if not hotbox.visible:
        return
    
    # 设置 OpenGL 状态
    gpu.state.blend_set('ALPHA')
    
    # 绘制中心圆
    vertices_center = []
    segments = 32
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = hotbox.center_x + hotbox.radius * 0.15 * math.cos(angle)
        y = hotbox.center_y + hotbox.radius * 0.15 * math.sin(angle)
        vertices_center.append((x, y))
    
    if vertices_center:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": vertices_center})
        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.8))
        batch.draw(shader)
    
    # 绘制外圆
    vertices_outer = []
    for i in range(segments):
        angle = 2 * math.pi * i / segments
        x = hotbox.center_x + hotbox.radius * math.cos(angle)
        y = hotbox.center_y + hotbox.radius * math.sin(angle)
        vertices_outer.append((x, y))
    
    if vertices_outer:
        shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": vertices_outer})
        shader.bind()
        shader.uniform_float("color", (0.8, 0.8, 0.8, 0.6))
        batch.draw(shader)
    
    # 绘制 8 个方向的指示器
    for zone_name, zone_data in hotbox.zones.items():
        angle = math.radians(zone_data["angle"])
        x = hotbox.center_x + hotbox.radius * 0.7 * math.cos(angle)
        y = hotbox.center_y + hotbox.radius * 0.7 * math.sin(angle)
        
        # 选中的区域用不同颜色
        if zone_name == hotbox.selected_zone:
            color = (1.0, 0.5, 0.2, 1.0)  # 橙色
        else:
            color = (0.7, 0.7, 0.7, 0.7)  # 灰色
        
        # 绘制小圆点
        vertices_dot = []
        dot_radius = 15
        for i in range(segments):
            angle_dot = 2 * math.pi * i / segments
            dot_x = x + dot_radius * math.cos(angle_dot)
            dot_y = y + dot_radius * math.sin(angle_dot)
            vertices_dot.append((dot_x, dot_y))
        
        if vertices_dot:
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINE_LOOP', {"pos": vertices_dot})
            shader.bind()
            shader.uniform_float("color", color)
            batch.draw(shader)


# ============= 全局 Space 键处理 =============

def space_press_handler(scene):
    """处理 Space 键（在后台运行）"""
    pass


# ============= 注册和卸载 =============

addon_keymaps = []


def register():
    # 注册 Operator 类
    bpy.utils.register_class(VIEW3D_OT_hotbox_modal)
    bpy.utils.register_class(VIEW3D_OT_shift_lmb_menu)
    
    # 注册快捷键
    try:
        km, kmi = register_modal_keymaps()
        addon_keymaps.append((km, kmi))
    except Exception as e:
        print(f"注册 Hotbox 快捷键失败: {e}")
    
    try:
        km, kmi = register_context_keymaps()
        addon_keymaps.append((km, kmi))
    except Exception as e:
        print(f"注册 Shift+LMB 快捷键失败: {e}")
    
    # 注册绘制回调
    bpy.types.SpaceView3D.draw_handler_add(draw_hotbox, (), 'WINDOW', 'POST_PIXEL')


def unregister():
    # 卸载快捷键
    for km, kmi in addon_keymaps:
        try:
            km.keymap_items.remove(kmi)
        except Exception as e:
            print(f"卸载快捷键失败: {e}")
    
    addon_keymaps.clear()
    
    # 卸载 Operator 类
    try:
        bpy.utils.unregister_class(VIEW3D_OT_hotbox_modal)
        bpy.utils.unregister_class(VIEW3D_OT_shift_lmb_menu)
    except Exception as e:
        print(f"卸载 Operator 失败: {e}")


if __name__ == "__main__":
    register()
