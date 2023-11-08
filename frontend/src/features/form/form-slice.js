import {createSlice} from "@reduxjs/toolkit";
import {normalize_path} from "./form-saga";


const initialState = {
    file_list: {/*
        "<namespace>": {
            path: "/",
            dirs: [...],
            files: [...],
        }
    */},
    image_meta: {},
    image_volumes: {/*
        path: <str>,
        data: <Float32Array>,
        shape: [<int>, ...],
        zooms: [<float>, ...],
        range: [<float>, <float>],
        dtype: <str>,
        timestamp: <int>,
    */},
};

export const formSlice = createSlice({
    name: "formSlice",
    initialState,
    reducers: {
        setFileList: (state, action) => {
            const {namespace, data} = action.payload;
            state.file_list[namespace] = {
                ...data,
                timestamp: new Date().getTime(),
            };
        },
        setImageMeta: (state, action) => {
            const {path, ...data} = action.payload;
            state.image_meta[path] = {
                path,
                ...data,
                timestamp: new Date().getTime(),
            };
        },
        setImageVolume: (state, action) => {
            const {path, ...data} = action.payload;
            state.image_volumes[path] = {
                path,
                ...data,
                timestamp: new Date().getTime(),
            };
        },
        clearImageVolume: (state, action) => {
            let {path} = action.payload;
            console.log("DELETE", path);
            path = normalize_path(path);
            delete state.image_volumes[path];
        },
    },
});

export const {
    setFileList,
    setImageMeta,
    setImageVolume,
    clearImageVolume,
} = formSlice.actions;
