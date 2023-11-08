import {AutoComplete, Button, Input, Modal} from "antd";
import {useEffect, useState} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {normalize_path, requestFileList} from "./form-saga";
import FileBrowserModal from "./FileBrowserModal";
import Flex from "/src/common/Flex";


const JsonInput = ({value, onChange, props}) => {
    const [encoded_value, set_encoded_value] = useState(null);

    useEffect(() => {
        try {
            set_encoded_value(JSON.stringify(value));
        } catch {
            set_encoded_value(null);
        }
    }, [value]);

    const handle_change = (e) => {
        try {
            const v = JSON.parse(e.target.value);
            if (onChange)
                onChange(v);
        } catch {

        }
    }

    return (
        <Input value={encoded_value} onChange={handle_change}{...props}/>
    );
};

export default JsonInput;
