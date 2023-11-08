import {useEffect, useState} from "react";
import {useMatch} from "react-router";
import {FileImageOutlined} from "@ant-design/icons";
import {APP_URLS} from "/src/app/urls";
import ImageViewer from "/src/features/form/ImageViewer";
import Flex from "/src/common/Flex";
import PageFrame from "/src/common/PageFrame";
import {history} from "/src/store";
import {normalize_path} from "/src/features/form/form-saga";


const ImagePage = () => {
    const match = useMatch(APP_URLS.FILES.IMAGE);
    const [filename, set_filename] = useState(null);

    useEffect(() => {
        const fn = match.params["*"];
        set_filename(fn.startsWith("/") ? fn : `/${fn}`);
    }, [match]);

    return (
        <PageFrame
            title={
                <Flex.Row marginX={".3rem"} align={"center"}>
                    <div><FileImageOutlined/></div>
                    <div><h3>{filename}</h3></div>
                </Flex.Row>
            }
            actions={[
                {
                    name: "show volume",
                    type: "primary",
                    action: () => {
                        history.push(
                            APP_URLS.FILES.VOLUME
                            .replace("*", normalize_path(match.params["*"]).slice(1))
                        );
                    }}
            ]}
        >
            <ImageViewer
                filename={filename}
            />
        </PageFrame>
    );
}

export default ImagePage;
