import {Modal} from "antd";
import {useState} from "react";
import "./AddModuleModal.scss"
import ReactMarkdown from "react-markdown";


const AddModuleModal = ({base_group_name, add_module_map, available_modules, onOk, onCancel, ...props}) => {

    const [selected_module, set_selected_module] = useState();

    return (
        <Modal
            title={`Add ${base_group_name} module`}
            open={!!add_module_map}
            onCancel={onCancel}
            onOk={() => onOk(selected_module)}
            okButtonProps={{disabled: !selected_module}}
            {...props}
        >
            <div className={"module-select"}>
                {Object.keys(add_module_map || {}).map(group_name => (
                    <div key={group_name}>
                        <div className={"group-name"}>{group_name}</div>
                        <div className={"group-modules"}>
                            {add_module_map[group_name].map(module_name => {
                                const is_selected = module_name === selected_module;
                                const module = available_modules.find(m => m.name === module_name);
                                return (
                                    <div className={"module"} key={module_name}>
                                        <div
                                            className={"module-name" + (is_selected ? " selected" : "")}
                                            onClick={() => set_selected_module(
                                                is_selected ? null : module_name
                                            )}
                                        >
                                            {module_name}
                                        </div>
                                        {!is_selected ? null : (
                                            <div className={"module-description"}>
                                                <ReactMarkdown>
                                                    {module?.help || "*no help available*"}
                                                </ReactMarkdown>
                                            </div>
                                        )}
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                ))}
            </div>
        </Modal>
    )
};

export default AddModuleModal;
