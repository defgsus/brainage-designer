import {Row, Col, Pagination, Table} from "antd";
import {useAppDispatch, useAppSelector} from "../../app/hooks";
import {useEffect, useState} from "react";
import {requestTable} from "./tableview-saga";
import Date from "/src/common/Date";
import {updateTableOptions} from "./tableview-slice";
import Uuid from "/src/common/Uuid";
import AutoTag from "/src/common/AutoTag";
import Text from "/src/common/Text";
import {CaretDownFilled, CaretDownOutlined, CaretUpFilled, CaretUpOutlined, ReloadOutlined} from "@ant-design/icons";
import Json from "/src/common/Json";
import Flex from "../../common/Flex";
import {IconAdd, IconReload, IconShow} from "../../icons";
import Float from "../../common/Float";
import "./TableView.scss"


const TableView = (
    {
        url,
        namespace,
        filters: fixed_filters,
        defaultPageSize,
        loading,
        refresh_trigger,
        show_row_callback,
        ...props
    }) => {
    const dispatch = useAppDispatch();

    const {tables_per_url} = useAppSelector(state => state.tables);
    const table = tables_per_url[`${namespace}${url}`] || null;

    const [columns, set_columns] = useState([]);
    const [components, set_components] = useState([]);
    const [page_size_options, set_page_size_options] = useState([10, 20, 50, 100, 200, 500]);
    const [sort_column, _set_sort_column] = useState(null);

    const refresh = () => {
        dispatch(requestTable({url, namespace}));
    };

    useEffect(() => {
        if (refresh_trigger)
            refresh();
    }, [refresh_trigger]);

    useEffect(() => {
        if (fixed_filters) {
            for (const key of Object.keys(fixed_filters)) {
                if (!table?.filters || table?.filters[key] !== fixed_filters[key]) {
                    dispatch(updateTableOptions({
                        url,
                        namespace,
                        filters: {
                            ...table?.filters,
                            ...fixed_filters,
                        }
                    }));
                    break;
                }
            }
        }
    }, [table, fixed_filters]);

    useEffect(() => {
        if (!table?.response || table?.needs_update) {
            if (!loading)
                refresh();
        } else {
            const backend_columns = table.response.columns.map(c => {
                let render = null;
                switch (c.type) {
                    case "date":
                    case "datetime":
                        render = (text) => <Date date={text}/>;
                        break;
                    case "uuid":
                        render = (text) => <Uuid uuid={text}/>;
                        break;
                    case "state":
                        render = (text) => <AutoTag tag={text}/>;
                        break;
                    case "text":
                        render = (text) => <Text text={text}/>;
                        break;
                    case "str":
                        break;
                    case "float":
                        render = (text, row) => <Float>{row[c.name]}</Float>;
                        break;
                    default:
                        render = (text, row) => <Json data={row[c.name]} />;
                }
                return {
                    dataIndex: c.name,
                    title: c.name,
                    render,
                    sortable: true,
                    //sorter: (a, b) => 1,
                    //showSorterTooltip: true,
                    //sortOrder: "descend",
                    //sortDirections: ["ascend", "descend"],
                };
            });

            const frontend_columns = [];

            if (show_row_callback) {
                frontend_columns.push({
                    dataIndex: null,
                    title: "show",
                    fixed: true,
                    render: (text, row) => (
                        <IconShow
                            onClick={e => { e.stopPropagation(); show_row_callback(row) }}
                        />
                    ),
                })
            }

            set_columns(frontend_columns.concat(backend_columns));

            _set_sort_column(table.response.options.sort || null);
        }
    }, [table, table?.response, url, loading]);

    useEffect(() => {
        if (defaultPageSize) {
            if (!page_size_options.includes(defaultPageSize)) {
                set_page_size_options(page_size_options.concat([defaultPageSize]).sort());
            }
        }
    }, [page_size_options, defaultPageSize]);

    const on_page_change = (page, size) => {
        dispatch(updateTableOptions({
            url,
            namespace,
            limit: size,
            offset: (page - 1) * size,
        }));
    }

    const set_sort_column = (sort_column) => {
        dispatch(updateTableOptions({
            url,
            namespace,
            sort: sort_column,
        }));
        _set_sort_column(sort_column);
    }

    const limit = table?.limit || defaultPageSize || 10;
    const offset = table?.offset || 0;
    //const has_filters = Object.keys(table?.response?.options.filters || {}).length > 0;

    const render_pagination = () => (
        <Flex align={"center"} marginX={".5rem"} className={"table-pagination"}>
            <Flex.Item>
                {
                    (table?.response?.total || 0) === (table?.response?.total_unfiltered || 0)
                        ? table?.response?.total || 0
                        : `${table?.response?.total || 0} of ${table?.response?.total_unfiltered || 0}`
                }
            </Flex.Item>
            <Flex.Grow/>
            <Flex.Item>
                <Pagination
                    pageSize={limit}
                    pageSizeOptions={page_size_options}
                    total={table?.response?.total}
                    current={Math.floor(offset / limit) + 1}
                    onChange={on_page_change}
                    showSizeChanger={true}
                />
            </Flex.Item>
            <Flex.Item>
                <IconReload onClick={refresh}/>
            </Flex.Item>
        </Flex>
    );

    return (
        <div className={"bad-table-view"}>
            {render_pagination()}
            <Table
                size={"small"}
                rowKey={row => row._id}
                {...props}
                dataSource={loading ? null : table?.response?.rows?.slice(0, limit)}
                columns={columns}
                loading={!columns?.length}
                pagination={false}
                scroll={{x: true}}
                components={{
                    header: {
                        wrapper: ({children, ...props}) => {
                            return (
                                <thead {...props}>
                                {/*children*/}
                                <tr>
                                    {children[0].props.flattenColumns.map((c, i) => {
                                        const is_sort_up = c.dataIndex === sort_column;
                                        const is_sort_down = `-${c.dataIndex}` === sort_column;

                                        return (
                                            <th
                                                key={i}
                                            >
                                                <Flex justify={"space-between"} marginX={"2px"}>

                                                    <div
                                                        className={"bad-title" + (c.sortable ? " clickable" : "")}
                                                        onClick={e => {
                                                            if (c.sortable) {
                                                                e.stopPropagation();
                                                                if (is_sort_up)
                                                                    set_sort_column(`-${c.dataIndex}`);
                                                                else if (is_sort_down)
                                                                    set_sort_column(null);
                                                                else
                                                                    set_sort_column(c.dataIndex);
                                                            }
                                                        }}
                                                    >
                                                        {c.title}
                                                    </div>

                                                    {!c.sortable ? null : (
                                                        <div className={"bad-sorter"}>
                                                            <Flex.Col>
                                                                <CaretUpOutlined
                                                                    className={
                                                                        is_sort_up
                                                                            ? "clickable selected"
                                                                            : "clickable"
                                                                    }
                                                                    onClick={e => {
                                                                        e.stopPropagation();
                                                                        set_sort_column(
                                                                            is_sort_up ? null : c.dataIndex
                                                                        );
                                                                    }}
                                                                />
                                                                <CaretDownOutlined
                                                                    className={
                                                                        is_sort_down
                                                                            ? "clickable selected"
                                                                            : "clickable"
                                                                    }
                                                                    onClick={e => {
                                                                        e.stopPropagation();
                                                                        set_sort_column(
                                                                            is_sort_down ? null : `-${c.dataIndex}`
                                                                        );
                                                                    }}
                                                                />
                                                            </Flex.Col>
                                                        </div>
                                                    )}
                                                </Flex>
                                            </th>
                                        )
                                    })}
                                </tr>
                                </thead>
                            );
                        }
                    }
                }}
            />
            {render_pagination()}
        </div>
    )
};

export default TableView;
