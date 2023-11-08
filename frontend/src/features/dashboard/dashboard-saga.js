import {createSliceSaga} from "redux-toolkit-saga";
import {call, put} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {setDashboard, setStatus} from "./dashboard-slice";
import {API_URLS} from "/src/app/urls";


export const dashboardSaga = createSliceSaga({
    name: "dashboardSaga",
    caseSagas: {
        *requestDashboard() {
            const api = yield* get_api();
            const response = yield call(() => api.get(API_URLS.DASHBOARD));
            yield put(setDashboard(response.data));
        },
        *requestStatus() {
            const api = yield* get_api();
            const response = yield call(() => api.get(API_URLS.STATUS));
            yield put(setStatus(response.data));
        },
    },
});

export const {
    requestDashboard,
    requestStatus,
} = dashboardSaga.actions;
