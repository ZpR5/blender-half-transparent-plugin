bl_info = {
    "name": "Maya 工作流",
    "author": "Copilot",
    "version": (1, 0, 0),
    "blender": (3, 0, 0),
    "location": "View3D",
    "description": "让 Blender 支持 Maya 式操作流程和快捷键",
    "category": "Navigation",
}

import bpy
import mathutils
from mathutils import Vector, Matrix, Quaternion
import math


# ============= 视图操控（中键旋转 / Shift+中键平移 / Ctrl+中键缩放）=============

class VIEW3D_OT_maya_rotate_view(bpy.types.Operator):
    """用中键旋转视图（Maya 式）"""
    bl_idname = "view3d.maya_rotate_view"
    bl_label = "Maya 式旋转视图"

    rotating: bpy.props.BoolProperty(default=False)
    last_mouse_x: bpy.props.IntProperty(default=0)
    last_mouse_y: bpy.props.IntProperty(default=0)
    timer = None

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            if self.rotating:
                dx = event.mouse_x - self.last_mouse_x
                dy = event.mouse_y - self.last_mouse_y

                self.last_mouse_x = event.mouse_x
                self.last_mouse_y = event.mouse_y

                # 旋转视图
                for area in context.screen.areas:
                    if area.type == 'VIEW_3D':
                        for region in area.regions:
                            if region.type == 'WINDOW':
                                with context.temp_override(area=area, region=region):
                                    bpy.ops.view3d.rotate(use_mouse_moves=False)

                # 应用旋转增量
                view3d = context.space_data
                if view3d:
                    # 使用 numpad_period 对应的快捷方式
                    rv3d = context.region_data
                    if rv3d:
                        # 直接修改视图旋转
                        angle_x = math.radians(dy * 0.5)
                        angle_y = math.radians(dx * 0.5)

                        # 获取当前旋转矩阵
                        quat = rv3d.view_rotation
                        # 应用旋转
                        rot_x = Quaternion((1, 0, 0), angle_x)
                        rot_y = Quaternion((0, 1, 0), angle_y)
                        rv3d.view_rotation = (rot_y @ rot_x) @ quat

        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'RELEASE':
                self.rotating = False
                if self.timer:
                    wm = context.window_manager
                    wm.event_timer_remove(self.timer)
                return {'RUNNING_MODAL'}

        elif event.type == 'TIMER':
            # 惯性衰减
            if self.rotating:
                pass

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.rotating = True
        self.last_mouse_x = context.window.width // 2
        self.last_mouse_y = context.window.height // 2

        wm = context.window_manager
        self.timer = wm.event_timer_add(0.01, window=context.window)
        wm.modal_handler_add(self)

        return {'RUNNING_MODAL'}


class VIEW3D_OT_maya_pan_view(bpy.types.Operator):
    """用 Shift+中键平移视图（Maya 式）"""
    bl_idname = "view3d.maya_pan_view"
    bl_label = "Maya 式平移视图"

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            rv3d = context.region_data
            if rv3d:
                # 计算平移量
                dx = event.mouse_x - self.last_mouse_x
                dy = event.mouse_y - self.last_mouse_y

                self.last_mouse_x = event.mouse_x
                self.last_mouse_y = event.mouse_y

                # 获取视图距离和平移速度
                view_distance = rv3d.view_distance
                pan_speed = view_distance * 0.001

                # 获取视图的左右上下方向
                forward = rv3d.view_matrix.inverted().col[2][:3]
                right = rv3d.view_matrix.inverted().col[0][:3]
                up = rv3d.view_matrix.inverted().col[1][:3]

                # 应用平移
                pan_vector = right * dx * pan_speed - up * dy * pan_speed
                rv3d.view_location += pan_vector

        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'RELEASE':
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.last_mouse_x = context.window.width // 2
        self.last_mouse_y = context.window.height // 2

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


class VIEW3D_OT_maya_zoom_view(bpy.types.Operator):
    """用 Ctrl+中键缩放视图（Maya 式）"""
    bl_idname = "view3d.maya_zoom_view"
    bl_label = "Maya 式缩放视图"

    def modal(self, context, event):
        if event.type == 'MOUSEMOVE':
            rv3d = context.region_data
            if rv3d:
                dy = event.mouse_y - self.last_mouse_y
                self.last_mouse_y = event.mouse_y

                # 缩放（向上放大，向下缩小）
                zoom_factor = 1.0 - dy * 0.01
                rv3d.view_distance *= zoom_factor

        elif event.type == 'MIDDLEMOUSE':
            if event.value == 'RELEASE':
                return {'FINISHED'}

        return {'RUNNING_MODAL'}

    def execute(self, context):
        self.last_mouse_y = context.window.height // 2

        wm = context.window_manager
        wm.modal_handler_add(self)
        return {'RUNNING_MODAL'}


# ============= 快捷键（Q/W/E/R 选择/移动/旋转/缩放）=============

class MESH_OT_set_selection_mode(bpy.types.Operator):
    """Q = 选择工具"""
    bl_idname = "mesh.set_selection_mode"
    bl_label = "设置为选择模式"

    def execute(self, context):
        # Blender 默认就是选择模式，这里确保激活选择工具
        bpy.ops.wm.tool_set_by_id(name="builtin.select_box")
        return {'FINISHED'}


class TRANSFORM_OT_maya_move(bpy.types.Operator):
    """W = 移动工具"""
    bl_idname = "transform.maya_move"
    bl_label = "移动工具"

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.move")
        return {'FINISHED'}


class TRANSFORM_OT_maya_rotate(bpy.types.Operator):
    """E = 旋转工具"""
    bl_idname = "transform.maya_rotate"
    bl_label = "旋转工具"

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.rotate")
        return {'FINISHED'}


class TRANSFORM_OT_maya_scale(bpy.types.Operator):
    """R = 缩放工具"""
    bl_idname = "transform.maya_scale"
    bl_label = "缩放工具"

    def execute(self, context):
        bpy.ops.wm.tool_set_by_id(name="builtin.scale")
        return {'FINISHED'}


class OBJECT_OT_maya_duplicate(bpy.types.Operator):
    """Ctrl+D = 复制"""
    bl_idname = "object.maya_duplicate"
    bl_label = "复制"

    def execute(self, context):
        bpy.ops.object.duplicate_move()
        return {'FINISHED'}


class OBJECT_OT_maya_delete(bpy.types.Operator):
    """Delete = 删除"""
    bl_idname = "object.maya_delete"
    bl_label = "删除"

    def execute(self, context):
        bpy.ops.object.delete(use_global=False)
        return {'FINISHED'}


class OBJECT_OT_maya_parent(bpy.types.Operator):
    """Ctrl+P = 父子关系（简化版）"""
    bl_idname = "object.maya_parent"
    bl_label = "设置父子关系"

    def execute(self, context):
        bpy.ops.object.parent_set(type='OBJECT')
        return {'FINISHED'}


class OBJECT_OT_maya_group(bpy.types.Operator):
    """Ctrl+G = 创建组"""
    bl_idname = "object.maya_group"
    bl_label = "创建组"

    def execute(self, context):
        # Blender 中用 collection 代替组
        bpy.ops.object.group_link()
        return {'FINISHED'}


class OBJECT_OT_maya_hide(bpy.types.Operator):
    """H = 隐藏"""
    bl_idname = "object.maya_hide"
    bl_label = "隐藏"

    def execute(self, context):
        bpy.ops.object.hide_view_set(unselected=False)
        return {'FINISHED'}


class OBJECT_OT_maya_show_all(bpy.types.Operator):
    """Shift+H = 显示所有"""
    bl_idname = "object.maya_show_all"
    bl_label = "显示所有"

    def execute(self, context):
        bpy.ops.object.hide_view_clear()
        return {'FINISHED'}


# ============= 快捷键映射 =============

addon_keymaps = []


def register_keymaps():
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='3D View', space_type='VIEW_3D')

    # 视图操控
    # 中键旋转 - 这个 Blender 原生支持，我们保持原样

    # 快捷键
    kmi = km.keymap_items.new("mesh.set_selection_mode", 'Q', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("transform.maya_move", 'W', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("transform.maya_rotate", 'E', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("transform.maya_scale", 'R', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_duplicate", 'D', 'PRESS', ctrl=True)
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_delete", 'DEL', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_parent", 'P', 'PRESS', ctrl=True)
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_group", 'G', 'PRESS', ctrl=True)
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_hide", 'H', 'PRESS')
    addon_keymaps.append((km, kmi))

    kmi = km.keymap_items.new("object.maya_show_all", 'H', 'PRESS', shift=True)
    addon_keymaps.append((km, kmi))


def unregister_keymaps():
    for km, kmi in addon_keymaps:
        km.keymap_items.remove(kmi)
    addon_keymaps.clear()


# ============= 注册 =============

classes = (
    VIEW3D_OT_maya_rotate_view,
    VIEW3D_OT_maya_pan_view,
    VIEW3D_OT_maya_zoom_view,
    MESH_OT_set_selection_mode,
    TRANSFORM_OT_maya_move,
    TRANSFORM_OT_maya_rotate,
    TRANSFORM_OT_maya_scale,
    OBJECT_OT_maya_duplicate,
    OBJECT_OT_maya_delete,
    OBJECT_OT_maya_parent,
    OBJECT_OT_maya_group,
    OBJECT_OT_maya_hide,
    OBJECT_OT_maya_show_all,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)
    register_keymaps()


def unregister():
    unregister_keymaps()
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)


if __name__ == "__main__":
    register()
