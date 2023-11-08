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
import {useEffect, useRef, useState, useContext} from "react";
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import {WebSocketContext} from "../ws/WebSocketProvider";
import {
    requestAnalysis, requestAnalysisAverageResult, requestAnalysisCopy, requestAnalysisDelete, requestAnalysisResult,
    requestAnalysisRun, requestAnalysisSourcePreview, requestAnalysisStop,
    requestAnalysisUpdate
} from "./analysis-saga";
import {useMatch} from "react-router";
import {API_URLS, APP_URLS} from "/src/app/urls";
import PageFrame from "/src/common/PageFrame";
import TableView from "/src/features/tableview/TableView";
import Values from "/src/common/Values";
import ModulesForm from "/src/features/module/ModulesForm";
import Section from "/src/common/Section";
import Json from "/src/common/Json";
import Flex from "../../common/Flex";
import {join_paths} from "../files/fileutil";
import AnalysisConfig from "./AnalysisConfig";
import PreprocessingProcessView from "../preprocessing/PreprocessingProcessView";
import SourcePreview from "./SourcePreview";
import SourceFilesTable from "./SourceFilesTable";
import {setWebsocketUuid} from "../ws/websocket-slice";
import SeparationWidget from "./SeparationWidget";
import "./AnalysisView.scss"
import ReductionForm from "./ReductionForm";
import AnalysisForm from "./AnalysisForm";
import {setAnalysisResultResponse} from "./analysis-slice";
import AnalysisResult from "./AnalysisResult";


const AnalysisView = (props) => {
    const dispatch = useAppDispatch();

    const {get_response, get_result_response,
        get_average_result_response, source_preview_response} = useAppSelector(state => state.analysis);
    const {websocket_data} = useAppSelector(state => state.websocket);
    const {ws} = useContext(WebSocketContext);

    const updateTimeoutRef = useRef();
    const sourcePreviewTimeoutRef = useRef();
    const [loading, set_loading] = useState(false);
    const [source_preview_loading, set_source_preview_loading] = useState(false);
    const [source_preview_module_uuid, set_source_preview_module_uuid] = useState(null);
    const [config_visible, set_config_visible] = useState(false);
    const [process_status, set_process_status] = useState({status: "stopped", running: false});
    const [source_object_count, set_source_object_count] = useState(null);
    const [object_progress, set_object_progress] = useState(null);
    const [refresh_trigger, set_refresh_trigger] = useState(0);
    const [reduction_preview, set_reduction_preview] = useState(null);
    const [average_analysis_result, set_average_analysis_result] = useState(null);

    const match = useMatch(APP_URLS.ANALYSIS.VIEW);
    const uuid = match.params.ap_id;

    useEffect(() => {
        dispatch(setWebsocketUuid({plugin: "analysis", uuid}));
    }, [uuid]);

    useEffect(() => {
        if (get_response?.uuid !== uuid) {
            refresh();
        } else {
            set_loading(false);
            refresh_reduction_preview();

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
                set_average_analysis_result(null);
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

                let average_analysis_result = null;
                for (const event of get_response.latest_process_data.events) {
                    if (event.type === "analysis_result") {
                        average_analysis_result = event.data.average;
                        break;
                    }
                }
                set_average_analysis_result(average_analysis_result);
            }
        }
    }, [get_response, uuid]);

    useEffect(() => {
        if (!websocket_data?.analysis || !websocket_data.analysis[uuid]) {
            set_reduction_preview(null);
        } else {
            const data = websocket_data.analysis[uuid];
            set_reduction_preview(data.reduction_preview || null);
        }
    }, [websocket_data?.analysis, uuid]);

    const refresh_reduction_preview = () => {
        if (ws?.send_plugin_message)
            ws.send_plugin_message("analysis", uuid, "reduction_preview")
    }

    const refresh = () => {
        set_loading(true);
        dispatch(requestAnalysis({uuid}));
        dispatch(requestAnalysisAverageResult({uuid}));
        refresh_reduction_preview();
        set_refresh_trigger(Math.random());
    }

    const refresh_soon = (timeout=5000) => {
        if (updateTimeoutRef.current)
            clearTimeout(updateTimeoutRef.current);
        updateTimeoutRef.current = setTimeout(refresh, timeout);
    }

    const handle_run = () => {
        dispatch(requestAnalysisRun({uuid}));
        refresh();
    };

    const handle_stop = () => {
        dispatch(requestAnalysisStop({uuid}));
        refresh_soon(1000);
    };

    const handle_copy = () => {
        dispatch(requestAnalysisCopy({uuid}));
    };

    const handle_delete = () => {
        Modal.confirm({
            title: `Delete this pipeline?`,
            okText: "Delete",
            onOk: () => {
                dispatch(requestAnalysisDelete({uuid}));
            },
        });
    };

    const patch_plugin_data = (values) => {
        if (get_response) {
            set_loading(true);
            dispatch(requestAnalysisUpdate({
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
            dispatch(requestAnalysisUpdate(updated_plugin_data));
        }
    }

    // -------------- source files preview ----------------

    useEffect(() => {
        if (ws?.send_plugin_message && !reduction_preview)
            refresh_reduction_preview();
    }, [ws?.send_plugin_message, reduction_preview]);

    useEffect(() => {
        set_source_preview_loading(false);
    }, [source_preview_response]);

    const request_source_preview = (parameter_values) => {
        set_source_preview_loading(true);
        dispatch(requestAnalysisSourcePreview({uuid, parameter_values}));
    };

    const request_source_preview_soon = (parameter_values, timeout=1000) => {
        if (sourcePreviewTimeoutRef.current)
            clearTimeout(sourcePreviewTimeoutRef.current);
        sourcePreviewTimeoutRef.current = setTimeout(() => request_source_preview(parameter_values), timeout);
    };

    const handle_module_form_change = (module, form_values) => {
        if (module.name === "analysis_source") {
            request_source_preview_soon(form_values.values);
        }
    };

    const handle_edited_module_change = (module) => {
        if (module?.name === "analysis_source" && module.uuid !== source_preview_module_uuid) {
            set_source_preview_module_uuid(module.uuid);
            request_source_preview(module.parameter_values);
        } else {
            set_source_preview_module_uuid(null);
        }
    };

    const SourcePreviewWrapper = ({module_uuid, ant_form}) => {
        const [attribute_mapping, set_attribute_mapping] = useState(null);

        useEffect(() => {
            let module = null;
            if (get_response?.modules) {
                module = get_response.modules.find(m => m.uuid === module_uuid);
            }
            if (!module) {
                set_attribute_mapping(null);
            } else {
                set_attribute_mapping(
                    module.parameter_values.table_mapping || null
                );
            }
        }, [get_response?.modules, module_uuid]);

        return (
            <SourcePreview
                loading={source_preview_loading}
                response={source_preview_response}
                ant_form={ant_form}
                //attribute_mapping={attribute_mapping}
                set_attribute_mapping={new_mapping => {
                    set_attribute_mapping(new_mapping);
                    if (ant_form) {
                        ant_form.setFieldValue("table_mapping", new_mapping);
                        request_source_preview_soon(ant_form.getFieldsValue(true));
                    }
                }}
            />
        );
    };

    // ---- results -----

    const show_result = (uuid) => {
        if (get_result_response?.uuid !== uuid) {
            dispatch(requestAnalysisResult({uuid}));
        }
    };

    const hide_result = () => {
        dispatch(setAnalysisResultResponse(null));
    };

    return (
        <PageFrame
            title={"analysis pipeline" + (
                get_response?.name ? `: "${get_response.name}"` : ""
            )}
            //uuid={uuid}
            loading={loading}
            onRefresh={refresh}
        >
            <Modal
                open={!!get_result_response}
                onOk={hide_result}
                onCancel={hide_result}
                width={"90%"}
                title={get_response?.name}
            >
                <AnalysisResult result_data={get_result_response}/>
            </Modal>

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
                                    {<AnalysisConfig
                                        data={get_response}
                                        onSubmit={patch_plugin_data}
                                        onCancel={() => set_config_visible(false)}
                                    />}
                                </Flex.Item>
                            </Flex.Row>
                        ) : (
                            <Flex.Row justify={"space-between"} marginX={"1rem"}>
                                <Flex.Item>
                                    <Values
                                        values={get_response}
                                        //onClick={item => console.log(item)}
                                        show={["name", "description", "date_created"]}
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

            <Section title={"Source modules"} collapsible>
                <ModulesForm
                    modules={get_response?.modules || []}
                    //process_data={get_response?.latest_process_data || null}
                    available_modules={get_response?.available_modules || []}
                    updateModules={on_update_modules}
                    module_group_order={{"source": 1}} //, "process": 2, "reduction": 3, "prediction": 4}}
                    //module_group_limit={{"reduction": 1}}
                    onModuleFormChange={handle_module_form_change}
                    onEditedModuleChange={handle_edited_module_change}
                    extra_module_content={
                        !source_preview_module_uuid
                            ? null
                            : {
                                [source_preview_module_uuid]: (props) => (
                                    <SourcePreviewWrapper
                                        module_uuid={source_preview_module_uuid}
                                        {...props}
                                    />
                                )
                            }
                    }
                />
            </Section>

            <Section
                title={"Set separation"}
                sub_title={
                    reduction_preview?.preview_str
                        ? ` ${reduction_preview.preview_str}`
                        : null
                }
                collapsible
            >
                <SeparationWidget
                    get_response={get_response}
                    reduction_preview={reduction_preview}
                    update_plugin={patch_plugin_data}
                />
            </Section>

            <Section title={"Reduction"} collapsible>
                <Flex margin={"1rem"}>
                    <ModulesForm
                        modules={get_response?.modules || []}
                        available_modules={get_response?.available_modules || []}
                        updateModules={on_update_modules}
                        module_group_order={{"process": 2, "reduction": 3}} //, "prediction": 4}}
                        module_group_limit={{"reduction": 1}}
                        onModuleFormChange={handle_module_form_change}
                        onEditedModuleChange={handle_edited_module_change}
                    />
                    <Flex.Grow>
                        <ReductionForm
                            get_response={get_response}
                            update_plugin={patch_plugin_data}
                        />
                    </Flex.Grow>
                </Flex>
            </Section>

            <Section
                title={"Training & prediction"}
                collapsible
            >
                <Flex margin={"1rem"}>
                    <ModulesForm
                        modules={get_response?.modules || []}
                        available_modules={get_response?.available_modules || []}
                        updateModules={on_update_modules}
                        module_group_order={{"prediction": 4}}
                        module_group_limit={{"prediction": 1}}
                        onModuleFormChange={handle_module_form_change}
                        onEditedModuleChange={handle_edited_module_change}
                    />
                    <Flex.Grow>
                        <AnalysisForm
                            get_response={get_response}
                            update_plugin={patch_plugin_data}
                        />
                    </Flex.Grow>
                </Flex>
            </Section>

            <Section
                title={"Latest runs"}
                collapsible
                actions={[
                    {
                        name: "Run",
                        type: "primary",
                        icon: <PlayCircleFilled/>,
                        action: handle_run,
                        disabled: !process_status.can_start,
                    },
                ]}
            >
                <AnalysisResult
                    result_data={get_average_result_response?.average}
                />
                <TableView
                    namespace={"analysis-view"}
                    url={API_URLS.ANALYSIS.RESULTS.TABLE}
                    filters={{process_uuid: get_response?.latest_process_data?.uuid || null}}
                    loading={!get_response?.latest_process_data?.uuid}
                    refresh_trigger={refresh_trigger}
                    show_row_callback={row => show_result(row.uuid) }
                />
            </Section>

            {/*<Section title={"Latest run"}>
                {get_response?.latest_process_data
                    ? <PreprocessingProcessView process_data={get_response.latest_process_data}/>
                    : "None"
                }
            </Section>*/}

            {/*<Section title={"Latest objects"}>
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
            </Section>*/}

            <Json data={get_response}/>
            {/*<br/><Json data={reduction_preview}/>*/}
        </PageFrame>
    )
};

export default AnalysisView;
