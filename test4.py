#!/usr/bin/env python
# -*- coding: utf-8 -*-
# vispy: gallery 60

"""
Dynamic planar graph layout.
"""

import numpy as np
from vispy import gloo, app
from vispy.gloo import set_viewport, set_state, clear
from vispy.util.transforms import perspective, translate, rotate
vertp = """
#version 120
// Uniforms
// ------------------------------------
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_antialias;
uniform float u_size;
uniform vec3 a_position;
// Attributes
// ------------------------------------
attribute vec4  a_fg_color;
attribute vec4  a_bg_color;
attribute float a_linewidth;
attribute float a_size;
// Varyings
// ------------------------------------
varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_size;
varying float v_linewidth;
varying float v_antialias;
void main (void) {
    v_size = a_size * u_size;
    v_linewidth = a_linewidth;
    v_antialias = u_antialias;
    v_fg_color  = a_fg_color;
    v_bg_color  = a_bg_color;
    gl_Position = u_projection * u_view * u_model *
        vec4(a_position*u_size,1.0);
    gl_PointSize = v_size + 2*(v_linewidth + 1.5*v_antialias);
}
"""

vert = """
#version 120
// Uniforms
// ------------------------------------
uniform mat4 u_model;
uniform mat4 u_view;
uniform mat4 u_projection;
uniform float u_antialias;
uniform float u_size;
// Attributes
// ------------------------------------
attribute vec3  a_position;
attribute vec4  a_fg_color;
attribute vec4  a_bg_color;
attribute float a_linewidth;
attribute float a_size;
// Varyings
// ------------------------------------
varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_size;
varying float v_linewidth;
varying float v_antialias;
void main (void) {
    v_size = a_size * u_size;
    v_linewidth = a_linewidth;
    v_antialias = u_antialias;
    v_fg_color  = a_fg_color;
    v_bg_color  = a_bg_color;
    gl_Position = u_projection * u_view * u_model *
        vec4(a_position*u_size,1.0);
    gl_PointSize = v_size + 2*(v_linewidth + 1.5*v_antialias);
}
"""

frag = """
#version 120
// Constants
// ------------------------------------
// Varyings
// ------------------------------------
varying vec4 v_fg_color;
varying vec4 v_bg_color;
varying float v_size;
varying float v_linewidth;
varying float v_antialias;
// Functions
// ------------------------------------
float marker(vec2 P, float size);
// Main
// ------------------------------------
void main()
{
    float size = v_size +2*(v_linewidth + 1.5*v_antialias);
    float t = v_linewidth/2.0-v_antialias;
    // The marker function needs to be linked with this shader
    float r = marker(gl_PointCoord, size);
    float d = abs(r) - t;
    if( r > (v_linewidth/2.0+v_antialias))
    {
        discard;
    }
    else if( d < 0.0 )
    {
       gl_FragColor = v_fg_color;
    }
    else
    {
        float alpha = d/v_antialias;
        alpha = exp(-alpha*alpha);
        if (r > 0)
            gl_FragColor = vec4(v_fg_color.rgb, alpha*v_fg_color.a);
        else
            gl_FragColor = mix(v_bg_color, v_fg_color, alpha);
    }
}
float marker(vec2 P, float size)
{
    float r = length((P.xy - vec2(0.5,0.5))*size);
    r -= v_size/2;
    return r;
}
"""

vs = """
uniform mat4 u_model;
attribute vec3 a_position;
attribute vec4 a_fg_color;
attribute vec4 a_bg_color;
attribute float a_size;
attribute float a_linewidth;
void main(){
    gl_Position = u_model *vec4(a_position, 1.);
}
"""

fs = """
void main(){
    gl_FragColor = vec4(0., 0., 0., 1.);
}
"""


class Canvas(app.Canvas):

    def __init__(self, **kwargs):
        # Initialize the canvas for real
        app.Canvas.__init__(self, keys='interactive', size=(960, 960),
                            **kwargs)
        ps = self.pixel_scale
        self.position = 50, 50

        n = 4
        data = np.zeros(n, dtype=[('a_position', np.float32, 3),
                                  ('a_fg_color', np.float32, 4),
                                  ('a_bg_color', np.float32, 4),
                                  ('a_size', np.float32, 1),
                                  ('a_linewidth', np.float32, 1),
                                  ])
        edges = np.array([[0, 1], [0, 2], [0, 3]], dtype='uint32')
        data['a_position'] = 0.0008*np.array([[0,0,0],[1000.0,0,0],[0,1000,0],[0,0,1000]])
        data['a_fg_color'] = 0, 0, 0, 1
        color = np.random.uniform(0.5, 1., (n, 3))
        data['a_bg_color'] = np.hstack((color, np.ones((n, 1))))
        data['a_size'] = 12*np.ones(n)
        data['a_linewidth'] = 1.*ps
        u_antialias = 1

        m=2
        data1 = np.zeros(m, dtype=[
                                  ('a_fg_color', np.float32, 4),
                                  ('a_bg_color', np.float32, 4),
                                  ('a_size', np.float32, 1),
                                  ('a_linewidth', np.float32, 1),
                                  ])
        data1['a_fg_color'] = 0, 0, 0, 1
        color1 = np.random.uniform(0.5, 1., (m, 3))
        data1['a_bg_color'] = np.hstack((color1, np.ones((m, 1))))
        data1['a_size'] = np.random.randint(size=m, low=8 * ps, high=20 * ps)
        data1['a_linewidth'] = 1. * ps

        self.translate = 5
        self.vbo = gloo.VertexBuffer(data)
        self.vbo1 = gloo.VertexBuffer(data1)
        self.index = gloo.IndexBuffer(edges)
        self.view = np.eye(4, dtype=np.float32)
        self.model = np.eye(4, dtype=np.float32)
        self.projection = np.eye(4, dtype=np.float32)

        self.program = gloo.Program(vert, frag)
        self.program.bind(self.vbo)
        self.program['u_size'] = 1
        self.program['u_antialias'] = u_antialias
        self.program['u_model'] = self.model
        self.program['u_view'] = self.view
        self.program['u_projection'] = self.projection

        set_viewport(0, 0, *self.physical_size)

        self.program_e = gloo.Program(vs, fs)
        self.program_e.bind(self.vbo)
        self.program_e['u_model'] = self.model
        self.theta = 0
        self.phi = 0

        self.program_p = gloo.Program(vertp, frag)
        self.program_p.bind(self.vbo1)
        self.program_p['a_position'] = 0.0008 * np.array([[500, 500, 500]])
        self.program_p['u_size'] = 1
        self.program_p['u_antialias'] = u_antialias
        self.program_p['u_model'] = self.model
        self.program_p['u_view'] = self.view
        self.program_p['u_projection'] = self.projection
        self.theta = 0
        self.phi = 0
        self.num = 1

        gloo.set_state('translucent', clear_color='white')
        self.timer = app.Timer('auto', connect=self.on_timer, start=True)

        self.show()
    def on_mouse_wheel(self, event):
        self.theta += 2
        self.phi += 2
        self.model = np.dot(rotate(self.theta, (0, 0, 1)),
                            rotate(self.phi, (0, 1, 0)))
        self.program['u_model'] = self.model
        self.program_e['u_model'] = self.model
        self.program_p['u_model'] = self.model
        self.update()

    def on_resize(self, event):
        set_viewport(0, 0, *event.physical_size)

    def on_timer(self, event):
        self.program_p['a_position'] =  self.program_p['a_position']+0.00008*np.array([50,50,50])
        self.num = self.num+1
        self.update()
    def on_key_press(self, event):
        if event.text == ' ':
            if self.timer.running:
                self.timer.stop()
            else:
                self.timer.start()

    def on_draw(self, event):
        clear(color=True, depth=True)
        self.program_e.draw('lines', self.index)
        self.program.draw('points')
        self.program_p.draw('points')

    def apply_zoom(self):
        gloo.set_viewport(0, 0, self.physical_size[0], self.physical_size[1])
        self.projection = perspective(45.0, self.size[0] /
                                      float(self.size[1]), 1.0, 1000.0)
        self.program['u_projection'] = self.projection

if __name__ == '__main__':
    c = Canvas(title="Graph")
    app.run()