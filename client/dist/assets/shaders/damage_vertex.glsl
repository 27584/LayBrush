#version 330 core

// 输入：arcade.gl 几何对象的顶点数据（位置 + 纹理坐标）
in vec2 in_vert;   // 顶点位置（官方示例标准输入名）
in vec2 in_uv;     // 纹理坐标（官方示例标准输入名）

// 输出到片段着色器
out vec2 v_uv;     // 传递纹理坐标

void main() {
    // 直接使用归一化设备坐标（官方示例风格，无需投影矩阵）
    gl_Position = vec4(in_vert, 0.0, 1.0);
    v_uv = in_uv;  // 传递纹理坐标到片段着色器
}