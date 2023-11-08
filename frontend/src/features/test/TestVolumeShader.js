import ImageVolumeViewer from "../graphics/ImageVolumeViewer";
import {useState} from "react";
import {Select} from "antd";

const image_paths = [
    "prog/data/datasets/ixi/IXI002-Guys-0828-T1.nii.gz",
    "/prog/data/TEST/ixi/IXI002-Guys-0828-T1.nii.gz",
];

const TestVolumeShader = (props) => {

    const [path, set_path] = useState(image_paths[0]);


    return (
        <div>
            <Select
                onChange={set_path}
                value={path}
            >
                {image_paths.map(path => (
                    <Select.Option key={path} value={path}>{path}</Select.Option>
                ))}
            </Select>
            <ImageVolumeViewer
                path={path}
                width={768}
                height={768}
            />
        </div>
    );
};

export default TestVolumeShader;

