import "./Flex.scss"
import {cloneElement} from "react";

const DEFAULT_MARGIN = ".1rem";

const _expand_justify = (value) => {
    if (value === "start")
        return "flex-start";
    if (value === "end")
        return "flex-end";
    return value;
}

const Flex = ({
        inline, column, wrap, align, justify, margin, marginX, marginY,
        className, style, children, ...props
}) => {
    const flex_style = {};
    const classes = className?.length ? [className] : [];
    classes.push("flex");

    if (inline)
        classes.push("flex-inline");
    if (column)
        classes.push("flex-column");
    if (wrap)
        classes.push("flex-wrap");
    if (justify)
        flex_style.justifyContent = _expand_justify(justify);
    if (align)
        flex_style.alignItems = _expand_justify(align);
    if (margin || marginX || marginY) {
        if (margin) {
            if (!marginX)
                marginX = margin;
            if (!marginY)
                marginY = margin;
        }
        if (margin === true)
            margin = DEFAULT_MARGIN;
        if (marginX === true)
            marginX = DEFAULT_MARGIN;
        if (marginY === true)
            marginY = DEFAULT_MARGIN;

        const child_style = {};
        if (marginX) {
            flex_style.marginLeft = `-${marginX}`;
            flex_style.marginRight = `-${marginX}`;
            child_style.marginLeft = marginX;
            child_style.marginRight = marginX;
        }
        if (marginY) {
            flex_style.marginTop = `-${marginY}`;
            flex_style.marginBottom = `-${marginY}`;
            child_style.marginTop = marginY;
            child_style.marginBottom = marginY;
        }

        if (children) {
            children = _patch_children(children, child_style);
        }
    }

    return (
        <div
            className={classes.length ? classes.join(" ") : null}
            style={{...flex_style, ...style}}
            {...props}
        >
            {children}
        </div>
    );
}

/** patches the style attributes on all children elements.
 * Recurses into react.fragments
 * @param children the value of parent.props.children
 */
const _patch_children = (children, style, level=2) => {
    if (!children)
        return children;
    if (typeof children.map === "function")
        return children.map((c, i) => _patch_element(c, style, i, level));

    return _patch_element(children, style, null, level);
};

const _patch_element = (c, style, key, level) => {
    //console.log("XX", c, style);
    if (!c || level <= 0)
        return c;
    if (Array.isArray(c)) {
        return c.map(e => _patch_element(e, style, key, level));
    }
    if (c.type?.toString() === "Symbol(react.fragment)") {
        return cloneElement(c, {
            key: c.key || key,
            children: _patch_children(c.props.children, style, level - 1),
        });
    }
    return cloneElement(c, {
        key: c.key || key,
        style: {
            ...c?.props?.style,
            ...style,
        },
    })
}

const Item = ({grow, shrink, basis, style, className, ...props}) => {
    const classes = className?.length ? [className] : [];
    const flex_style = {}

    if (grow)
        flex_style.flexGrow = grow === true ? 1 : grow;
    if (shrink)
        flex_style.flexShrink = shrink === true ? 1 : shrink;

    return (
        <div
            className={classes.length ? classes.join(" ") : null}
            style={{...flex_style, ...style}}
            {...props}
        />
    );
}

Flex.Row = Flex;
Flex.Col = (props) => <Flex column {...props}/>;
Flex.Item = Item;
Flex.Grow = (props) => <Item grow {...props}/>;
Flex.Shrink = (props) => <Item shrink {...props}/>;

export default Flex;
