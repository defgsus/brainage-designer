import {createSlice} from "@reduxjs/toolkit";


const initialState = {
    get_response: null,
    module_objects: {}
};

export const processSlice = createSlice({
    name: "processSlice",
    initialState,
    reducers: {
        setProcessResponse: (state, action) => {
            state.get_response = action.payload;
        },
        setProcessModuleObjects: (state, action) => {
            const {process_uuid, module_uuid, response} = action.payload;
            state.module_objects[module_uuid] = response;
        },
    },
});

export const {
    setProcessResponse,
    setProcessModuleObjects,
} = processSlice.actions;
