// 임시
/*
import React from 'react'
import ReactDOM from 'react-dom/client'
import SpineDiskPage from './DH/SpineDiskPage' // 우리가 만든 파일 직접 임포트
import './index.css' // 스타일을 위해 꼭 필요합니다!

ReactDOM.createRoot(document.getElementById('root')).render(
    <React.StrictMode>
        <SpineDiskPage />
    </React.StrictMode>,
)
*/

import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)




