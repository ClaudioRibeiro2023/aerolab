import React from 'react'
import ReactDOM from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ErrorBoundary } from '@/components/common/ErrorBoundary'
import App from './App'
import './styles/index.css'
import './styles/module-functions-panel.css'

// Design System Component Styles
import '../../../packages/design-system/src/components/Button/Button.css'
import '../../../packages/design-system/src/components/Input/Input.css'
import '../../../packages/design-system/src/components/Card/Card.css'
import '../../../packages/design-system/src/components/Modal/Modal.css'
import '../../../packages/design-system/src/components/Toast/Toast.css'
import '../../../packages/design-system/src/components/Tabs/Tabs.css'
import '../../../packages/design-system/src/components/Table/Table.css'
import '../../../packages/design-system/src/components/Dropdown/Dropdown.css'
import '../../../packages/design-system/src/components/Skeleton/Skeleton.css'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <App />
        </BrowserRouter>
      </QueryClientProvider>
    </ErrorBoundary>
  </React.StrictMode>
)
