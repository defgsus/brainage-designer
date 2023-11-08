import {Button, Card, Col, Form, Modal, Row, Table} from "antd";
import {useEffect, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import TableView from "/src/features/tableview/TableView";
import NewPreprocessModal from "/src/features/preprocessing/NewPreprocessModal";
import {API_URLS} from "/src/app/urls";


const PreprocessingWidget = () => {
    const dispatch = useAppDispatch();

    // const socket_context = useContext(WebSocketContext);

    const [modal_trigger, set_modal_trigger] = useState(0);
    const [form] = Form.useForm();

    const handle_new = (event) => {
        //dispatch(requestPreprocessCreate());
        set_modal_trigger(Math.random())
    }

    return (
        <>
            <NewPreprocessModal trigger={modal_trigger}/>
            <Card className={"preprocessing-widget"} title={"preprocessing pipelines"}>
                <div>
                    <Button
                        onClick={handle_new}
                        type={"primary"}
                    >
                        new preprocessing pipeline
                    </Button>
                    <TableView
                        url={API_URLS.PREPROCESSING.TABLE}
                        defaultPageSize={5}
                    />
                </div>
            </Card>
        </>
    )
};

export default PreprocessingWidget;