import Moment from "moment";
import {useEffect, useState} from "react";


const Date = ({date, ...props}) => {
    const [display_props, set_display_props] = useState({text: null, title: null});

    useEffect(() => {
        try {
            if (typeof date === "string" && date[10] !== "T")
                date = `${date.slice(0, 10)}T${date.slice(11)}`;
            const mtm = Moment(date || "-");

            if (mtm.isValid()) {
                set_display_props({
                    text: mtm.format("YYYY/MM/DD hh:mm:ss"),
                    title: `${mtm.format("dddd, MMM Mo YYYY @ hh:mm:ss.SSSS")} | ${mtm.fromNow()}`
                });
            } else {
                set_display_props({
                    text: date || "-",
                    title: "invalid date",
                })
            }
        } catch {
            set_display_props({text: "-", title: "invalid date"})
        }

    }, [date]);

    return (
        <span className={"nowrap"} {...props} title={display_props.title}>{display_props.text}</span>
    )
}

export default Date;