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


const STATUS_NAME_MAPPING = {
    "not_in_table": "not in attribute table"
};


const SeparationWidget = ({get_response, reduction_preview, update_plugin, ...props}) => {

    const [files, set_files] = useState();
    const [attributes, set_attributes] = useState();
    const [counts, set_counts] = useState();
    const [separation_config_visible, set_separation_config_visible] = useState(false);
    const [separation_values, set_separation_values] = useState(null);

    useEffect(() => {
        if (!reduction_preview?.files) {
            set_files(null);
            set_attributes(null);
            set_counts(null)
        } else {
            set_files({
                all: reduction_preview.files,
                ...reduction_preview.sets,
            });
            set_attributes(reduction_preview.attribute_names);

            const counts = reduction_preview.counts;
            const count_list = [
                {name: "files", value: <span><b>{counts.ok || 0}</b> / {counts.all}</span>}
            ];
            for (const key of Object.keys(reduction_preview.counts)) {
                if (key !== "ok" && key !== "all") {
                    count_list.push({
                        name: (STATUS_NAME_MAPPING[key] || key.replaceAll("_", " ")),
                        value: counts[key],
                    });
                }
            }
            set_counts(count_list);
        }
    }, [reduction_preview]);

    const start_separation_config = () => {
        set_separation_values(get_response.separation_values);
        set_separation_config_visible(true);
    };

    const submit_separation_config = () => {
        update_plugin({
            separation_values
        });
        set_separation_config_visible(false);
    };

    return (
        <div className={"separation-widget"} {...props}>

            <Section
                title={"all source files"}
                boxed
            >
                <Collapse>
                    <Collapse.Panel
                        key={"table"}
                        header={
                            <Flex marginX={".5rem"}>
                                {counts?.map(entry => (
                                    <div key={entry.name}>{entry.name}: {entry.value}</div>
                                ))}
                                <Flex.Grow/>
                                <div style={{color: "#999"}}>(click to show table)</div>
                            </Flex>
                        }
                    >
                        <SourceFilesTable
                            files={files?.all || null}
                            attributes={attributes}
                        />
                    </Collapse.Panel>
                </Collapse>
            </Section>

            <br/>
            <Section
                boxed
                title={<h3>split into <b>training</b> and <b>validation</b> set</h3>}
                edited={separation_config_visible}
                actions={
                    separation_config_visible
                        ? [
                            {
                                name: "Cancel",
                                action: () => {
                                    set_separation_config_visible(false);
                                }
                            },
                            {
                                name: "Save",
                                type: "primary",
                                action: submit_separation_config,
                            }
                        ] : [
                            {
                                icon: <IconEdit/>,
                                disabled: separation_config_visible || !get_response,
                                action: start_separation_config,
                            }
                        ]
                }
            >
                {separation_config_visible
                    ? (
                        <AutoForm
                            form={get_response?.separation_form}
                            values={get_response?.separation_values}
                            onChange={data => set_separation_values(data.values)}
                        />
                    ) : (
                        <AutoFormValues
                            form={get_response?.separation_form}
                            values={get_response?.separation_values}
                            onClick={() => set_separation_config_visible(true)}
                        />
                    )
                }
            </Section>

            <br/>
            <Section
                title={"training / validation files"}
                boxed
            >
                <Collapse>
                    {["training", "validation"].map(key => {
                        const num_files = files && files[key] ? files[key].length : 0;
                        const shape = num_files && reduction_preview?.output_size
                            ? `(shape: ${num_files} x ${reduction_preview.output_size})`
                            : "";
                        return (
                            <Collapse.Panel
                                key={key}
                                header={
                                    <Flex marginX={".5rem"}>
                                        <div>{key}: <b className={files && files[key] && !num_files ? "not-good" : null}>{num_files}</b></div>
                                        <div>{shape}</div>
                                        <Flex.Grow/>
                                        <div style={{color: "#999"}}>(click to show table)</div>
                                    </Flex>
                                }
                            >
                                <SourceFilesTable
                                    files={files && files[key] || null}
                                    attributes={attributes}
                                />
                            </Collapse.Panel>
                        )
                    })}
                </Collapse>
            </Section>
        </div>
    );
};

export default SeparationWidget;

