import {useEffect, useRef, useState} from "react";
import {} from "antd";
import Plot from "react-plotly.js"
import {useAppDispatch, useAppSelector} from "/src/app/hooks";
import Flex from "../../common/Flex";
import Values from "../../common/Values";
import AnalysisResultPlot from "./AnalysisResultPlot";
import Json from "../../common/Json";



const AnalysisResult = ({result_data, ...props}) => {

    const [values, set_values] = useState(null);

    useEffect(() => {
        if (!result_data) {
            set_values(null);
        } else {
            const values = [];
            for (const key of Object.keys(result_data)) {
                const value = result_data[key];
                if (typeof value === "number") {
                    values.push({
                        name: key,
                        value: value,
                    });
                }
            }
            set_values(values);
        }
    }, [result_data]);

    return (
        <div className={"analysis-run"} {...props}>
            <Flex.Row>

                <Values values={values}/>

                <AnalysisResultPlot result_data={result_data}/>

            </Flex.Row>

        </div>
    );
};

export default AnalysisResult;
