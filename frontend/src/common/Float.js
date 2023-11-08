

const Float = ({children, className, ...props}) => {

    className = className ? `${className} bad-float` : "bad-float";
    let title = null;

    if (typeof children === "number") {
        if (isNaN(children)) {
            children = "-";
            title = "Not A Number";
        }
        else if (children !== Math.round(children) && Math.abs(children) >= 0.001) {
            try {
                title = children;
                children = Math.round(children * 1000) / 1000;
            }
            catch { }
        }
    }

    return (
        <span className={className} title={title} {...props}>
            {children}
        </span>
    )
};

export default Float;
