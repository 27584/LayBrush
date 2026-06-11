#version 330 core

// 输入：从顶点着色器传递的纹理坐标
in vec2 v_uv;

// 输出：最终像素颜色
out vec4 out_color;

//  uniforms（从 Python 传递，每个单位独立控制）
uniform sampler2D u_texture;        // 单位纹理（绑定到纹理通道）
uniform float u_time;               // 当前时间戳（控制动画）
uniform float u_damage_intensity;   // 受伤强度（0.0-1.0）
uniform float u_damage_duration;    // 受伤持续时间（秒）
uniform float u_damage_start_time;  // 受伤开始时间（时间戳）
uniform vec3 u_damage_color;        // 受伤颜色（默认红色）

void main() {
    // 1. 采样原始纹理颜色
    vec4 original_color = texture(u_texture, v_uv);

    // 2. 计算受伤效果衰减（从 1.0 渐变到 0.0）
    float elapsed = u_time - u_damage_start_time;
    float decay = 1.0 - (elapsed / u_damage_duration);
    decay = clamp(decay, 0.0, 1.0);  // 避免负数

    // 3. 叠加受伤颜色（原始色 + 受伤色混合）
    vec3 final_rgb = mix(
        original_color.rgb,
        u_damage_color,
        decay * u_damage_intensity
    );

    // 4. 输出最终颜色（保留原始透明度）
    out_color = vec4(final_rgb, original_color.a);
}