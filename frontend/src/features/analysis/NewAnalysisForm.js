import {Button, Form, Input} from "antd";


const NewAnalysisForm = ({form, ...props}) => {
    return (
        <div>
            <Form
                layout={"vertical"}
                requiredMark={"optional"}
                form={form}
                className={"create-analysis-form"}
            >
                <Form.Item
                    name={"name"}
                    label={"name"}
                    rules={[
                        {required: true, message: "need to have a name"},
                    ]}
                >
                    <Input/>
                </Form.Item>

                <Form.Item
                    name={"description"}
                    label={"description"}
                >
                    <Input.TextArea/>
                </Form.Item>
            </Form>
        </div>

    )
};

export default NewAnalysisForm;
