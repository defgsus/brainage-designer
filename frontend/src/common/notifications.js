import {notification} from "antd";

const NOTIFICATION_DEFAULTS = {
    duration: 2,
}

export const successNotification = ({message, ...props}) => {
    notification.success({
        message,
        ...NOTIFICATION_DEFAULTS,
        ...props,
    });
}