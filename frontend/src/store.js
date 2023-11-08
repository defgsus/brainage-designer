import { createBrowserHistory } from 'history'
import { createRouterReducer, createRouterMiddleware } from '@lagunovsky/redux-react-router'
import { configureStore, combineReducers } from '@reduxjs/toolkit'
import createSagaMiddleware from "redux-saga";
import {all} from "redux-saga/effects";
import {dashboardSaga} from "./features/dashboard/dashboard-saga";
import {dashboardSlice} from "./features/dashboard/dashboard-slice";
import {preprocessingSaga} from "./features/preprocessing/preprocessing-saga";
import {preprocessingSlice} from "./features/preprocessing/preprocessing-slice";
import {tableviewSaga} from "./features/tableview/tableview-saga";
import {tableviewSlice} from "./features/tableview/tableview-slice";
import {processSaga} from "./features/process/process-saga";
import {processSlice} from "./features/process/process-slice";
import {formSaga} from "./features/form/form-saga";
import {formSlice} from "./features/form/form-slice";
import {analysisSaga} from "./features/analysis/analysis-saga";
import {analysisSlice} from "./features/analysis/analysis-slice";
import {websocketSlice} from "./features/ws/websocket-slice";


export const history = createBrowserHistory();

const rootSagas = function* rootSaga() {
    yield all([
        // add sagas here
        dashboardSaga.saga(),
        processSaga.saga(),
        preprocessingSaga.saga(),
        analysisSaga.saga(),
        tableviewSaga.saga(),
        formSaga.saga(),
    ]);
};

const rootReducer = combineReducers({
    // add reducers here
    router: createRouterReducer(history),
    websocket: websocketSlice.reducer,
    dashboard: dashboardSlice.reducer,
    process: processSlice.reducer,
    preprocessing: preprocessingSlice.reducer,
    analysis: analysisSlice.reducer,
    tables: tableviewSlice.reducer,
    form: formSlice.reducer,
});


const sagaMiddleware = createSagaMiddleware();

export const store = configureStore({
    reducer: rootReducer,
    middleware: getDefaultMiddleware => (
        getDefaultMiddleware({
            // this may take too much time for the size of the state
            // serializableCheck: false,
        }).concat([
            createRouterMiddleware(history),
            sagaMiddleware,
        ])
    )
});
sagaMiddleware.run(rootSagas);

window.store = store;
