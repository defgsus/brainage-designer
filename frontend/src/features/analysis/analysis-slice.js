import {createSlice} from "@reduxjs/toolkit";


const initialState = {
    get_response: null,
    get_result_response: null,
    get_average_result_response: null,
    create_response: null,
    source_preview_response: null,
};

export const analysisSlice = createSlice({
    name: "analysisSlice",
    initialState,
    reducers: {
        setAnalysisCreateResponse: (state, action) => {
            state.create_response = action.payload;
        },
        setAnalysisResponse: (state, action) => {
            state.get_response = action.payload;
        },
        setAnalysisResultResponse: (state, action) => {
            state.get_result_response = action.payload;
        },
        setAnalysisAverageResultResponse: (state, action) => {
            state.get_average_result_response = action.payload;
        },
        setAnalysisSourcePreviewResponse: (state, action) => {
            state.source_preview_response = action.payload;
        },
    },
});

export const {
    setAnalysisCreateResponse,
    setAnalysisResponse,
    setAnalysisSourcePreviewResponse,
    setAnalysisResultResponse,
    setAnalysisAverageResultResponse,
} = analysisSlice.actions;
