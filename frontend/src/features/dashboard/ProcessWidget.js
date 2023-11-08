import {Button, Card, Col, Form, Modal, Row, Table} from "antd";
import {useEffect, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {WebSocketContext} from "/src/features/ws/WebSocketProvider";
import TableView from "/src/features/tableview/TableView";
import {API_URLS} from "/src/app/urls";


const ProcessWidget = () => {
    const dispatch = useAppDispatch();

    const socket_context = useContext(WebSocketContext);

    return (
        <>
            <Card className={"process-widget"} title={"processes"}>
                <TableView
                    url={API_URLS.PROCESS.TABLE}
                    defaultPageSize={5}
                />
            </Card>
        </>
    )
};

export default ProcessWidget;