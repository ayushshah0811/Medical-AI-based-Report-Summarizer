import { BrowserRouter, Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import SummaryPage from "./pages/SummaryPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<UploadPage />} />
        <Route path="/summary/:id" element={<SummaryPage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
