import {useState} from "react";
import "./Json.scss"
import {Modal} from "antd";


const Json = ({data, className, ...props}) => {

    const [expanded, set_expanded] = useState(false);

    const json_full = JSON.stringify(data, null, 2);
    let json_short = JSON.stringify(data);
    if (json_short?.length > 32) {
        json_short = `${json_short.slice(0, 30)}..`;
    }

    className = className ? `${className} json` : "json";
    return (
        <>
            <Modal
                open={expanded}
                width={"90%"}
                destroyOnClose={true}
                onOk={() => set_expanded(false)}
                onCancel={() => set_expanded(false)}
            >
                <pre>{expanded ? json_full : null}</pre>
            </Modal>

            <code
                className={className}
                onClick={() => set_expanded(!expanded)}
                {...props}
            >
                {json_short}
            </code>
        </>
    );
};

export default Json;