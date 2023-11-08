import {
    CheckCircleTwoTone, CheckOutlined,
    CloseCircleTwoTone, CloseOutlined, CopyTwoTone,
    EditTwoTone, EyeOutlined, LoadingOutlined,
    PlusCircleTwoTone, QuestionCircleTwoTone, ReloadOutlined
} from "@ant-design/icons";
import "./index.scss"


export const IconDelete = (props) => {
    return <CloseCircleTwoTone twoToneColor={"red"} title={"remove"} {...props}/>;
};

export const IconEdit = (props) => {
    return <EditTwoTone twoToneColor={"green"} title={"edit"} {...props}/>;
};

export const IconAdd = ({disabled, onClick, ...props}) => {
    return (
        <PlusCircleTwoTone
            twoToneColor={disabled ? "gray" : "blue"}
            title={"add"}
            onClick={(disabled ? null : onClick) || null}
            {...props}
        />
    );
};

export const IconCopy = (props) => {
    return <CopyTwoTone twoToneColor={"blue"} title={"copy"} {...props}/>;
};

export const IconCheck = (props) => {
    return <CheckOutlined {...props}/>;
};

export const IconCross = (props) => {
    return <CloseOutlined {...props}/>;
};

export const IconShow = (props) => {
    return <EyeOutlined {...props}/>;
};


export const IconHelp = (props) => {
    return <QuestionCircleTwoTone title={"help"} twoToneColor={"#20c050"} {...props}/>;
};

export const IconReload = ({className, loading, title, ...props}) => {
    title = title || "reload";
    className = className ? `${className} icon-reload-color` : "icon-reload-color";

    return loading
        ? (
            <LoadingOutlined
                title={title}
                className={className}
                {...props}
            />
        ) : (
            <ReloadOutlined
                title={title}
                className={className}
                {...props}
            />
        );
};
