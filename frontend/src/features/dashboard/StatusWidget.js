import {Card, Col, Row} from "antd";
import {useEffect, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {requestStatus} from "./dashboard-saga";
import {LoadingOutlined} from "@ant-design/icons";
import {WebSocketContext} from "/src/features/ws/WebSocketProvider";


const StatusWidget = () => {
    const dispatch = useAppDispatch();

    const socket_context = useContext(WebSocketContext);
    const {status} = useAppSelector(state => state.dashboard);

    const [loading, set_loading] = useState(true);

    useEffect(() => {
        set_loading(true);
        dispatch(requestStatus());
    }, [socket_context.trigger_request_status]);

    useEffect(() => {
        if (status)
            set_loading(false);
    }, [status]);

    return (
        <Card className={"status-widget"}>
            <h3>status</h3>
            <pre>
                {JSON.stringify(socket_context, null, 2)}
            </pre>
            {loading
                ? <LoadingOutlined/>
                : (
                    <pre>
                        {JSON.stringify(status, null, 2)}
                    </pre>
                )
            }
        </Card>
    )
};

export default StatusWidget;