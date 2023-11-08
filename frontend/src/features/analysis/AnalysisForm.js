import {useEffect, useRef, useState} from "react";
import {Button, Col, Modal, Row, Select, Space, Progress, Table, Collapse, Form} from "antd";
import {ControlOutlined, LoadingOutlined} from "@ant-design/icons";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Json from "../../common/Json";
import {table_string_sorter} from "../../utils/table";
import "./AttributesTable.scss"
import SourceFilesTable from "./SourceFilesTable";
import Flex from "../../common/Flex";
import AutoForm from "../form/AutoForm";
import AutoFormValues from "../form/AutoFormValues";
import Section from "../../common/Section";
import {IconEdit} from "../../icons";



const AnalysisForm = ({get_response, update_plugin, ...props}) => {

    const [config_visible, set_config_visible] = useState(false);
    const [values, set_values] = useState(null);

    const start_config = () => {
        set_values(get_response.analysis_values);
        set_config_visible(true);
    };

    const submit_config = () => {
        update_plugin({
            analysis_values: values
        });
        set_config_visible(false);
    };

    return (
        <div className={"analysis-form"} {...props}>

            <Section
                boxed
                title={"analysis configuration"}
                edited={config_visible}
                actions={
                    config_visible
                        ? [
                            {
                                name: "Cancel",
                                action: () => {
                                    set_config_visible(false);
                                }
                            },
                            {
                                name: "Save",
                                type: "primary",
                                action: submit_config,
                            }
                        ] : [
                            {
                                icon: <IconEdit/>,
                                disabled: config_visible || !get_response,
                                action: start_config,
                            }
                        ]
                }
            >
                {config_visible
                    ? (
                        <AutoForm
                            form={get_response?.analysis_form}
                            values={get_response?.analysis_values}
                            onChange={data => set_values(data.values)}
                        />
                    ) : (
                        <AutoFormValues
                            form={get_response?.analysis_form}
                            values={get_response?.analysis_values}
                            onClick={() => set_config_visible(true)}
                        />
                    )
                }
            </Section>

        </div>
    );
};

export default AnalysisForm;
