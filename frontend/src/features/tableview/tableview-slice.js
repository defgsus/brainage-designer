import {createSlice} from "@reduxjs/toolkit";


const initialState = {
    tables_per_url: {},
};

export const tableviewSlice = createSlice({
    name: "tableviewSlice",
    initialState,
    reducers: {
        setTableResponse: (state, action) => {
            const {url, namespace, data} = action.payload;
            state.tables_per_url[`${namespace}${url}`] = {
                ...state.tables_per_url[`${namespace}${url}`],
                response: data,
                needs_update: false,
            };
        },
        updateTableOptions: (state, action) => {
            const {url, namespace} = action.payload;
            state.tables_per_url[`${namespace}${url}`] = {
                ...state.tables_per_url[`${namespace}${url}`],
                ...{...action.payload, url: undefined, namespace: undefined},
                needs_update: true,
            };
        }
    },
});

export const {
    setTableResponse,
    updateTableOptions,
} = tableviewSlice.actions;
