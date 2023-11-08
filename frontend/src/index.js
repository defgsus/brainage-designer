import React from 'react'
import * as ReactDOM from 'react-dom/client'
import { store } from './store'
import { Provider } from 'react-redux'
import App from './app/App'
import './index.scss'
import 'antd/dist/reset.css';


window.addEventListener('DOMContentLoaded', () => {

    ReactDOM.createRoot(
        document.getElementById('app')
    ).render(
        <Provider store={store}>
            <App/>
        </Provider>
    );

});