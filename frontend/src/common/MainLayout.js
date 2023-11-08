import {Col, Layout, Row} from "antd";
import {CheckCircleTwoTone, StopTwoTone, LoadingOutlined} from "@ant-design/icons";
import {useContext} from "react";
import {WebSocketContext} from "../features/ws/WebSocketProvider";
import "./MainLayout.scss"
import {Link} from "react-router-dom";
import {APP_URLS} from "/src/app/urls";
import Flex from "/src/common/Flex";


const MainLayout = ({children, loading, ...props}) => {
    const {pending, connected, client_id} = useContext(WebSocketContext);

    let connection_icon;
    if (pending) {
        connection_icon = <LoadingOutlined title={"trying to connect"} className={"loading-"}/>;
    } else {
        if (connected) {
            connection_icon = <CheckCircleTwoTone
                twoToneColor={"#4f4"}
                title={`connected as "${client_id}"`}
            />;
        } else {
            connection_icon = <StopTwoTone
                twoToneColor={"#f44"}
                title={"not connected"}
            />;
        }
    }

    return (
        <Layout {...props}>
            <Layout.Header style={{paddingInline: "0"}}>
                <Flex className={"header-content"}>
                    <Flex.Item>
                        <Link to={APP_URLS.DASHBOARD}>
                            <div className={"brain-logo"}/>
                        </Link>
                    </Flex.Item>
                    <Flex.Grow/>
                    <Flex.Item className={"layout-headline"}>
                        {"BrainAGE Designer"}
                    </Flex.Item>
                    <Flex.Grow/>
                    <Flex.Item>
                        {connection_icon}
                    </Flex.Item>
                </Flex>
            </Layout.Header>
            <Layout.Content>
                {loading ? <LoadingOutlined/> : children}
            </Layout.Content>
            <Layout.Footer style={{textAlign: "center"}}>
                (c) 2022, 2023 <a href={"https://netzkolchose.de/"}>netzkolchose.de</a>
            </Layout.Footer>
        </Layout>
    );
}

export default MainLayout;
