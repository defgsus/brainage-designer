import {APP_URLS, OBJECT_URLS} from "/src/app/urls";
import {Link} from "react-router-dom";
import {useEffect, useState} from "react";


const Uuid = ({uuid, length, className, fullName, ...props}) => {
    const [display_props, set_display_props] = useState({
        prefix: null, text: uuid, url: null, title: uuid
    });

    uuid = uuid || "-";

    useEffect(() => {
        let text = uuid;
        let prefix = null;
        let title = uuid;
        let url = null;

        if (text.length > ((length || 14) + 2)) {
            text = `${text.slice(0, length || 14)}..`;
        }

        const id_prefix = uuid.split("-")[0];
        if (OBJECT_URLS[id_prefix]) {
            const obj_url = OBJECT_URLS[id_prefix];
            url = obj_url.url.replace(`:${id_prefix}_id`, uuid);
            title = `${obj_url.name} ${uuid}`;
            if (fullName)
                prefix = obj_url.name;
        }
        set_display_props({text, prefix, url, title});

    }, [uuid, length, fullName]);

    className = className ? `${className} uuid nowrap` : "uuid nowrap";

    let content = (
        <code
            className={className}
            {...props}
            title={display_props.title}
        >
            {display_props.text}
        </code>
    );
    if (display_props.url) {
        content = <Link to={display_props.url}>{content}</Link>;
    }
    if (display_props.prefix) {
        content = <>{display_props.prefix} {content}</>
    }

    return content;
}

export default Uuid;