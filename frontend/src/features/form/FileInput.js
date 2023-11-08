import {AutoComplete, Button, Modal} from "antd";
import {useEffect, useState} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {normalize_path, requestFileList} from "./form-saga";
import FileBrowserModal from "./FileBrowserModal";
import Flex from "/src/common/Flex";


const FileInput = ({path_only, namespace="fileinput", ...props}) => {
    const dispatch = useAppDispatch();
    const {file_list} = useAppSelector(state => state.form);
    const [options, set_options] = useState(null);
    const [loading, set_loading] = useState(false);
    const [browser_trigger, set_browser_trigger] = useState(0);

    const handle_search = (value) => {
        value = value || "";
        const split_path = value.split("/");
        let parent_path, query;
        if (split_path.length === 0) {
            parent_path = "";
            query = "";
        } else if (split_path.length === 1) {
            parent_path = "";
            query = split_path[0];
        } else {
            parent_path = split_path.slice(0, split_path.length - 1).join("/");
            query = split_path[split_path.length - 1]
        }
        parent_path = normalize_path(parent_path);
        query = query.toLowerCase()

        const listing = file_list[namespace];

        if (normalize_path(listing?.path) !== parent_path && !loading) {
            // console.log("REQ LISTING", {namespace, parent_path, listing_path: listing?.path});
            set_loading(true);
            dispatch(requestFileList({path: parent_path, namespace}));
        } else if (listing) {
            set_loading(false);
            let options = (
                listing.dirs
                .map(f => f.name)
                .filter(f => f.toLowerCase().indexOf(query) >= 0)
                .map(f => ({
                    value: normalize_path(parent_path.length ? `${parent_path}/${f}/` : `${parent_path}${f}/`)
                }))
            );
            if (!path_only) {
                options = options.concat(
                    listing.files
                    .map(f => f.name)
                    .filter(f => f.toLowerCase().indexOf(query) >= 0)
                    .map(f => ({
                        value: normalize_path(parent_path.length ? `${parent_path}/${f}` : `${parent_path}${f}`),
                        is_file: true,
                    }))
                );
            }
            set_options(options.map(o => ({
                value: o.value,
                label: o.is_file ? <i>{o.value}</i> : o.value,
                is_file: !!o.is_file,
            })));
        }
    }

    const handle_select = (val) => {
        const option = options.find(o => o.value === val);
        val = normalize_path(val);
        if (!option?.is_file) {
            if (!val.endsWith("/"))
                val = `${val}/`;
        }
        props.onChange(val);
    }

    useEffect(() => {
        handle_search(props.value);
    }, [props.value, file_list]);

    return (
        <div>
            <FileBrowserModal
                trigger={browser_trigger}
                initial_path={props.value}
                onOk={props.onChange}
                path_only={path_only}
            />
            <Flex>
                <Flex.Item grow className={"file-input-wrapper"}>
                    <AutoComplete
                        {...props}
                        options={options}
                        onSearch={handle_search}
                        onSelect={handle_select}
                    />
                </Flex.Item>
                <div><Button onClick={() => set_browser_trigger(Math.random())}>...</Button></div>
            </Flex>
        </div>
    );
};

export default FileInput;
