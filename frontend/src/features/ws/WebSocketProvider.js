import {createContext, useEffect, useState} from "react";
import {useAppDispatch} from "../../app/hooks";
import {requestStatus} from "../dashboard/dashboard-saga";
import {API_URLS} from "../../app/urls";
import {setWebsocketData} from "./websocket-slice";

const INIT_CONTEXT = {
    pending: false,
    connected: false,
    client_id: null,
    ws: null,
    trigger_request_status: null,
}
export const WebSocketContext = createContext(INIT_CONTEXT);


const WebSocketProvider = ({children}) => {
    const dispatch = useAppDispatch();

    const [web_socket, set_web_socket] = useState(null);
    const [connected, set_connected] = useState(false);
    const [pending, set_pending] = useState(false);
    const [client_id, set_client_id] = useState(null);
    //const [send_message, set_send_message] = useState(() => null);
    const [trigger_request_status, set_trigger_request_status] = useState(0);

    useEffect(() => {
        if (!web_socket) {
            set_connected(false);
            set_client_id(null);
            set_pending(true);
            set_web_socket(null);

            let ws_url;
            if (window.location.port?.length)
                ws_url = `ws://${window.location.hostname}:9009${API_URLS.WEBSOCKET}`;
            else
                ws_url = `ws://${window.location.hostname}${API_URLS.WEBSOCKET}`;

            const ws = new WebSocket(ws_url);

            ws.onopen = (event) => {
                set_web_socket(ws);
                set_connected(true);
                set_pending(false);
            };
            ws.onclose = (event) => {
                set_web_socket(null);
            }
            ws.onerror = (event) => {
                set_web_socket(null);
            }
            ws.onmessage = (event) => {
                const {name, data} = JSON.parse(event.data);
                switch (name) {
                    case "welcome":
                        set_client_id(data.client_id);
                        break;
                    case "status_change":
                        set_trigger_request_status(Math.random());
                        break;
                    default: {
                        const [plugin, uuid, what] = name.split(":");
                        dispatch(setWebsocketData({plugin, uuid, what, data}));
                    }

                }
            };
            ws.send_message = (name, data) => {
                ws.send(JSON.stringify({name, data}));
            };
            ws.send_plugin_message = (plugin, uuid, what, data) => {
                ws.send(JSON.stringify({name: `${plugin}:${uuid}:${what}`, data}));
            };
        }
    }, [web_socket]);

    return (
        <WebSocketContext.Provider
            value={{
                pending,
                connected,
                client_id,
                ws: web_socket,
                trigger_request_status,
            }}
        >
            {children}
        </WebSocketContext.Provider>
    )
};

export default WebSocketProvider;
