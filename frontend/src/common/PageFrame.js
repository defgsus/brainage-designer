import {Button, Row, Col} from "antd";
import Head from "./Head";


const PageFrame = ({title, uuid, loading, onRefresh, actions, help, children, ...props}) => {
    return (
        <div className={"page-frame"}>
            <Head
                title={<><h2>{title}</h2>{uuid}</>}
                loading={loading}
                onRefresh={onRefresh}
                actions={actions}
                help={help}
            />
            {children}
        </div>
    )
}

export default PageFrame;