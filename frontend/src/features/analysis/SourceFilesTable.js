import {useEffect, useRef, useState} from "react";
import {Button, Col, Modal, Row, Select, Space, Progress, Table} from "antd";
import {LoadingOutlined} from "@ant-design/icons";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Json from "../../common/Json";
import {table_string_sorter} from "../../utils/table";
import "./AttributesTable.scss"
import {Link} from "react-router-dom";
import {APP_URLS} from "../../app/urls";


const SourceFilesTable = ({files, attributes, ...props}) => {

    const [table_data, set_table_data] = useState(null);

    useEffect(() => {
        const dataSource = [];
        const columns = [
            {
                dataIndex: "_path",
                title: "path",
                sorter: table_string_sorter("_path"),
                render: (text, record) => <Link
                    to={APP_URLS.FILES.IMAGE.replace("*", record._full_path)}
                >{text}</Link>
            },
            {
                dataIndex: "_status",
                title: <i>status</i>,
                sorter: table_string_sorter("_status"),
            },
            {
                dataIndex: "id",
                title: "id",
                sorter: table_string_sorter("id"),
                render: (text, record) => record.id ? record.id : "NONE!",
            }
        ];
        if (attributes?.length) {
            for (const attr of attributes) {
                if (attr !== "id" && attr !== "_status" && attr !== "_use_for") {
                    columns.push({
                        dataIndex: attr,
                        title: attr,
                        sorter: table_string_sorter(attr),
                    });
                }
            }
        }
        if (files?.length) {
            for (const file of files) {
                dataSource.push({
                    "_path": file.short_path || file.path,
                    "_full_path": file.path,
                    ...file.attributes,
                });
            }
        }

        set_table_data({dataSource, columns});

    }, [files, attributes]);

    const get_row_attributes = (record, index) => {
        return {className: record._status !== "ok" ? "incomplete-data" : undefined};
    };

    return (
        <div className={"source-files-table"} {...props}>
            <Table
                dataSource={table_data?.dataSource || null}
                columns={table_data?.columns || null}
                size={"small"}
                rowKey={record => record._path}
                scroll={{x: "50vw"}}
                onRow={get_row_attributes}
            />
        </div>
    );
};

export default SourceFilesTable;

