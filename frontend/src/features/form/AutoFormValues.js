import {useEffect, useState} from "react";
import {Row, Col} from "antd";
import Values from "/src/common/Values";
import {get_form_parameter, is_parameter_visible} from "./AutoForm";
import {CheckOutlined, CloseOutlined} from "@ant-design/icons";


const AutoFormValues = ({form, values, override, onClick=null, ...props}) => {
    const [mapped_values, set_mapped_values] = useState([]);

    useEffect(() => {

        const transform_value = (value, name) => {
            const param = get_form_parameter(form, name);
            if (param) {
                switch (param.type) {
                    case "select":
                        for (const opt of param.options) {
                            if (opt.value === value) {
                                return opt.name;
                            }
                        }
                        break;
                    case "bool":
                        return value ? <CheckOutlined/> : <CloseOutlined/>;
                }
            }
            return value;
        }

        const tmp_values = [];
        if (form?.parameters) {
            form.parameters
                .filter(param => is_parameter_visible(param, values))
                .forEach(param => {
                if (override && override[param.name])
                    tmp_values.push(override[param.name]);
                else
                    tmp_values.push({
                        name: param.human_name || param.name,
                        value: transform_value(
                            !values || typeof values[param.name] === "undefined"
                                ? param.default_value
                                : values[param.name]
                            , param.name
                        ),
                    });
            });
        }
        set_mapped_values(tmp_values);
    }, [form, values, override]);

    return (
        <span className={"form-values"}>
            {!form?.parameters ? null : (
                <Values
                    values={mapped_values}
                    onClick={onClick}
                    {...props}
                />
            )}
        </span>
    )
};

export default AutoFormValues;
