import Head from "./Head";
import {Collapse} from "antd";


const Section = ({
     title, sub_title, children, actions, loading, help, onRefresh, boxed, edited, collapsible,
     ...props
}) => {

    const head = (
        <Head
            title={title}
            sub_title={sub_title}
            actions={actions}
            loading={loading}
            onRefresh={onRefresh}
            help={help}
            small
            {...props}
        />
    );

    const content = (
        <div className={"section-content"}>
            {children}
        </div>
    )

    return (
        <div className={"bad-section" + (boxed ? " boxed" : "") + (edited ? " edited" : "")}>
            {
                collapsible ? (
                    <Collapse
                        defaultActiveKey={"content"}
                    >
                        <Collapse.Panel
                            key={"content"}
                            header={head}
                            className={"bad-section-collapse"}
                        >
                            {content}
                        </Collapse.Panel>
                    </Collapse>
                ) : <>
                    {head} {content}
                </>
            }
        </div>
    )
};

export default Section;
