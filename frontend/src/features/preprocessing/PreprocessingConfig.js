import AutoForm from "../form/AutoForm";
import {useState} from "react";
import AutoFormWithButtons from "/src/features/form/AutoFormWithButtons";


const PreprocessingConfig = ({data, onSubmit, onCancel, ...props}) => {

    return (
        <div className={"preprocessing-config-form"} {...props}>
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

export default PreprocessingConfig;
