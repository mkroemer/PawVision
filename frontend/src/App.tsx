import { Routes, Route } from 'react-router-dom';
import { Toaster } from '@/components/ui/sonner';
import { ThemeProvider } from '@/components/theme-provider';
import Layout from '@/components/Layout';
import ControlPage from '@/pages/ControlPage';
import LibraryPage from '@/pages/LibraryPage';
import StatisticsPage from '@/pages/StatisticsPage';
import ConfigPage from '@/pages/ConfigPage';

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="pawvision-ui-theme">
      <Layout>
        <Routes>
          <Route path="/" element={<ControlPage />} />
          <Route path="/library" element={<LibraryPage />} />
          <Route path="/statistics" element={<StatisticsPage />} />
          <Route path="/config" element={<ConfigPage />} />
        </Routes>
      </Layout>
      <Toaster />
    </ThemeProvider>
  );
}

export default App;
