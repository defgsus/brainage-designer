

const Text = ({text, className, ...props}) => {
    className = className ? `${className} prewrap` : "prewrap";

    return (
        <div className={className} {...props}>
            {text}
        </div>
    );
}

export default Text;