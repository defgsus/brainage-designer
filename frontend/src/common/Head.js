import {Button, Modal} from "antd";
import {LoadingOutlined} from "@ant-design/icons";
import Flex from "/src/common/Flex";
import {IconHelp, IconReload} from "../icons";
import {useState} from "react";
import ReactMarkdown from "react-markdown";


const Head = ({title, sub_title, loading, onRefresh, actions, help, className, small, ...props}) => {
    const [help_visible, set_help_visible] = useState(false);

    className = className ? `${className} bad-head` : "bad-head";

    const render_action = (action) => {
        if (!action)
            return null;
        if (action.component)
            return action.component;

        const {name, title, action: callback, type, icon, disabled, ...extra} = action;
        return (
            <Button
                title={title}
                onClick={e => {e.stopPropagation(); callback(); }}
                type={type}
                icon={icon}
                disabled={loading || disabled}
                size={"small"}
                {...extra}
            >
                {name}
            </Button>
        )
    }
    if (typeof title === "string") {
        title = small ? <h3>{title}</h3> : <h2>{title}</h2>;
    }
    return (<>
        {!help_visible ? null : (
            <Modal
                open={help_visible}
                onOk={() => set_help_visible(false)}
                onCancel={() => set_help_visible(false)}
            >
                <ReactMarkdown>{help}</ReactMarkdown>
            </Modal>
        )}
        <Flex className={className} {...props}>
            <Flex.Item>
                {title}
                {!sub_title ? null : <div className={"sub-title"}>{sub_title}</div>}
            </Flex.Item>
            <Flex.Item grow={1}/>
            <Flex.Row wrap margin={".5rem"} align={"center"}>
                {!actions ? null : (
                    actions.map(render_action).filter(comp => !!comp).map((comp, i) => (
                        <Flex.Item key={i}>
                            {comp}
                        </Flex.Item>
                    ))
                )}
                {!help ? null : (
                    <Button
                        title={"Show help"}
                        icon={<IconHelp title={null}/>}
                        onClick={() => set_help_visible(true)}
                    />
                )}
                <Flex.Item>
                    {!onRefresh
                        ? (
                            loading ? <LoadingOutlined/> : null
                        ) : (
                            <Button
                                loading={loading}
                                icon={<IconReload/>}
                                onClick={() => onRefresh()}
                            />
                        )}
                </Flex.Item>
            </Flex.Row>
        </Flex>
    </>)
}

export default Head;