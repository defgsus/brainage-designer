import {useEffect, useRef, useState} from "react";
import * as THREE from 'three';
import Flex from "../../common/Flex";
import {Select, Slider, Switch} from "antd";
import Error from "../../common/Error";
import FormItemLabel from "antd/es/form/FormItemLabel";

window.THREE = THREE;


const VERT_SHADER = `
varying vec2 screen_uv;
varying mat4 projection_matrix;
varying mat4 view_matrix;

void main() {
    gl_Position = vec4(position, 1);
    screen_uv = position.xy;
    projection_matrix = projectionMatrix;
    view_matrix = modelViewMatrix;
}
`;

const FRAG_SHADER = `
uniform mat4 ray_view_matrix;
uniform mat4 ray_model_matrix;

uniform highp sampler3D volume_texture;
uniform vec3 volume_shape;
uniform vec2 volume_range;
uniform vec3 volume_scale;
uniform vec3 volume_start;
uniform vec3 volume_end;
uniform float transparency;
uniform vec2 voxel_threshold;

varying vec2 screen_uv;
varying mat4 projection_matrix;
varying mat4 view_matrix;


float get_voxel(in vec3 tex_pos) {
    float voxel = texture(volume_texture, tex_pos).x;
    return (voxel - volume_range.x) / (volume_range.y - volume_range.x);
}


vec3 get_voxel_normal(in vec3 tex_pos) {
    vec4 e = vec4(1. / volume_shape, 0.);
    vec3 diff = vec3(
        get_voxel(tex_pos + e.xww) - get_voxel(tex_pos - e.xww),
        get_voxel(tex_pos + e.wyw) - get_voxel(tex_pos - e.wyw),
        get_voxel(tex_pos + e.wwz) - get_voxel(tex_pos - e.wwz)  
    );
    if (diff.x != 0. || diff.y != 0. || diff.z != 0.)
        return normalize(diff);
    else
        return vec3(0, 0, 1);     
}

vec3 voxel_color_gray(in float v, in vec3 pos, in vec3 dir) {
    return vec3(v);
}

vec3 voxel_color_uniform(in float v, in vec3 pos, in vec3 dir) {
    return vec3(.5);
}

vec3 voxel_color_rainbow(in float v, in vec3 pos, in vec3 dir) {
    return vec3(
        .7 + .3 * sin(v * 7.),
        .7 + .3 * sin(v * 9. + 4.),
        .7 + .3 * sin(v * 13. + 2.)
    );
}

vec3 voxel_color_normal(in float v, in vec3 pos, in vec3 dir) {
    return vec3(.5) + .45 * get_voxel_normal(pos);
}

vec3 voxel_color(in float voxel, in vec3 pos, in vec3 dir) { 
    vec3 color = voxel_color_{{color_mode}}(voxel, pos, dir);
    return color; 
}

// From https://www.shadertoy.com/view/4s23DR
bool cube(vec3 org, vec3 dir, out float near, out float far)
{
    // compute intersection of ray with all six bbox planes
    vec3 invR = 1.0/dir;
    vec3 tbot = invR * (-0.5 - org);
    vec3 ttop = invR * (0.5 - org);
    
    // re-order intersections to find smallest and largest on each axis
    vec3 tmin = min (ttop, tbot);
    vec3 tmax = max (ttop, tbot);
    
    // find the largest tmin and the smallest tmax
    vec2 t0 = max(tmin.xx, tmin.yz);
    near = max(t0.x, t0.y);
    t0 = min(tmax.xx, tmax.yz);
    far = min(t0.x, t0.y);
    
    // check for hit
    return near < far && far > 0.0;
}

bool is_inside_volume(in vec3 pos) {
    return (
        pos.x >= volume_start.x && pos.y >= volume_start.y && pos.z >= volume_start.z
     && pos.x <= volume_end.x   && pos.y <= volume_end.y   && pos.z <= volume_end.z
    );
}

vec3 render_cube(in vec3 ray_pos, in vec3 ray_dir, in float max_dist) {
    const float step_size = .005;
    //float voxel_strength = step_size * 30. * (1. - transparency);
    
    float t = 0.;
    vec3 color = vec3(0);
    vec2 ray_load = vec2(0);
    for (int i=0; i<400 && t<=max_dist; ++i, t+=step_size) {
        vec3 pos = ray_pos + t * ray_dir;
        pos = pos * volume_scale + .5;
        if (is_inside_volume(pos)) {
            float voxel = get_voxel(pos);
            
            if (voxel > voxel_threshold.x && voxel <= voxel_threshold.y) {
                vec3 vox_color = voxel_color(voxel, pos, ray_dir) * (1. - ray_load.x);
                color += vox_color;
                float strength = mix(voxel, dot(vox_color, vox_color), .5);
                ray_load.x += strength * 2. * (1. - 0.99 * transparency); 
            }
            if (ray_load.x >= 1.)
                break;
        }

        /*if (max(abs(pos.x), max(abs(pos.y), abs(pos.z))) > .51) {
            break;
        }*/
    }
    float depth = t / max_dist;
    //color = mix(color, vec3(depth), depth);
    return color * (1. - 0.99 * transparency);
}

vec3 render(in vec3 ray_pos, in vec3 ray_dir) {
    float near = 0., far = 0.;
    
    vec3 pos = (ray_model_matrix * vec4(ray_pos, 1)).xyz;
    vec3 dir = (ray_model_matrix * vec4(ray_dir, 0)).xyz;
    
    if (!cube(pos, dir, near, far)) {
        return vec3(0);
    } else {
        near = max(0., near);
        return render_cube(
            pos + dir * near,
            dir,
            far - near
        );
    }
}

void main() {
    vec3 ray_pos = vec3(0, 0, 0);
    vec3 ray_dir = normalize(vec3(screen_uv, 2));
    
    ray_pos = (ray_view_matrix * vec4(ray_pos, 1)).xyz;
    ray_dir = (ray_view_matrix * vec4(ray_dir, 0)).xyz;
    
    //gl_FragColor = vec4(screen_uv.x, screen_uv.y, 0, 1);
    //gl_FragColor = vec4(texture(volume_texture, vec3(screen_uv, 0.5)).xxx / volume_range.y, 1);
    //gl_FragColor = vec4(texture(test_texture, screen_uv).xyz, 1);

    gl_FragColor = vec4(render(ray_pos, ray_dir), 1.);
}
`;


const VolumeRenderer = ({width, height, image, ...props}) => {

    const mountRef = useRef(null);
    const context = useRef(null);
    const [error, set_error] = useState(null);
    const [compile_state, set_compile_state] = useState({
        color_mode: "normal",
    });
    const [state, set_state] = useState({
        scale_by_shape: true,
        scale_by_zoom: true,
        rotation_x: 0.,
        rotation_y: 0.,
        distance: 1.5,
        transparency: 0.,
        voxel_threshold: [0.07, 1.],
        slice_x: [0., 1.],
        slice_y: [0., 1.],
        slice_z: [0., 1.],
        smooth: false,
    });

    const get_fragment_code = () => {
        const code = (
            FRAG_SHADER
            .replaceAll("{{color_mode}}", compile_state.color_mode)
        );
        return code;
    }

    useEffect(() => {
        const scene = new THREE.Scene();
        //const camera = new THREE.PerspectiveCamera(75, 1.0, 0.1, 1000);
        const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
        camera.position.z = 1;

        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            cullFace: THREE.CullFaceNone,
        });
        renderer.setPixelRatio(window.devicePixelRatio);
        renderer.setClearColor('#000000');
        renderer.setSize(width, height);

        mountRef.current.appendChild(renderer.domElement);

        const geometry = new THREE.PlaneGeometry(2, 2);
        const material = new THREE.ShaderMaterial({
            vertexShader: VERT_SHADER,
            fragmentShader: get_fragment_code(),
            uniforms: {
                ray_view_matrix: {value: new THREE.Matrix4()},
                ray_model_matrix: {value: new THREE.Matrix4()},
                volume_texture: {value: null},
                volume_shape: {value: [1, 1, 1]},
                volume_range: {value: [0., 1.]},
                volume_scale: {value: [1., 1., 1.]},
                volume_start: {value: [0., 0., 0.]},
                volume_end: {value: [1., 1., 1.]},
                transparency: {value: 0.},
                voxel_threshold: {value: [0., 1.]},
            }
        });
        scene.add(new THREE.Mesh(geometry, material));

        context.scene = scene;
        context.renderer = renderer;
        context.camera = camera;
        context.material = material;
        context.update = () => {
            material.uniformsNeedUpdate = true;
            renderer.render(scene, camera);
        };

        return () => {
            if (mountRef.current)
                mountRef.current.removeChild(renderer.domElement);
        }
    }, []);

    useEffect(() => {
        if (context?.update) {
            context.material.fragmentShader = get_fragment_code();
            context.material.needsUpdate = true;
            context.update();
        }
    }, [context, compile_state]);

    useEffect(() => {
        if (context?.update) {
            if (image?.data) {
                const texture = new THREE.Data3DTexture(image.data, image.shape[2], image.shape[1], image.shape[0]);
                texture.format = THREE.RedFormat;
                texture.type = THREE.FloatType;
                texture.unpackAlignment = 1;
                texture.wrapR = THREE.ClampToEdgeWrapping;
                texture.wrapS = THREE.ClampToEdgeWrapping;
                texture.wrapT = THREE.ClampToEdgeWrapping;
                texture.magFilter = THREE.NearestFilter;
                texture.minFilter = THREE.NearestFilter;
                texture.needsUpdate = true;
                context.material.uniforms.volume_texture.value = texture;
                context.material.uniforms.volume_shape.value = image.shape;
                context.material.uniforms.volume_range.value = image.range;
            } else {
                context.material.uniforms.volume_texture.value = null;
            }

            context.update();
        }
    }, [context, image]);

    // update uniforms
    useEffect(() => {
        set_error(image?.error || null);

        if (context?.material && image?.shape) {

            const volume_sizes = [];
            for (let i=0; i<image.shape.length; ++i) {
                let size = 1.;
                if (state.scale_by_shape)
                    size *= image.shape[i];
                if (state.scale_by_zoom && image.zooms[i])
                    size *= image.zooms[i];
                volume_sizes.push(size);
            }
            const max_size = Math.max(...volume_sizes);
            context.material.uniforms.volume_scale.value = volume_sizes.map(z => max_size / z)
            //context.material.uniforms.volume_scale.value = [150. / 150., 150. / 100., 150. / 20.];

            context.material.uniforms.volume_start.value = [
                state.slice_x[0], state.slice_y[0], state.slice_z[0],
            ];
            context.material.uniforms.volume_end.value = [
                state.slice_x[1], state.slice_y[1], state.slice_z[1],
            ];

            const view_matrix = new THREE.Matrix4().setPosition(0, 0, -state.distance);
            context.material.uniforms.ray_view_matrix.value = view_matrix;

            const model_matrix = new THREE.Matrix4().makeRotationX(state.rotation_x);
            model_matrix.multiply(new THREE.Matrix4().makeRotationY(state.rotation_y));
            context.material.uniforms.ray_model_matrix.value = model_matrix;

            context.material.uniforms.transparency.value = state.transparency;
            context.material.uniforms.voxel_threshold.value = state.voxel_threshold;

            if (context.material.uniforms.volume_texture.value) {
                const voxel_filter = state.smooth ? THREE.LinearFilter : THREE.NearestFilter;
                if (voxel_filter !== context.material.uniforms.volume_texture.value.magFilter) {
                    context.material.uniforms.volume_texture.value.magFilter = voxel_filter;
                    context.material.uniforms.volume_texture.value.minFilter = voxel_filter;
                    context.material.uniforms.volume_texture.value.needsUpdate = true;
                }
            }
            context.update();
        }
    }, [context, state, image]);

    const handle_mouse_move = (event) => {
        if (event.buttons) {
            set_state({
                ...state,
                rotation_x: state.rotation_x - event.movementY / 100.,
                rotation_y: state.rotation_y + event.movementX / 100.,
            })
        }
    };

    const handle_mouse_wheel = (event) => {
        event.stopPropagation();
        event.preventDefault();
        set_state({
            ...state,
            distance: state.distance + event.deltaY / 1000.,
        });
    };

    return (
        <div>
            <Flex.Row marginX={".5rem"}>
                <Flex.Col>
                    {!error ? null : (
                        <Error>{error}</Error>
                    )}
                    <div
                        ref={mountRef}
                        onMouseMove={handle_mouse_move}
                        onWheel={handle_mouse_wheel}
                    />
                    <pre>
                        <div>shape:  {image?.shape?.join(", ")}</div>
                        <div>voxels: {image?.zooms?.join(" x ")}</div>
                        <div>range:  {image?.range?.join(" - ")}</div>
                        <div>dtype:  {image?.dtype}</div>
                        <div>bytes:  {image?.data?.byteLength}</div>
                    </pre>
                </Flex.Col>
                <Flex.Col style={{minWidth: "40rem"}}>
                    <Flex.Row margin={".3rem"}>
                        <Flex.Item>scale by shape</Flex.Item>
                        <Flex.Item>
                            <Switch
                                checked={state.scale_by_shape}
                                onChange={checked => set_state({...state, scale_by_shape: checked})}
                            />
                        </Flex.Item>
                        <Flex.Item>scale by voxel size</Flex.Item>
                        <Flex.Item>
                            <Switch
                                checked={state.scale_by_zoom}
                                onChange={checked => set_state({...state, scale_by_zoom: checked})}
                            />
                        </Flex.Item>
                    </Flex.Row>
                    <Flex.Item>
                        distance
                        <Slider
                            value={state.distance}
                            onChange={v => set_state({...state, distance: v})}
                            step={0.01}
                            min={0}
                            max={2}
                        />
                    </Flex.Item>
                    <Flex.Item>
                        transparency
                        <Slider
                            value={state.transparency}
                            onChange={v => set_state({...state, transparency: v})}
                            step={0.01}
                            min={0}
                            max={1}
                        />
                    </Flex.Item>
                    <Flex.Item>
                        voxel value threshold
                        <Slider
                            value={state.voxel_threshold}
                            onChange={v => set_state({...state, voxel_threshold: v})}
                            range
                            step={0.01}
                            min={0}
                            max={1}
                        />
                    </Flex.Item>
                    {["x", "y", "z"].map(axis => (
                        <Flex.Item key={axis}>
                            slice {axis.toUpperCase()}
                            <Slider
                                value={state[`slice_${axis}`]}
                                onChange={v => set_state({...state, [`slice_${axis}`]: v})}
                                range
                                step={0.01}
                                min={0}
                                max={1}
                            />
                        </Flex.Item>
                    ))}
                    <Flex.Row margin={".5rem"}>
                        <Flex.Item>
                            color<br/>
                            <Select
                                value={compile_state.color_mode}
                                onChange={v => set_compile_state({...compile_state, color_mode: v})}
                            >
                                <Option value={"uniform"}>uniform</Option>
                                <Option value={"gray"}>gray</Option>
                                <Option value={"rainbow"}>rainbow</Option>
                                <Option value={"normal"}>normal</Option>
                            </Select>
                        </Flex.Item>
                        <Flex.Item>
                            interpolation<br/>
                            <Switch
                                checked={state.smooth}
                                onChange={v => set_state({...state, smooth: v})}
                            />
                        </Flex.Item>
                    </Flex.Row>
                </Flex.Col>
            </Flex.Row>
        </div>
    );
};

export default VolumeRenderer;
