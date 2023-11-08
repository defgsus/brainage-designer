import {Form, Input, InputNumber, Modal, Select, Switch} from "antd";
import {useEffect, useState} from "react";
import ReactMarkdown from "react-markdown";
import FileInput from "./FileInput";
import Json from "/src/common/Json";
import TextArea from "antd/es/input/TextArea";
import Flex from "/src/common/Flex";
import {IconHelp} from "/src/icons";
import "./AutoForm.scss"
import AutoFormValues from "./AutoFormValues";
import JsonInput from "./JsonInput";



export const get_form_values = (form, field_name) => {
    const values = {};
    form?.parameters?.forEach(item => {
        values[item.name] = item[field_name];
    });
    return values;
};

export const get_form_parameter = (form, field_name) => {
    if (!form)
        return null;
    for (const param of form.parameters) {
        if (param.name === field_name)
            return param;
    }
    return null;
};


export const is_parameter_visible = (param, form_values) => {
    if (!param.visible_js || !form_values)
        return true;

    let code = "";
    for (const key of Object.keys(form_values)) {
        code += `const ${key} = ${JSON.stringify(form_values[key])};\n`;
    }
    code += `${param.visible_js}`;

    return !!eval(code);
};


const are_values_equal = (values1, values2) => {
    for (const key of Object.keys(values1).concat(Object.keys(values2))) {
        if (values1[key] !== values2[key])
            return false;
    }
    return true;
}


const ParameterHelp = ({parameter, className, ...props}) => {
    className = className ? `${className} parameter-help` : "parameter-help";
    return (
        <div className={className} {...props}>
            <h3>Parameter {parameter.name} <span className={"parameter-type"}>
                ({parameter.type})
            </span></h3>
            <p>{parameter.description}</p>
            <ReactMarkdown>
                {parameter.help}
            </ReactMarkdown>
        </div>
    )
};

const AutoFormItem = ({item, hide_label=false, set_show_help, namespace, visible}) => {
    namespace = `${namespace}/${item.name}`;

    let input;
    let value_prop_name = "value";
    let rules = [];
    if (item.required)
        rules.push({required: true, message: `A value for ${item.human_name || item.name} is required`});
    switch (item.type) {
        case "int":
        case "float":
            input = <InputNumber/>;
            break;
        case "string":
            input = <Input/>;
            break;
        case "text":
            input = <TextArea/>;
            break;
        case "bool":
            input = <Switch/>;
            value_prop_name = "checked";
            break;
        case "select":
            input = (
                <Select>
                    {item.options.map(opt => (
                        <Select.Option key={opt.value} value={opt.value}>{opt.name}</Select.Option>
                    ))}
                </Select>
            );
            break;
        case "filepath":
        case "filename":
            input = <FileInput path_only={item.type === "filepath"} namespace={namespace}/>;
            break;

        case "string_mapping":
            input = <JsonInput/>
            break;

        default:
            input = <Input/>;
    }
    return (
        <Form.Item
            name={item.name}
            className={(hide_label ? "" : "label-visible") + (visible ? "" : " hidden")}
            label={
                <div>
                    {hide_label ? null : <b>{item.human_name || item.name}</b>} {!item.help ? null : (
                    <IconHelp
                        onClick={() => set_show_help(item)}
                    />
                )}
                </div>
            }
            help={
                <ReactMarkdown>
                    {item.description}
                </ReactMarkdown>
            }
            rules={rules}
            valuePropName={value_prop_name}
        >
            {input}
        </Form.Item>
    );
};


const AutoForm = ({form, values, parameterName=null, passUseForm, onChange, ...props}) => {
    const [ant_form] = Form.useForm();
    const [show_help, set_show_help] = useState(null);
    const [single_param, set_single_param] = useState(null);
    const [param_visible_map, set_param_visible_map] = useState({});

    useEffect(() => {
        if (passUseForm)
            passUseForm(ant_form);
    }, [ant_form, passUseForm]);

    useEffect(() => {
        if (!form) {
            ant_form.resetFields();
        } else {
            ant_form.setFieldsValue({
                ...get_form_values(form, "default_value"),
                ...values,
            });
        }
        update_visible_map();
    }, [form, values]);

    useEffect(() => {
        if (!parameterName) {
            set_single_param(null);
        } else {
            set_single_param(
                form.parameters.find(item => item.name === parameterName) || null
            );
        }
    }, [form, parameterName]);

    const update_visible_map = (form_values=null) => {
        if (!form_values)
            form_values = ant_form.getFieldsValue(true);

        const visible_map = {};

        if (form?.parameters) {
            /*for (const item of form.parameters) {
                if (form_values[item.name] === undefined)
                    form_values[item.name] = item.default_value;
            }*/
            for (const item of form.parameters) {
                visible_map[item.name] = is_parameter_visible(item, form_values);
            }
        }
        set_param_visible_map(visible_map);
    }

    const handle_values_change = () => {
        const form_values = ant_form.getFieldsValue(true);
        update_visible_map(form_values);

        if (onChange) {
            const default_values = get_form_values(form, "default_value");
            onChange({
                values: form_values,
                is_default: are_values_equal(form_values, default_values),
            });
        }
    }

    return (
        <>
            {!show_help ? null : (
                <Modal
                    open={!!show_help}
                    onOk={() => set_show_help(null)}
                    onCancel={() => set_show_help(null)}
                >
                    <ParameterHelp parameter={show_help}/>
                </Modal>
            )}
            {!single_param
                ? (
                    <Form
                        className={"autoform"}
                        form={ant_form}
                        layout={"vertical"}
                        requiredMark={"optional"}
                        {...props}
                        onValuesChange={handle_values_change}
                    >
                        {!form?.parameters ? null : (
                            form.parameters.map((item, idx) => (
                                <AutoFormItem
                                    key={item.name}
                                    namespace={`${form.id}-${idx}`}
                                    item={item}
                                    set_show_help={set_show_help}
                                    visible={!!param_visible_map[item.name]}
                                />
                            )
                        ))}
                    </Form>
                )
                : (
                    <AutoFormValues
                        form={form}
                        values={values}
                        override={{
                            [parameterName]: {
                                name: parameterName,
                                value: (
                                    <Form
                                        className={"autoform"}
                                        form={ant_form}
                                        layout={"horizontal"}
                                        requiredMark={false}
                                        colon={false}
                                        {...props}
                                        onValuesChange={handle_values_change}
                                    >
                                        <AutoFormItem
                                            item={single_param}
                                            set_show_help={set_show_help}
                                            hide_label={true}
                                        />
                                    </Form>
                                )
                            }
                        }}
                    />
                )
            }
        </>
    );
}

export default AutoForm;
