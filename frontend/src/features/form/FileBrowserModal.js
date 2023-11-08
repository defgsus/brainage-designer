import {useEffect, useState} from "react";
import {Modal} from "antd";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import FileBrowser from "./FileBrowser";


const FileBrowserModal = ({onOk, onCancel, trigger, initial_path, path_only, ...props}) => {

    const [modal_visible, set_modal_visible] = useState(false);
    const [current_file, set_current_file] = useState(initial_path || null);

    useEffect(() => {
        if (trigger) {
            set_modal_visible(true);
        }
    }, [trigger]);

    return (
        <Modal
            {...props}
            open={modal_visible}
            onOk={() => {
                set_modal_visible(false);
                if (onOk)
                    onOk(current_file);
            }}
            onCancel={() => {
                set_modal_visible(false);
                if (onCancel)
                    onCancel();
            }}
            bodyStyle={{paddingTop: "17px"}}
        >
            {!modal_visible ? null : (
                <FileBrowser
                    path={initial_path}
                    on_file_change={set_current_file}
                    path_only={path_only}
                />
            )}
        </Modal>
    )
};

export default FileBrowserModal;
