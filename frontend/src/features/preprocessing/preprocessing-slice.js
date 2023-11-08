import {createSlice} from "@reduxjs/toolkit";


const initialState = {
    get_response: null,
    create_response: null,
};

export const preprocessingSlice = createSlice({
    name: "preprocessingSlice",
    initialState,
    reducers: {
        setPreprocessCreateResponse: (state, action) => {
            state.create_response = action.payload;
        },
        setPreprocessResponse: (state, action) => {
            state.get_response = action.payload;
        },
    },
});

export const {
    setPreprocessResponse,
    setPreprocessCreateResponse,
} = preprocessingSlice.actions;
