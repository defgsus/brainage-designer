import {createSliceSaga} from "redux-toolkit-saga";
import {call, put, select} from "redux-saga/effects";
import {get_api} from "/src/app/api";
import {setTableResponse} from "./tableview-slice";


function *requestTableSaga(action) {
    const {url, namespace} = action.payload;

    const {tables_per_url} = yield select((state) => state.tables);
    const {limit, offset, sort, filters} = (tables_per_url[`${namespace}${url}`] || {});
    const query_args = {};
    if (offset)
        query_args._offset = offset;
    if (limit)
        query_args._limit = limit;
    if (sort)
        query_args._sort = sort;
    if (filters) {
        for (const key of Object.keys(filters))
            query_args[key] = filters[key];
    }
    const api = yield* get_api();
    const response = yield call(() => api.get(url, {params: query_args}));
    yield put(setTableResponse({url, namespace, data: response.data}));
}
export {requestTableSaga}

export const tableviewSaga = createSliceSaga({
    name: "tableviewSaga",
    caseSagas: {
        requestTable: requestTableSaga,
    },
});

export const {
    requestTable,
} = tableviewSaga.actions;
