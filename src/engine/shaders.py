def get_shader_program(ctx):
    vertex_shader = """
    #version 330 core

    layout (location = 0) in vec3 in_position;
    layout (location = 1) in vec2 in_tex_coord;
    layout (location = 2) in float in_shading;

    uniform mat4 m_proj;
    uniform mat4 m_view;
    uniform mat4 m_model;

    out vec2 v_tex_coord;
    out float v_shading;

    void main() {
        v_tex_coord = in_tex_coord;
        v_shading = in_shading;
        gl_Position = m_proj * m_view * m_model * vec4(in_position, 1.0);
    }
    """

    fragment_shader = """
    #version 330 core

    out vec4 fragColor;

    in vec2 v_tex_coord;
    in float v_shading;

    uniform sampler2D u_texture_0;
    uniform vec3 u_fog_color;
    uniform float u_fog_density;

    void main() {
        vec4 tex_color = texture(u_texture_0, v_tex_coord);
        if (tex_color.a < 0.1) discard;
        
        // Apply shading
        tex_color.rgb *= v_shading;
        
        // Fog calculation
        float dist = gl_FragCoord.z / gl_FragCoord.w;
        float fog_factor = 1.0 - exp(-pow(dist * u_fog_density, 2.0));
        fog_factor = clamp(fog_factor, 0.0, 1.0);
        
        fragColor = mix(tex_color, vec4(u_fog_color, 1.0), fog_factor);
    }
    """
    
    return ctx.program(vertex_shader=vertex_shader, fragment_shader=fragment_shader)
