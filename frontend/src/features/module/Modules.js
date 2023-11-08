import {useEffect, useState} from "react";
import {Button, Modal} from "antd";
import {LoadingOutlined} from "@ant-design/icons";
import {useDrag, useDrop} from "react-dnd";
import Module from "./Module";
import "./Modules.scss"
import Flex from "../../common/Flex";
import {IconAdd} from "../../icons";
import ReactMarkdown from "react-markdown";

const MODULE_GROUP_ORDER = {
    "source": 1,
    "filter": 2,
    "process": 3,
};

const Modules = (
    {modules, process_data, onUpdateModule, onRemoveModule, onAddClick, onDrop, onCopy, highlight_uuid,
        module_group_order, module_group_limit,
        onModuleFormChange, onEditedModuleChange, extra_module_content,
     ...props}
) => {
    module_group_order = module_group_order || MODULE_GROUP_ORDER;

    const [module_groups, set_module_groups] = useState([]);
    const [drop_target, set_drop_target] = useState(null);
    const [help_module, set_help_module] = useState(null);
    const [edited_module, set_edited_module_impl_] = useState(null);

    const set_edited_module = (edited_module) => {
        set_edited_module_impl_(edited_module);
        if (onEditedModuleChange)
            onEditedModuleChange(edited_module);
    };

    useEffect(() => {
        const module_by_group = {};
        Object.keys(module_group_order).forEach(key => module_by_group[key] = []);

        for (const module of (modules || [])) {
            const group = module.group[0];
            if (!module_by_group[group])
                continue;
            module_by_group[group].push(module);
        }
        const sorted_groups = Object.keys(module_by_group).sort(
            (a, b) => (
                (module_group_order[a] || 100) < (module_group_order[b] || 100) ? -1 : 1
            )
        )
        set_module_groups(sorted_groups.map(g => ({
            name: g,
            modules: module_by_group[g],
        })));
    }, [modules, module_group_order])

    return (<>
        {!help_module ? null : (
            <Modal
                open={help_module}
                onOk={() => set_help_module(null)}
                onCancel={() => set_help_module(null)}
            >
                <h3>{help_module.name}</h3>
                <ReactMarkdown>
                    {help_module.help || "*no help available*"}
                </ReactMarkdown>
            </Modal>
        )}
        <div className={"modules"} {...props}>
            <Flex.Row margin={".5rem"} wrap>
                {module_groups.map(group => {
                    const can_add_module =
                        !module_group_limit || module_group_limit[group.name] === undefined
                        || group.modules.length < module_group_limit[group.name];
                    return (
                        <div key={group.name} className={"module-group"}>
                            <Flex.Row className={"module-group-head"} align={"center"} marginX={".2rem"}>
                                <Flex.Item>
                                    <IconAdd
                                        title={can_add_module
                                            ? `add ${group.name} module`
                                            : `limit of ${module_group_limit[group.name]} reached`
                                        }
                                        onClick={() => onAddClick(group.name)}
                                        disabled={!can_add_module}
                                    />
                                </Flex.Item>
                                <Flex.Item className={"module-group-title"}>
                                    {group.name}
                                </Flex.Item>
                                <Flex.Item grow/>
                            </Flex.Row>
                            <Flex.Col margin={".5rem"}>
                                {group.modules.map(module => {
                                    return (
                                        <Flex.Item key={module.uuid}>
                                            <Module
                                                module={module}
                                                process_data={process_data}
                                                onUpdate={onUpdateModule}
                                                onRemove={onRemoveModule}
                                                highlight={highlight_uuid === module.uuid}
                                                dropping={drop_target?.uuid === module.uuid}
                                                onDrop={onDrop}
                                                setDropTarget={set_drop_target}
                                                onHelp={() => set_help_module(module)}
                                                onCopy={onCopy ? () => onCopy(module) : null}
                                                allowEdit={!edited_module || edited_module === module}
                                                onEdit={editing => set_edited_module(editing ? module : null)}
                                                onModuleFormChange={onModuleFormChange}
                                                extra_content={(extra_module_content && extra_module_content[module.uuid]) || null}
                                            />
                                        </Flex.Item>
                                    )
                                })}
                            </Flex.Col>
                        </div>
                    )
                })}
            </Flex.Row>
        </div>
    </>)
};

export default Modules;
