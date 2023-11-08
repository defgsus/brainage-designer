import FileBrowser from "/src/features/form/FileBrowser";
import Section from "../../common/Section";
import {Switch} from "antd";
import {useState} from "react";


const TestBrowser = (props) => {
    const [directory_only, set_directory_only] = useState();

    return (
        <Section
            title={"browser test"}
            actions={[
                {component: (
                    <div>
                        directory only&nbsp;
                        <Switch checked={directory_only} onChange={v => set_directory_only(v)}/>
                    </div>
                )}
            ]}
        >
            <FileBrowser path={"/"} path_only={directory_only}/>
        </Section>
    );
}

export default TestBrowser;