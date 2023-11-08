
const API_URLS = {
    url: "/api",
    DASHBOARD: "/dashboard/",
    STATUS: "/status/",
    WEBSOCKET: "/ws/",
    FILES: {
        "url": "/files",
        BROWSE: "/browse/",
        IMAGE: {
            url: "/image",
            META: "/meta/",
            SLICE: "/slice/",
            SLICES: "/slices/",
            PLOT: "/plot/",
            BLOB: "/blob/",
        },
    },
    PROCESS: {
        url: "/process",
        TABLE: "/table/",
        GET: "/:uuid/",
        EVENT: {
            url: "/event",
            TABLE: "/table/",
        },
        OBJECT: {
            url: "/object",
            TABLE: "/table/",
            BY_MODULE: "/module/",
        },
    },
    PREPROCESSING: {
        url: "/preprocess",
        TABLE: "/table/",
        GET: "/:uuid/",
        POST: "/:uuid/",
        CREATE: "/",
        START_PROCESS: "/:uuid/start/",
        STOP_PROCESS: "/:uuid/stop/",
        COPY: "/:uuid/copy/",
    },
    ANALYSIS: {
        url: "/analysis",
        TABLE: "/table/",
        GET: "/:uuid/",
        POST: "/:uuid/",
        CREATE: "/",
        START_PROCESS: "/:uuid/start/",
        STOP_PROCESS: "/:uuid/stop/",
        COPY: "/:uuid/copy/",
        SOURCE_PREVIEW: "/:uuid/source-preview/",
        RESULT: "/:uuid/result/",
        RESULTS: {
            url: "/results",
            GET: "/:uuid/",
            TABLE: "/table/",
        },
    },
}


const APP_URLS = {
    url: "",
    DASHBOARD: "/",
    TEST: {
        url: "/test",
        BROWSER: "/browser",
        FLEX: "/flex",
        SHADER: "/shader",
    },
    PROCESS: {
        url: "/process",
        VIEW: "/:p_id",
    },
    PREPROCESSING: {
        url: "/preprocessing",
        VIEW: "/:pp_id",
    },
    ANALYSIS: {
        url: "/analysis",
        VIEW: "/:ap_id",
    },
    FILES: {
        url: "/files",
        IMAGE: "/image/*",
        VOLUME: "/volume/*",
    }
};

const _patch_urls = (url_mapping, prefix=null) => {
    const sub_path = prefix ? `${prefix}${url_mapping.url}` : url_mapping.url;
    for (const key of Object.keys(url_mapping)) {
        if (key !== "url") {
            const value = url_mapping[key];

            if (typeof value === "object")
                _patch_urls(value, sub_path);
            else
                url_mapping[key] = `${sub_path}${value}`;
        }
    }
};

_patch_urls(APP_URLS);
_patch_urls(API_URLS);


const OBJECT_URLS = {
    "p": {name: "process", url: APP_URLS.PROCESS.VIEW},
    "pp": {name: "preprocessing pipeline", url: APP_URLS.PREPROCESSING.VIEW},
    "ap": {name: "analysis pipeline", url: APP_URLS.ANALYSIS.VIEW},
};


export {
    APP_URLS, API_URLS,
    OBJECT_URLS,
}
