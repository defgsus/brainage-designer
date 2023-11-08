import {createSlice} from "@reduxjs/toolkit";

const initialState = {
    dashboard: null,
    status: null,
};

export const dashboardSlice = createSlice({
    name: "dashboardReducer",
    initialState,
    reducers: {
        setDashboard: (state, action) => {
            state.dashboard = action.payload;
        },
        setStatus: (state, action) => {
            state.status = action.payload;
        },
    },
});

export const {
    setDashboard,
    setStatus,
} = dashboardSlice.actions;
