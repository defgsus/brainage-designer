import {Row, Col} from "antd";
import Date from "./Date";
import Uuid from "./Uuid";
import AutoTag from "./AutoTag";
import {useEffect, useState} from "react";
import Json from "./Json";
import "./Values.scss"
import Float from "./Float";


const Values = ({values, show, hide, onClick=null, ...props}) => {

    const [value_list, set_value_list] = useState([]);

    useEffect(() => {
        let tmp_list = [];
        if (!values) {

        } else if (Array.isArray(values)) {
            tmp_list = values;
        } else if (typeof values === "object") {
            tmp_list = Object.keys(values).map(key => (
                {name: key, value: values[key]}
            ));
        }
        if (show) {
            const new_tmp_list = [];
            for (const key of show) {
                const value = tmp_list.find(i => i.name === key) || {name: key, value: "-"};
                new_tmp_list.push(value);
            }
            set_value_list(new_tmp_list);
        } else {
            hide = hide ? [...hide, "_id"] : ["_id"];
            set_value_list(
                tmp_list.filter(item => {
                    if (hide.indexOf(item.name) >= 0)
                        return false;
                    return true;
                })
            );
        }
    }, [values, hide, show]);

    const render_item_value = (item) => {
        let value = item.value;
        if (typeof value === "number") {
            value = <Float>{value}</Float>;
        }
        else if (typeof value === "object") {
            if (value && value["$$typeof"])  // is it a react comp? (more or less)
                return value;
            value = <Json data={value}/>;
        }
        else if (item.name.indexOf("date") >= 0
            || item.name.indexOf("timestamp") >=0
            || item.name.indexOf("created_at") >= 0)
        {
            value = <Date date={value}/>
        }
        else if (item.name.indexOf("uuid") >= 0) {
            value = <Uuid uuid={value} fullName/>
        }
        else if (item.name.indexOf("status") >= 0) {
            value = <AutoTag tag={value}/>
        }
        return value;
    }

    return (
        <div className={"values"}>
            <table>
                <tbody>
                    {value_list.map(item => (
                        <tr key={item.name}
                            className={!onClick ? null : "clickable"}
                            onClick={!onClick ? null : () => onClick(item)}
                        >
                            <td><span className={"value-name"}>{item.name}:</span></td>
                            <td>{render_item_value(item)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    )
};

export default Values;