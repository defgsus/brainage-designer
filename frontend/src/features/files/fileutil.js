import {FileImageOutlined, FileOutlined} from "@ant-design/icons";


export const join_paths = (...parts) => {
    const result = [];
    for (let arg of parts) {
        if (!arg || arg === ".")
            continue;
        if (!result.length) {
            result.push(arg);
        } else {
            if (arg?.startsWith("/"))
                arg = arg.slice(1);
            result.push(arg);
        }
    }
    return result.join("/");
}

export const get_file_type = (filename) => {
    if (!filename)
        return null;
    filename = filename.toLowerCase();
    if (filename.endsWith(".nii") || filename.endsWith(".nii.gz"))
        return "image";

    return null;
}

export const get_file_type_icon = (type) => {
    switch (type) {
        case "image": return <FileImageOutlined/>;
        default: return <FileOutlined/>;
    }
}
