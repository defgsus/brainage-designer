import {useEffect, useRef, useState} from "react";
import {produce} from "immer";
import {Row, Col, Button, Form, Modal, Badge} from "antd";
import {IconCopy, IconDelete, IconEdit, IconHelp} from "/src/icons";
import AutoForm from "/src/features/form/AutoForm";
import AutoFormValues from "/src/features/form/AutoFormValues";
import Flex from "/src/common/Flex";
import "./Modules.scss"
import {useDrag, useDrop} from "react-dnd";
import {FileFilled, FileImageOutlined, FileOutlined} from "@ant-design/icons";
import {Link} from "react-router-dom";
import {APP_URLS} from "../../app/urls";
import {normalize_path} from "../form/form-saga";
import ModuleObjects from "./ModuleObjects";


const Module = ({
        module, process_data, onRemove, onUpdate, onHelp, onCopy, setDropTarget,
        onDrop, dropping, className, highlight, onEdit, allowEdit,
        onModuleFormChange, extra_content,
        ...props
}) => {
    const dragRef = useRef();
    const [edited_module, set_edited_module] = useState(null);
    const [edited_parameter, set_edited_parameter] = useState(null);
    const [ant_form, set_ant_form] = useState(null);
    const [object_count, set_object_count] = useState(0);
    const [files_visible, set_files_visible] = useState(false);

    useEffect(() => {
        let object_count = 0;
        if (process_data?.object_count) {
            if (process_data.object_count.source[module.uuid])
                object_count = process_data.object_count.source[module.uuid];
            if (process_data.object_count.target[module.uuid])
                object_count = process_data.object_count.target[module.uuid];
        }
        set_object_count(object_count);
    }, [module, process_data]);

    const can_drop_item = (item) => (
        module.uuid !== item.uuid && module.group[0] === item.group[0]
    );
    const [{ handlerId }, drop] = useDrop({
        accept: "module",
        collect(monitor) {
            return {
                handlerId: monitor.getHandlerId(),
            }
        },
        hover: (item, monitor) => {
            const can_drop = dragRef.current && can_drop_item(item);
            setDropTarget(can_drop ? module : null);
        },
        canDrop: can_drop_item,
        drop: (item, monitor) => {
            setDropTarget(null);
            onDrop(item, module);
        }
    });
    const [{ isDragging }, drag] = useDrag({
        type: "module",
        item: () => {
            return module
        },
        collect: (monitor) => ({
            isDragging: monitor.isDragging(),
        }),
    })

    const handle_edit = () => {
        if (allowEdit) {
            set_edited_module(module);
            set_edited_parameter(null);
            if (onEdit)
                onEdit(true);
        }
    }

    const handle_edit_parameter = (name) => {
        if (allowEdit) {
            set_edited_module(module);
            set_edited_parameter(name);
            if (onEdit)
                onEdit(true);
        }
    }

    const handle_remove = () => {
        if (onRemove) {
            Modal.confirm({
                title: `Delete module ${module.name}?`,
                okText: "Delete",
                onOk: () => onRemove(module),
            });
        }
    }
    const handle_form_submit = (values) => {
        if (module) {
            const new_module = produce(module, draft => {
                draft.parameter_values = {
                    ...draft.parameter_values,
                    ...values,
                };
            });
            if (onUpdate)
                onUpdate(new_module);
        }
        set_edited_module(null);
        set_edited_parameter(null);
        if (onEdit)
            onEdit(false);

    };

    className = className ? `${className} module` : "module";
    if (highlight)
        className = `${className} highlight`;

    if (isDragging)
        className = `${className} dragging`;

    if (dropping)
        className = `${className} dropping`;

    drag(drop(dragRef));

    const module_content = (
        edited_module
            ? (<>
                <AutoForm
                    form={module?.form}
                    values={module?.parameter_values}
                    parameterName={edited_parameter}
                    passUseForm={set_ant_form}
                    onFinish={handle_form_submit}
                    onChange={values => {
                        if (onModuleFormChange)
                            onModuleFormChange(module, values);
                    }}
                />
            </>)
            : files_visible
                ? (
                    <ModuleObjects
                        module={module}
                        process_uuid={process_data?.uuid}
                    />
                ) : (
                    <AutoFormValues
                        form={module?.form}
                        values={module?.parameter_values}
                        onClick={item => handle_edit_parameter(item.name)}
                    />
                )
    );

    return (
        <div
            className={className}
            {...props}
            data-handler-id={handlerId}
        >
            <div className={"module-header"}
                 ref={dragRef}
            >
                <Flex marginX={".3rem"} align={"center"}>
                    <Flex.Item grow className={"module-name"}>{module.name}</Flex.Item>
                    {edited_module
                        ? (<>
                            {!module.help || !onHelp ? null : (
                                <Flex.Item>
                                    <IconHelp onClick={() => onHelp()}/>
                                </Flex.Item>
                            )}
                            <Flex.Item>
                                <Button
                                    onClick={() => {
                                        set_edited_module(null);
                                        if (onEdit)
                                            onEdit(false);
                                    }}
                                >
                                    Cancel
                                </Button>
                            </Flex.Item>
                            <Flex.Item>
                                <Button
                                    type={"primary"}
                                    onClick={() => ant_form.submit()}
                                    disabled={!ant_form}
                                >
                                    Save
                                </Button>
                            </Flex.Item>
                        </>) : (<>
                            {!object_count ? null : (
                                <Flex.Item>
                                    <Badge
                                        count={object_count}
                                        size={"small"}
                                        overflowCount={99999}
                                        offset={[-6, -8]}
                                        color={"#0a0"}
                                    >
                                        {files_visible
                                            ? <FileFilled
                                                title={"hide processed files"}
                                                onClick={() => set_files_visible(!files_visible)}
                                            />
                                            : <FileOutlined
                                                title={"list processed files"}
                                                onClick={() => set_files_visible(!files_visible)}
                                            />
                                        }
                                    </Badge>
                                </Flex.Item>
                            )}
                            {!onCopy ? null : (
                                <Flex.Item>
                                    <IconCopy onClick={() => onCopy()}/>
                                </Flex.Item>
                            )}
                            {!module.help || !onHelp ? null : (
                                <Flex.Item>
                                    <IconHelp onClick={() => onHelp()}/>
                                </Flex.Item>
                            )}
                            {(files_visible || !allowEdit) ? null : (
                                <Flex.Item>
                                    {!onUpdate ? null : <IconEdit onClick={handle_edit}/>}
                                </Flex.Item>
                            )}
                            <Flex.Item>
                                {(!onRemove || !allowEdit) ? null : <IconDelete onClick={handle_remove}/>}
                            </Flex.Item>
                        </>)
                    }
                </Flex>
            </div>

            <div className={"module-content"}>
                {!extra_content
                    ? module_content
                    : (
                        <Flex.Row wrap={true}>
                            <div>
                                {module_content}
                            </div>
                            <div className={"module-content-divider"}/>
                            <div>
                                {typeof extra_content === "function"
                                    ? extra_content({ant_form})
                                    : extra_content
                                }
                            </div>
                        </Flex.Row>
                    )
                }
            </div>
        </div>
    )
};

export default Module;
