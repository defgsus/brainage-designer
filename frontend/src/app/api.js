import axios from "axios";


function* get_api(config) {
    const api = axios.create(config);
    api.defaults.headers.post = {
        ContentType: "application/json",
    };

    return api;
}

export { get_api };