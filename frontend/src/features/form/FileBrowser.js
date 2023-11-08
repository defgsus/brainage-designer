import {useEffect, useState} from "react";
import {produce} from "immer";
import {
    CaretDownOutlined,
    CaretRightOutlined,
    FileImageOutlined,
    FileOutlined,
    LoadingOutlined
} from "@ant-design/icons";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {normalize_path, requestFileList} from "./form-saga";
import Json from "/src/common/Json";
import "./FileBrowser.scss"
import ImageViewer from "./ImageViewer";
import Flex from "../../common/Flex";
import {Pagination, Switch} from "antd";


const remove_trailing_slash = (path) => {
    if (typeof path === "string") {
        while (path.endsWith("/"))
            path = path.slice(0, path.length - 1);
        return normalize_path(path);
    }
    return path;
}


const FileBrowser = ({path, on_file_change, path_only, namespace, page_size=30, ...props}) => {
    const dispatch = useAppDispatch();
    const {file_list} = useAppSelector(state => state.form);
    const [file_items, set_file_items] = useState({});
    const [current_path, set_current_path] = useState(remove_trailing_slash(path) || "/");
    const [file_viewer, set_file_viewer] = useState(null);
    const [show_files, set_show_files] = useState(!path_only);

    const file_type_mapping = {
        "image": {
            icon: <FileImageOutlined/>,
            viewer: filename => <ImageViewer filename={filename}/>,
        },
    };

    const handle_file_click = (info) => {
        const type_info = file_type_mapping[info.type];
        if (type_info?.viewer) {
            set_file_viewer({
                path: info.full_path,
                viewer: type_info.viewer,
            })
        }
    }

    const directory_click = (dir, path) => {
        let new_path = dir.path;

        // close
        if (dir.children) {
            // get parent path
            const split_path = new_path.split("/");
            if (split_path.length > 1)
                new_path = split_path.slice(0, split_path.length - 1).join("/");
            else
                new_path = "/";

        // open
        } else {
            // set full children path
        }

        new_path = new_path || "/";
        set_current_path(new_path);
        if (on_file_change)
            on_file_change(new_path);
    };

    useEffect(() => {
        set_current_path(remove_trailing_slash(path));
    }, [path]);

    useEffect(() => {
        dispatch(requestFileList({path: current_path, recursive: true, namespace}));
    }, [current_path, namespace]);

    useEffect(() => {
        set_file_items(file_list[namespace]);
    }, [file_list, namespace]);

    useEffect(() => {
        set_show_files(!path_only);
    }, [path_only])

    // --- rendering ---

    const FileList = ({items, parent_path}) => {
        const [cur_file_page, set_cur_file_page] = useState(0);

        useEffect(() => {
            if (!items?.files)
                set_cur_file_page(0);
            else {
                const num_pages = Math.floor(items.files.length / page_size);
                if (cur_file_page >= num_pages)
                    set_cur_file_page(Math.max(0, num_pages - 1));
            }
        }, [items, cur_file_page]);

        if (!items)
            return <LoadingOutlined/>;

        return (
            <>
                {items.dirs?.length || items.files?.length ? null : (
                    <div className={"empty-dir"}>..empty..</div>
                )}
                {items.dirs?.map(dir => {
                    const full_path = `${parent_path}/${dir.name}`;
                    return (
                        <div key={dir.name}>
                            <div
                                className={"file-row"}
                            >
                                <div
                                    className={"file-icon clickable"}
                                    onClick={() => directory_click(dir, full_path)}
                                >
                                    {dir.children ? <CaretDownOutlined/> : <CaretRightOutlined/>}
                                </div>
                                <div
                                    className={"dir-name clickable selectable" + (
                                        full_path === current_path ? " selected" : ""
                                    )}
                                    onClick={() => directory_click(dir, full_path)}
                                >
                                    {dir.name}
                                </div>
                            </div>
                            {!dir.children ? null : (
                                <div className={"sub-files"}>
                                    <FileList key={full_path} items={dir.children} parent_path={full_path}/>
                                </div>
                            )}
                        </div>
                    )
                })}
                {!(show_files && items.files) ? null : (
                    <>
                        {items.files.length <= page_size ? null : (
                            <Pagination
                                pageSize={page_size}
                                total={items.files.length}
                                current={cur_file_page + 1}
                                onChange={(page, size) => set_cur_file_page(page - 1)}
                                showSizeChanger={false}
                                size={"small"}
                            />
                        )}
                        {items.files
                            .slice(cur_file_page * page_size, (cur_file_page + 1) * page_size)
                            .map(file => {
                                const full_path = `${parent_path}/${file.name}`;
                                const type_info = file_type_mapping[file.type];
                                return (
                                    <div key={file.name}>
                                        <div
                                            className={"file-row"}
                                            onClick={() => handle_file_click({
                                                ...file,
                                                full_path: full_path,
                                            })}
                                        >
                                            <div className={"file-icon"}>
                                                {type_info?.icon || <FileOutlined/>}
                                            </div>
                                            <div className={"file-name"}>
                                                {file.name}
                                            </div>
                                        </div>
                                        {file_viewer?.path !== full_path ? null : (
                                            file_viewer.viewer(full_path)
                                        )}
                                    </div>
                                );
                            })}
                    </>
                )}
            </>
        );
    };

    return (
        <div className={"file-browser"} {...props}>
            <Flex.Row>
                <Flex.Item grow={1}>
                    <h3>{current_path}</h3>
                </Flex.Item>
                {!path_only ? null : <Flex.Item>
                    show files <Switch checked={show_files} onChange={set_show_files}></Switch>
                </Flex.Item>}
            </Flex.Row>
            <FileList items={file_items} parent_path={""}/>
            {/*<Json data={file_items}/>*/}
        </div>
    );
};

export default FileBrowser;
