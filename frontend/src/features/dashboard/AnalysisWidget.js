import {Button, Card, Col, Form, Modal, Row, Table} from "antd";
import {useEffect, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import TableView from "/src/features/tableview/TableView";
import {API_URLS} from "/src/app/urls";
import NewAnalysisModal from "../analysis/NewAnalysisModal";


const AnalysisWidget = () => {
    const dispatch = useAppDispatch();

    // const socket_context = useContext(WebSocketContext);

    const [modal_trigger, set_modal_trigger] = useState(0);
    const [form] = Form.useForm();

    const handle_new = (event) => {
        set_modal_trigger(Math.random())
    }

    return (
        <>
            <NewAnalysisModal trigger={modal_trigger}/>
            <Card className={"analysis-widget"} title={"analysis pipelines"}>
                <div>
                    <Button
                        onClick={handle_new}
                        type={"primary"}
                    >
                        new analysis pipeline
                    </Button>
                    <TableView
                        url={API_URLS.ANALYSIS.TABLE}
                        defaultPageSize={5}
                    />
                </div>
            </Card>
        </>
    )
};

export default AnalysisWidget;