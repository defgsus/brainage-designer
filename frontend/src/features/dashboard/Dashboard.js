import {Col, Row} from "antd";
import {useEffect} from "react";
import {useAppDispatch} from "/src/app/hooks";
import {requestDashboard} from "./dashboard-saga";
import StatusWidget from "./StatusWidget";
import PreprocessingWidget from "./PreprocessingWidget";
import ProcessWidget from "./ProcessWidget";
import AnalysisWidget from "./AnalysisWidget";


const Dashboard = () => {
    const dispatch = useAppDispatch();

    useEffect(() => {
        dispatch(requestDashboard());
    }, []);

    return (
        <div className={"dashboard"}>
            <Row>
                <Col xs={24} l={12}><PreprocessingWidget/></Col>
                <Col xs={24} l={12}><AnalysisWidget/></Col>
                <Col xs={24} l={12}><ProcessWidget/></Col>
                <Col xs={24} l={12}><StatusWidget/></Col>
            </Row>
        </div>
    )
};

export default Dashboard;