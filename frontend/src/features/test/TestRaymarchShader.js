import {useEffect, useRef, useState} from "react";
import * as THREE from 'three';

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

varying vec2 screen_uv;
varying mat4 projection_matrix;
varying mat4 view_matrix;


// https://iquilezles.org/articles/distfunctions/
float sdTorus( vec3 p, vec2 t )
{
  vec2 q = vec2(length(p.xz)-t.x,p.y);
  return length(q)-t.y;
}

float sdBoxFrame( vec3 p, vec3 b, float e )
{
  p = abs(p  )-b;
  vec3 q = abs(p+e)-e;
  return min(min(
      length(max(vec3(p.x,q.y,q.z),0.0))+min(max(p.x,max(q.y,q.z)),0.0),
      length(max(vec3(q.x,p.y,q.z),0.0))+min(max(q.x,max(p.y,q.z)),0.0)),
      length(max(vec3(q.x,q.y,p.z),0.0))+min(max(q.x,max(q.y,p.z)),0.0));
}

float scene_distance(in vec3 pos) {
    float d = 10000.;
    d = min(d, dot(pos - vec3(0, -2, 0), vec3(0, 1, 0)));
    d = min(d, sdTorus((pos).xzy, vec2(.5, .1)));
    //d = min(d, length(pos) - .5);
    d = min(d, sdBoxFrame(pos, vec3(.3), .02));
    return d;
}

vec3 scene_normal(in vec3 pos) {
    const vec2 e = vec2(0.001, 0);
    return normalize(vec3(
        scene_distance(pos + e.xyy) - scene_distance(pos - e.xyy),
        scene_distance(pos + e.yxy) - scene_distance(pos - e.yxy),
        scene_distance(pos + e.yyx) - scene_distance(pos - e.yyx)  
    ));
}

vec3 render(in vec3 ray_pos, in vec3 ray_dir) {
    const float max_dist = 20.;

    float t = 0.;
    vec3 color = vec3(0);
    for (int i=0; i<100 && t<=max_dist; ++i) {
        vec3 pos = ray_pos + t * ray_dir;
        pos = (ray_model_matrix * vec4(pos, 1)).xyz;
        float d = scene_distance(pos);
        if (abs(d) <= 0.0001) {
            color = scene_normal(pos) * .5 + .5;
            break;
        }
        t += d;
    }
    float depth = t / max_dist;
    color = mix(color, vec3(depth), depth);
    return color;
}

void main() {
    vec3 ray_pos = vec3(0, 0, 0);
    vec3 ray_dir = normalize(vec3(screen_uv, 2));
    
    ray_pos = (ray_view_matrix * vec4(ray_pos, 1)).xyz;
    ray_dir = (ray_view_matrix * vec4(ray_dir, 0)).xyz;
    
    //gl_FragColor = vec4(screen_uv.x, screen_uv.y, 0, 1);
    gl_FragColor = vec4(render(ray_pos, ray_dir), 1.);
}
`;


const TestRaymarchShader = (props) => {

    const mountRef = useRef(null);
    const [context, set_context] = useState();
    const [state, set_state] = useState({
        rotation_x: 0.,
        rotation_y: 0.,
    });

    useEffect(() => {
        const scene = new THREE.Scene();
        //const camera = new THREE.PerspectiveCamera(75, 1.0, 0.1, 1000);
        const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 100);
        camera.position.z = 1;

        const renderer = new THREE.WebGLRenderer({
            antialias: true,
            cullFace: THREE.CullFaceNone,
        });
        renderer.setClearColor('#000000');
        renderer.setSize(256, 256);

        mountRef.current.appendChild(renderer.domElement);

        const geometry = new THREE.PlaneGeometry(2, 2);
        const material = new THREE.ShaderMaterial({
            vertexShader: VERT_SHADER,
            fragmentShader: FRAG_SHADER,
            uniforms: {
                ray_view_matrix: {value: new THREE.Matrix4().setPosition(0, 0, -2)},
                ray_model_matrix: {value: new THREE.Matrix4()},
            }
        });
        scene.add(new THREE.Mesh(geometry, material));

        set_context({
            scene, renderer, camera, material,
            update: () => {
                material.uniformsNeedUpdate = true;
                renderer.render(scene, camera)
            },
        });

        return () => mountRef.current.removeChild(renderer.domElement);
    }, []);

    useEffect(() => {
        if (context?.update) {
            const matrix = new THREE.Matrix4().makeRotationX(state.rotation_x);
            matrix.multiply(new THREE.Matrix4().makeRotationY(state.rotation_y));

            context.material.uniforms.ray_model_matrix.value = matrix;

            context.update();
        }
    }, [context, state]);

    const handle_mouse_move = (event) => {
        if (event.buttons) {
            set_state({
                ...state,
                rotation_x: state.rotation_x - event.movementY / 100.,
                rotation_y: state.rotation_y + event.movementX / 100.,
            })
        }
    };

    return (
        <div
            ref={mountRef}
            onMouseMove={handle_mouse_move}
        />
    );
};

export default TestRaymarchShader;

