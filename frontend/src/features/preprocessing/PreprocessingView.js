import {Button, Col, Modal, Row, Select, Space, Progress} from "antd";
import {
    ControlOutlined,
    CopyOutlined,
    DeleteOutlined,
    PlayCircleFilled,
    PlusOutlined,
    StopFilled
} from "@ant-design/icons";
import {produce} from "immer";
import {useEffect, useRef, useState} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {
    requestPreprocess, requestPreprocessCopy, requestPreprocessDelete,
    requestPreprocessRun, requestPreprocessStop,
    requestPreprocessUpdate
} from "./preprocessing-saga";
import {useMatch} from "react-router";
import {API_URLS, APP_URLS} from "/src/app/urls";
import PageFrame from "/src/common/PageFrame";
import TableView from "/src/features/tableview/TableView";
import Values from "/src/common/Values";
import ModulesForm from "/src/features/module/ModulesForm";
import Section from "/src/common/Section";
import Json from "/src/common/Json";
import PreprocessingProcessView from "./PreprocessingProcessView";
import Flex from "../../common/Flex";
import PreprocessingConfig from "./PreprocessingConfig";
import {join_paths} from "../files/fileutil";
import module_help from "bundle-text:./help/modules.md"


const PreprocessingView = (props) => {
    const dispatch = useAppDispatch();

    const {get_response} = useAppSelector(state => state.preprocessing);

    const updateTimeoutRef = useRef();
    const [loading, set_loading] = useState(false);
    const [config_visible, set_config_visible] = useState(false);
    const [module_file_map, set_module_file_map] = useState({});
    const [process_status, set_process_status] = useState({status: "stopped", running: false});
    const [source_object_count, set_source_object_count] = useState(null);
    const [object_progress, set_object_progress] = useState(null);
    const [refresh_trigger, set_refresh_trigger] = useState(0);

    const match = useMatch(APP_URLS.PREPROCESSING.VIEW);
    const uuid = match.params.pp_id;

    useEffect(() => {
        if (get_response?.uuid !== uuid) {
            refresh();
        } else {
            set_loading(false);

            if (!get_response.latest_process_data) {
                set_process_status({status: "stopped", running: false, can_start: true, can_stop: false});
            } else {
                const proc_status = get_response.latest_process_data.status;
                const new_process_status = {
                    status: proc_status,
                    running: proc_status === "requested" || proc_status === "started",
                    can_start: proc_status === "finished" || proc_status === "failed" || proc_status === "killed",
                    can_stop: proc_status === "requested" || proc_status === "started",
                };
                set_process_status(new_process_status);
                if (new_process_status.running) {
                    refresh_soon();
                }
            }
            if (!get_response?.latest_process_data) {
                set_source_object_count(null);
                set_object_progress(null);
            } else {
                const source_object_count = get_response.latest_process_data.source_object_count || null;
                const object_count = get_response.latest_process_data.object_count || null;
                set_source_object_count(source_object_count);
                if (!source_object_count || !object_count) {
                    set_object_progress(null);
                } else {
                    let all_count = 0;
                    let done_count = 0;
                    for (const module_uuid of Object.keys(source_object_count)) {
                        all_count += source_object_count[module_uuid];
                    }
                    for (const module_uuid of Object.keys(object_count.source)) {
                        done_count += object_count.source[module_uuid];
                    }
                    set_object_progress({
                        all: all_count,
                        done: done_count,
                        percent: Math.round(done_count / all_count * 1000.) / 10.,
                    });
                }
            }
        }
    }, [get_response, uuid]);

    const refresh = () => {
        set_loading(true);
        dispatch(requestPreprocess({uuid}));
        set_refresh_trigger(Math.random());
    }

    const refresh_soon = () => {
        if (updateTimeoutRef.current)
            clearTimeout(updateTimeoutRef.current);
        updateTimeoutRef.current = setTimeout(refresh, 2000);
    }

    const handle_run = () => {
        dispatch(requestPreprocessRun({uuid}));
        refresh();
    };

    const handle_stop = () => {
        dispatch(requestPreprocessStop({uuid}));
        refresh_soon();
    };

    const handle_copy = () => {
        dispatch(requestPreprocessCopy({uuid}));
    };

    const handle_delete = () => {
        Modal.confirm({
            title: `Delete this pipeline?`,
            okText: "Delete",
            onOk: () => {
                dispatch(requestPreprocessDelete({uuid}));
            },
        });
    };

    const handle_config_submit = (values) => {
        if (get_response) {
            set_loading(true);
            dispatch(requestPreprocessUpdate({
                uuid: get_response.uuid,
                ...values
            }));
            set_config_visible(false);
        }
    };

    const on_update_modules = (modules) => {
        if (get_response) {
            const updated_plugin_data = produce(get_response, draft => {
                draft.modules = modules;
            });
            set_loading(true);
            dispatch(requestPreprocessUpdate(updated_plugin_data));
        }
    }

    return (
        <PageFrame
            title={"preprocessing pipeline" + (
                get_response?.name ? `: "${get_response.name}"` : ""
            )}
            //uuid={uuid}
            loading={loading}
            onRefresh={refresh}
        >
            <Section
                title={"Overview"}
                actions={[
                    (!object_progress ? null : {
                        component: <div style={{width: "10rem"}}>
                            <Progress percent={object_progress.percent}/>
                        </div>
                    }),
                    (!process_status.can_start ? null : {
                        name: "Run pipeline",
                        type: process_status.can_start ? "primary" : null,
                        icon: <PlayCircleFilled/>,
                        action: handle_run,
                        disabled: !process_status.can_start,
                    }),
                    (!process_status.can_stop ? null : {
                        name: "Stop pipeline",
                        type: process_status.can_stop ? "primary" : null,
                        icon: <StopFilled/>,
                        action: handle_stop,
                        disabled: !process_status.can_stop,
                    }),
                    {
                        name: "Configure",
                        icon: <ControlOutlined/>,
                        disabled: config_visible,
                        action: () => set_config_visible(true),
                    },
                    {
                        name: "Copy",
                        icon: <CopyOutlined/>,
                        disabled: config_visible,
                        action: handle_copy,
                    },
                    {
                        name: "Delete",
                        icon: <DeleteOutlined/>,
                        danger: true,
                        disabled: config_visible || process_status.running,
                        action: handle_delete,
                    },
                ]}
            >
                <Flex.Item>
                    {config_visible
                        ? (
                            <Flex.Row justify={"center"}>
                                <Flex.Item>
                                    <PreprocessingConfig
                                        data={get_response}
                                        onSubmit={handle_config_submit}
                                        onCancel={() => set_config_visible(false)}
                                    />
                                </Flex.Item>
                            </Flex.Row>
                        ) : (
                            <Flex.Row justify={"space-between"}>
                                <Flex.Item>
                                    <Values
                                        values={get_response}
                                        //onClick={item => console.log(item)}
                                        //show={["name", "description", "date_created", "num_processes"]}
                                        hide={[
                                            "form", "modules", "available_modules", "config_form",
                                            "plugin_name", "uuid",
                                        ]}
                                    />
                                </Flex.Item>
                                <Flex.Item>
                                    {get_response?.latest_process_data
                                        ? <PreprocessingProcessView
                                            process_data={get_response.latest_process_data}
                                        />
                                        : null
                                    }
                                </Flex.Item>
                            </Flex.Row>
                        )
                    }
                </Flex.Item>
            </Section>

            <Section title={"Modules"} help={module_help}>
                <ModulesForm
                    modules={get_response?.modules || []}
                    process_data={get_response?.latest_process_data || null}
                    available_modules={get_response?.available_modules || []}
                    updateModules={on_update_modules}
                />
            </Section>

            {/*<Section title={"Latest run"}>
                {get_response?.latest_process_data
                    ? <PreprocessingProcessView process_data={get_response.latest_process_data}/>
                    : "None"
                }
            </Section>*/}

            <Section title={"Latest objects"}>
                <TableView
                    namespace={"preprocview"}
                    url={API_URLS.PROCESS.OBJECT.TABLE}
                    filters={{process_uuid: get_response?.latest_process_data?.uuid || null}}
                    loading={!get_response?.latest_process_data?.uuid}
                    refresh_trigger={refresh_trigger}
                />
            </Section>

            <Section title={"All runs"}>
                <TableView
                    namespace={"preprocview"}
                    url={API_URLS.PROCESS.TABLE}
                    filters={{source_uuid: uuid}}
                    loading={!uuid}
                    refresh_trigger={refresh_trigger}
                />
            </Section>

            <Json data={get_response}/>
        </PageFrame>
    )
};

export default PreprocessingView;