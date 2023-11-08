import {Button} from "antd";
import {CheckOutlined} from "@ant-design/icons";
import {useEffect, useState} from "react";
import AutoForm from "./AutoForm";
import Flex from "/src/common/Flex";


const AutoFormWithButtons = ({form, values, passUseForm, onChange, onSubmit, onCancel, ...props}) => {

    const [ant_form, set_ant_form] = useState();

    const pass_use_form = (f) => {
        set_ant_form(f);
        if (passUseForm)
            passUseForm(f);
    }
    return (
        <div>
            <AutoForm
                form={form}
                values={values}
                passUseForm={pass_use_form}
                onChange={onChange}
                {...props}
            />
            <Flex.Row margin={".5rem"}>
                <Flex.Item grow/>
                <Flex.Item>
                    <Button
                        disabled={!onCancel}
                        onClick={() => onCancel()}
                    >
                        Cancel
                    </Button>
                </Flex.Item>
                <Flex.Item margin={".5rem"}>
                    <Button
                        type={"primary"}
                        onClick={() => onSubmit(ant_form.getFieldsValue(true))}
                        disabled={!(onSubmit && ant_form)}
                        icon={<CheckOutlined/>}
                    >
                        Save
                    </Button>
                </Flex.Item>
            </Flex.Row>
        </div>
    )
}

export default AutoFormWithButtons;
