import "./Error.scss"


const Error = ({children, className, ...props}) => {

    className = className ? `${className} error` : "error";
    return (
        <div className={className} {...props}>
            {children}
        </div>
    )
};

export default Error;
