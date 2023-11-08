import {Tag} from "antd";
import "./AutoTag.scss";


const AutoTag = ({tag, className, ...props}) => {
    if (!tag)
        return null;

    let color;
    if (typeof tag === "string") {
        switch (tag.toLowerCase()) {
            case "requested":
                color = "cyan"; break;
            case "started":
                color = "blue"; break;
            case "finished":
                color = "green"; break;
            case "failed":
            case "exception":
            case "killed":
                color = "red"; break;
        }
    }
    className = className ? `${className} autotag` : "autotag";
    return (
        <Tag
            color={color}
            className={className}
            {...props}
        >
            {tag}
        </Tag>
    )
}

export default AutoTag;
