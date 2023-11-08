import {useEffect, useRef, useState} from "react";
import {Button, Col, Modal, Row, Select, Space, Progress, Table, Input, Form} from "antd";
import {CheckOutlined, LoadingOutlined} from "@ant-design/icons";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Json from "../../common/Json";
import {table_string_sorter} from "../../utils/table";
import Flex from "../../common/Flex";
import {IconAdd, IconCheck, IconCross} from "../../icons";
import "./AttributesTable.scss"


const AttributesTable = ({headers, rows, attribute_mapping, set_attribute_mapping, small, ...props}) => {
    const editable = !!set_attribute_mapping;

    const [table_data, set_table_data] = useState(null);

    useEffect(() => {
        const dataSource = [];
        const columns = [];

        if (headers?.length) {
            for (const attr of headers) {
                columns.push({
                    dataIndex: attr,
                    title: attr,
                    sorter: table_string_sorter(attr),
                });
            }
        }

        if (rows?.length) {
            /*if (headers?.length) {
                const row = {};
                for (const header of headers) {
                    row[header] = "X";
                }
                dataSource.push(row);
            }*/

            for (const row of rows) {
                dataSource.push(row);
            }
        }

        const MappingColumnHeader = ({dataIndex}) => {
            const original_value = attribute_mapping ? (attribute_mapping[dataIndex] || null) : null;

            const [value, set_value] = useState(original_value);

            if (!editable) {
                if (attribute_mapping && attribute_mapping[dataIndex])
                    return `:${attribute_mapping[dataIndex]}`;
                else
                    return <i style={{color: "#bbb"}}>unmapped</i>;
            } else {
                return (
                    <div>
                        <Flex marginX={"1px"}>
                            <div>
                                <Input
                                    value={value}
                                    placeholder={"mapping"}
                                    title={"map column name to own name"}
                                    style={{minWidth: "5rem"}}
                                    size={"small"}
                                    onChange={e => set_value(e.target.value)}
                                    onPressEnter={e => {
                                        set_attribute_mapping({
                                            ...attribute_mapping,
                                            [dataIndex]: value || undefined,
                                        })
                                    }}
                                />
                            </div>
                            <div>
                                <Button
                                    disabled={original_value === value}
                                    size={"small"}
                                    icon={<IconCheck/>}
                                    onClick={() => set_attribute_mapping({
                                        ...attribute_mapping,
                                        [dataIndex]: value || undefined,
                                    })}
                                />
                            </div>
                            <div>
                                <Button
                                    disabled={original_value === value}
                                    size={"small"}
                                    icon={<IconCross/>}
                                    onClick={() => set_value(original_value)}
                                />
                            </div>
                        </Flex>
                    </div>
                );
            }
        };

        const components = {
            header: {
                wrapper: ({children, ...props}) => {
                    return (
                        <thead {...props}>
                            {children}
                            <tr>
                                {children[0].props.cells.map((c, i) => (
                                    <th
                                        key={i}
                                        className={
                                            attribute_mapping && attribute_mapping[c.column.dataIndex]
                                                ? "with-mapping" : null
                                        }
                                    >
                                        <MappingColumnHeader
                                            dataIndex={c.column.dataIndex}
                                        />
                                    </th>
                                ))}
                            </tr>
                        </thead>
                    );
                }
                /*cell: ({children, ...props}) => {
                    console.log(props);
                    return <th {...props}>{children}</th>;
                },*/
            }
        };

        set_table_data({dataSource, columns, components});

    }, [rows, headers, attribute_mapping]);

    return (
        <>
            <div className={"attributes-table" + (small ? " small" : "")} {...props}>
                <Table
                    dataSource={table_data?.dataSource || null}
                    columns={table_data?.columns || null}
                    size={"small"}
                    rowKey={(record, index) => index}
                    components={table_data?.components || null}
                    scroll={{x: "50vw"}}
                />
            </div>
        </>
    );
};

export default AttributesTable;

