import {useEffect, useState} from "react";
import {Col, Row, Select, Button} from "antd";
import Values from "/src/common/Values";
import Date from "/src/common/Date";
import "./PreprocessingProcessView.scss"
import Flex from "/src/common/Flex";
import Json from "../../common/Json";
import Progress from "/src/common/Progress";


const PreprocessingProcessView = ({process_data, ...props}) => {
    const [values, set_values] = useState([]);
    const [special_events, set_special_events] = useState([]);

    useEffect(() => {
        const new_values = {
            "status": process_data.status,
            "progress": <Progress data={process_data.progress}/>,
            "requested at": <Date date={process_data.date_created}/>,
            "last update at": <Date date={process_data.date_updated}/>,
        };
        const new_special_events = [];
        const graph_result_events = [];

        const render_output = (data) => {
            return (
                <div>
                    <pre>{data?.stdout}</pre>
                    <pre>{data?.stderr}</pre>
                </div>
            );
        };

        process_data?.events?.forEach(event => {
            switch (event.type) {
                case "finished":
                    new_values["finished at"] = <Date date={event.timestamp}/>;
                    if (event.data?.stdout?.length || event.data?.stderr?.length) {
                        new_special_events.push({
                            event,
                            title: "finished",
                            content: render_output(event.data),
                        });
                    }
                    break;
                case "failed":
                    new_values["failed at"] = <Date date={event.timestamp}/>;
                    new_special_events.push({
                        event,
                        title: "failed",
                        content: render_output(event.data),
                    });
                    break;
                case "exception":
                    new_special_events.push({
                        event,
                        title: "exception",
                        content: <pre>{event.data?.traceback}</pre>,
                    });
                    break;
                case "graph_result":
                    graph_result_events.push(event);
                    break;
            }
        });

        if (graph_result_events.length) {
            const sorted_events = graph_result_events.sort(
                (a, b) => a.data.sub_process < b.data.sub_process ? -1 : 1
            );
            for (const event of sorted_events) {
                for (const key of Object.keys(event.data.report)) {
                    const value = event.data.report[key];
                    new_values[key] = new_values[key]
                        ? `${new_values[key]} / ${value}`
                        : `${value}`;
                }
            }
        }

        set_values(new_values);
        set_special_events(new_special_events);
    }, [process_data]);

    return (
        <div className={"preprocessing-process"}>
            <Row>
                <Col xs={24} md={9}>
                    <Values
                        values={values}
                    />
                </Col>
            </Row>
            <div className={"special-events"}>
                {special_events.map((e, i) => (
                    <div key={i} className={"special-event"}>
                        <div className={"event-head"}><Date date={e.event.timestamp}/> {e.title}</div>
                        <div className={"event-content"}>{e.content}</div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default PreprocessingProcessView;
