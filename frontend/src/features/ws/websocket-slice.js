import {createSlice} from "@reduxjs/toolkit";


const initialState = {
    websocket_data: {},
};

export const websocketSlice = createSlice({
    name: "websocketSlice",
    initialState,
    reducers: {
        // clears all other uuids
        setWebsocketUuid: (state, action) => {
            const {plugin, uuid} = action.payload;
            state.websocket_data = {
                ...state.websocket_data,
                [plugin]: {
                    [uuid]: (state.websocket_data[plugin] && state.websocket_data[plugin][uuid]) || {}
                }
            };
        },
        setWebsocketData: (state, action) => {
            const {plugin, uuid, what, data} = action.payload;
            state.websocket_data[plugin] = {
                ...state.websocket_data[plugin],
                [uuid]: {
                    ...(state.websocket_data[plugin] && state.websocket_data[plugin][uuid]),
                    [what]: data
                        //...(state.websocket_data[plugin] && state.websocket_data[plugin][uuid] && state.websocket_data[plugin][uuid][what]),
                }
            }
        }
    },
});

export const {
    setWebsocketUuid,
    setWebsocketData,
} = websocketSlice.actions;
