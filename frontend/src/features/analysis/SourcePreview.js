import {useEffect, useRef, useState} from "react";
import {Button, Col, Modal, Row, Select, Space, Progress} from "antd";
import {LoadingOutlined} from "@ant-design/icons";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Json from "../../common/Json";
import SourceFilesTable from "./SourceFilesTable";
import Flex from "../../common/Flex";
import Error from "../../common/Error";
import AttributesTable from "./AttributesTable";

const SourcePreview = ({loading, response, ant_form, set_attribute_mapping, ...props}) => {
    return (
        <div className={"analysis-source-preview"} {...props}>
            <Flex.Row>
                <Flex.Grow/>
                <div>{loading ? <div><LoadingOutlined/></div> : null}</div>
            </Flex.Row>

            {!response?.error ? null : (
                <Error>{response.error}</Error>
            )}

            {!response?.files ? null : (
                <div>
                    <h3>source files: {response.files.length} {
                        response.files.length >= response.limit
                            ? <span>(previewing only {response.limit})</span>
                            : null
                    }</h3>
                    <SourceFilesTable
                        files={response.files}
                        attributes={response.attributes}
                    />
                </div>
            )}

            {!response?.table ? null : (
                <div>
                    {response.table.error
                        ? <Error>{response.table.error}</Error>
                        : <div>
                            <h3>attribute table: {response.table.rows?.length}</h3>
                            <AttributesTable
                                rows={response.table.rows}
                                headers={response.table.headers}
                                attribute_mapping={ant_form?.getFieldValue("table_mapping")}
                                set_attribute_mapping={set_attribute_mapping}
                                small={true}
                            />
                        </div>
                    }
                </div>
            )}
        </div>
    );
};

export default SourcePreview;
