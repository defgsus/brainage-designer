import AutoForm from "../form/AutoForm";
import {useState} from "react";
import AutoFormWithButtons from "/src/features/form/AutoFormWithButtons";


const AnalysisConfig = ({data, onSubmit, onCancel, ...props}) => {

    return (
        <div className={"analysis-config-form"} {...props}>
            {!data?.config_form ? null : (
                <AutoFormWithButtons
                    form={data.config_form}
                    values={data}
                    onSubmit={onSubmit}
                    onCancel={onCancel}
                />
            )}
        </div>
    )
};

export default AnalysisConfig;
