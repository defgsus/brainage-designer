import {useEffect, useRef, useState} from "react";
import {Select} from "antd";
import Plot from "react-plotly.js"
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Flex from "../../common/Flex";
import Values from "../../common/Values";



const AnalysisResultPlot = ({result_data, ...props}) => {

    const [plot_props, set_plot_props] = useState(null);
    const [sort_by, set_sort_by] = useState("real");
    const [plot_type, set_plot_type] = useState("line");

    useEffect(() => {
        if (!result_data?.predicted_values) {
            set_plot_props(null);
        } else {
            const x = [];
            const y_real = [];
            const y_predicted = [];
            const y_error = [];

            let subjects = Object.keys(result_data.predicted_values);

            if (sort_by === "predicted") {
                subjects = subjects.sort((a, b) => (
                    result_data.predicted_values[a] < result_data.predicted_values[b] ? -1 : 1
                ));
            } else if (sort_by === "error") {
                subjects = subjects.sort((a, b) => (
                    result_data.predicted_value_errors[a] < result_data.predicted_value_errors[b] ? -1 : 1
                ));
            } else if (sort_by === "real") {
                subjects = subjects.sort((a, b) => {
                    const x = result_data.predicted_values[a] - result_data.predicted_value_errors[a];
                    const y = result_data.predicted_values[b] - result_data.predicted_value_errors[b];
                    return x < y ? -1 : 1;
                });
            }

            for (const id of subjects) {
                x.push(x.length);
                y_real.push(result_data.predicted_values[id] - result_data.predicted_value_errors[id])
                y_predicted.push(result_data.predicted_values[id]);
                y_error.push(result_data.predicted_value_errors[id]);
            }

            const subject_labels = subjects.map(id => `subject id: ${id}`);

            set_plot_props({
                data: [
                    {
                        type: plot_type,
                        x,
                        y: y_real,
                        name: "real value",
                        text: subject_labels,
                    },
                    {
                        type: plot_type,
                        x,
                        y: y_predicted,
                        name: "predicted value",
                        text: subject_labels,
                    },
                    {
                        type: plot_type,
                        x,
                        y: y_error,
                        name: "prediction error",
                        text: subject_labels,
                    },
                ],
                layout: {
                    width: 1200,
                    height: 500,
                    autosize: true,
                    title: 'real vs. predicted values',
                    colorway: ["#7d7", "#4af", "#d77"],
                    margin: {
                        t: 40,
                        l: 40,
                        b: 20,
                        r: 40,
                    }
                }
            });
        }
    }, [result_data, sort_by, plot_type]);

    if (!plot_props)
        return null;

    return (
        <div className={"analysis-plot"} {...props}>

            <Plot {...plot_props}/>

            <Flex.Row marginX={".2rem"} align={"center"}>
                <div>sort by:</div>
                <Select
                    value={sort_by}
                    onChange={v => set_sort_by(v)}
                    style={{minWidth: "10rem"}}
                >
                    <Select.Option value={"unsorted"}>unsorted</Select.Option>
                    <Select.Option value={"real"}>real value</Select.Option>
                    <Select.Option value={"predicted"}>predicted value</Select.Option>
                    <Select.Option value={"error"}>error</Select.Option>
                </Select>

                <div>plot type:</div>
                <Select
                    value={plot_type}
                    onChange={v => set_plot_type(v)}
                    style={{minWidth: "10rem"}}
                >
                    <Select.Option value={"bar"}>bar</Select.Option>
                    <Select.Option value={"line"}>line</Select.Option>
                </Select>
            </Flex.Row>
        </div>
    );
};

export default AnalysisResultPlot;
