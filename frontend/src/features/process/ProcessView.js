import {Button, Col, Row} from "antd";
import {useEffect, useState} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {useMatch} from "react-router";
import {API_URLS, APP_URLS} from "/src/app/urls";
import {requestProcess} from "./process-saga";
import TableView from "/src/features/tableview/TableView";
import {LoadingOutlined} from "@ant-design/icons";
import PageFrame from "/src/common/PageFrame";
import Values from "../../common/Values";
import Head from "../../common/Head";


const ProcessView = (props) => {
    const dispatch = useAppDispatch();

    const {get_response} = useAppSelector(state => state.process);
    const [loading, set_loading] = useState(false);

    const match = useMatch(APP_URLS.PROCESS.VIEW);
    const uuid = match.params.p_id;

    const refresh = () => {
        set_loading(true);
        dispatch(requestProcess({uuid}));
    };

    useEffect(() => {
        if (get_response?.uuid !== uuid) {
            refresh()
        } else {
            set_loading(false);
        }
    }, [get_response, uuid]);

    return (
        <PageFrame
            title={"process"}
            uuid={uuid}
            loading={loading}
            onRefresh={refresh}
        >
            <Row>
                <Col xs={24} md={12}>
                    <Values values={get_response}/>
                </Col>
            </Row>

            <Head title={"events"}/>
            <TableView
                url={API_URLS.PROCESS.EVENT.TABLE}
                filters={{process_uuid: uuid}}
            />
        </PageFrame>
    )
};

export default ProcessView;
