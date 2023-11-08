import {Button, Card, Col, Form, Modal, Row, Table} from "antd";
import {useEffect, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {WebSocketContext} from "/src/features/ws/WebSocketProvider";
import {requestPreprocessCreate} from "/src/features/preprocessing/preprocessing-saga";
import {history} from "/src/store";
import {APP_URLS} from "../../app/urls";
import NewAnalysisForm from "./NewAnalysisForm";
import {requestAnalysisCreate} from "./analysis-saga";


const NewAnalysisModal = ({trigger, ...props}) => {
    const dispatch = useAppDispatch();

    const socket_context = useContext(WebSocketContext);
    const {create_response} = useAppSelector(state => state.analysis);

    const [modal_visible, set_modal_visible] = useState(false);
    const [requested, set_requested] = useState(false);
    const [form] = Form.useForm();

    useEffect(() => {
        if (trigger)
            set_modal_visible(true);
    }, [trigger]);

    useEffect(() => {
        if (requested && create_response) {
            set_requested(false);
            history.push(APP_URLS.ANALYSIS.VIEW.replace(":ap_id", create_response.uuid));
        }
    }, [requested, create_response]);

    const on_form_finish = () => {
        set_requested(true);
        dispatch(requestAnalysisCreate(form.getFieldsValue()));
    }

    return (
        <>
            <Modal
                open={modal_visible}
                title={"create analysis pipeline"}
                okText={"create"}
                onOk={() => form.submit()}
                onCancel={() => set_modal_visible(false)}
            >
                <Form.Provider onFormFinish={on_form_finish}>
                    <NewAnalysisForm form={form}/>
                </Form.Provider>
            </Modal>
        </>
    )
};

export default NewAnalysisModal;