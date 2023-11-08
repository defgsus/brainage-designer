import {useEffect, useState} from "react";
import {Button, Col, Modal, Row, Select} from "antd";
import Modules from "./Modules";
import {produce} from "immer";
import Flex from "/src/common/Flex";
import AddModuleModal from "./AddModuleModal";


const ModulesForm = ({
        modules, process_data, available_modules, updateModules, module_group_order, module_group_limit,
        onModuleFormChange, onEditedModuleChange, extra_module_content,
        ...props
}) => {
    const [add_module_group, set_add_module_group] = useState(null);
    const [add_module_map, set_add_module_map] = useState(null);

    const handle_update_module = (mod) => {
        if (updateModules) {
            const index = modules.findIndex(m => m.uuid === mod.uuid);
            if (index >= 0) {
                updateModules(produce(modules || [], draft => {
                    draft[modules.findIndex(m => m.uuid === mod.uuid)] = mod;
                }));
            }
        }
    };

    const handle_add_click = (group_name) => {
        const module_map = {};
        for (const module of available_modules) {
            if (module.group[0] !== group_name)
                continue;
            const full_group_name = module.group.slice(1).join(" / ");
            if (!module_map[full_group_name])
                module_map[full_group_name] = [];
            module_map[full_group_name].push(module.name);
        }
        const sorted_map = {};
        for (const key of Object.keys(module_map).sort()) {
            sorted_map[key] = module_map[key];
            sorted_map[key].sort();
        }
        set_add_module_group(group_name);
        set_add_module_map(sorted_map);
    };

    const handle_add_module = (module_name) => {
        if (updateModules)
            updateModules([
                ...(modules || []),
                {name: module_name},
            ]);
        set_add_module_map(null);
    }

    const handle_remove_module = (mod) => {
        if (updateModules)
            updateModules(modules.filter(
                m => m.uuid !== mod.uuid
            ));
    }

    const handle_copy_module = (module) => {
        if (updateModules) {
            const new_module = {
                name: module.name,
                parameter_values: module.parameter_values,
            };
            updateModules([
                ...(modules || []),
                new_module,
            ]);
        }
    }

    // move source module before target module
    const handle_module_drop = (source, target) => {
        if (updateModules) {
            let new_modules = [...modules];
            const source_idx = new_modules.findIndex(m => m.uuid === source.uuid);
            new_modules.splice(source_idx, 1);
            const target_idx = new_modules.findIndex(m => m.uuid === target.uuid);
            if (target_idx === 0) {
                new_modules = [source, ...new_modules];
            } else {
                new_modules = [
                    ...new_modules.slice(0, target_idx),
                    source,
                    ...new_modules.slice(target_idx),
                ];
            }
            updateModules(new_modules);
        }
    };

    return (
        <div {...props}>
            <AddModuleModal
                base_group_name={add_module_group}
                add_module_map={add_module_map}
                available_modules={available_modules}
                onOk={handle_add_module}
                onCancel={() => set_add_module_map(null)}
            />

            <div className={"module-edit-form"}>
                <Modules
                    modules={modules}
                    module_group_order={module_group_order}
                    module_group_limit={module_group_limit}
                    process_data={process_data}
                    highlight_uuid={null}
                    extra_module_content={extra_module_content}
                    onAddClick={handle_add_click}
                    onModuleFormChange={onModuleFormChange}
                    onUpdateModule={handle_update_module}
                    onRemoveModule={handle_remove_module}
                    onCopy={handle_copy_module}
                    onEditedModuleChange={onEditedModuleChange}
                    onDrop={handle_module_drop}
                />
            </div>

        </div>
    )
};

export default ModulesForm;
