import {useAppDispatch, useAppSelector} from "../../app/hooks";
import {useEffect, useState} from "react";
import Json from "../../common/Json";
import {requestModuleObjects} from "../process/process-saga";
import {Pagination} from "antd";
import {get_file_type, get_file_type_icon} from "../files/fileutil";
import {APP_URLS} from "../../app/urls";
import {normalize_path} from "../form/form-saga";
import {Link} from "react-router-dom";


const ModuleObjects = ({module, process_uuid, page_size, props}) => {
    page_size = page_size || 20;
    const dispatch = useAppDispatch();
    const {module_objects} = useAppSelector(state => state.process);

    const [objects, set_objects] = useState(null);
    const [pages, set_pages] = useState(0);
    const [page, set_page] = useState(0);
    const [objects_page, set_objects_page] = useState([]);

    useEffect(() => {
        dispatch(requestModuleObjects({
            module_uuid: module.uuid,
            process_uuid,
            source: module.group[0] === "source" ? "source" : "target",
        }));
    }, [module, process_uuid]);

    useEffect(() => {
        const response = module_objects[module.uuid] || null;
        set_objects(response?.result || null);
    }, [module_objects])

    useEffect(() => {
        if (!objects?.length)
            set_objects_page([]);
        else {
            set_objects_page(
                objects
                .slice(page * page_size, (page + 1) * page_size)
                .map((filename, idx) => {
                    const type = get_file_type(filename);
                    const icon = get_file_type_icon(type);
                    const selectable = type === "image";
                    let url = null;
                    if (type === "image")
                        url = APP_URLS.FILES.IMAGE.replace("*", normalize_path(filename).slice(1));

                    const content = (
                        <div key={idx} className={"file-row" + (selectable ? " selectable" : "")}>
                            <div className={"file-icon"}>
                                {icon}
                            </div>
                            <div className={"file-name"}>
                                {filename}
                            </div>
                        </div>
                    );
                    if (!url)
                        return content;
                    return (
                        <Link to={url}>{content}</Link>
                    );
                })
            );
        }
    }, [objects, page, page_size]);

    return (
        <div className={"module-objects"} {...props}>
            {!objects?.length || objects.length <= page_size ? null : (
                <Pagination
                    pageSize={page_size}
                    current={page + 1}
                    total={objects.length}
                    onChange={(page, size) => set_page(page - 1)}
                    showSizeChanger={false}
                    size={"small"}
                />
            )}
            {objects_page}
        </div>
    );
};

export default ModuleObjects;

