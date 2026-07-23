import { useEffect, useState } from "react";
import { AppHeader } from "./components/AppHeader";
import { MarketTrendsPage } from "./pages/MarketTrendsPage";
import { ValuationPage } from "./pages/ValuationPage";

type Page = "market" | "valuation";
const pageFor = (pathname: string): Page => pathname === "/arac-degerleme" ? "valuation" : "market";

export default function App() {
  const [page, setPage] = useState<Page>(() => pageFor(window.location.pathname));
  useEffect(() => { const sync = () => setPage(pageFor(window.location.pathname)); window.addEventListener("popstate", sync); return () => window.removeEventListener("popstate", sync); }, []);
  const navigate = (path: string) => { window.history.pushState({}, "", path); setPage(pageFor(path)); window.scrollTo({ top: 0, behavior: "smooth" }); };
  return <><AppHeader page={page} onNavigate={navigate} />{page === "valuation" ? <ValuationPage /> : <MarketTrendsPage />}<footer><div className="shell">ArabamFiyat.com <span>·</span> Veriye dayalı ikinci el araç piyasa analizi</div></footer></>;
}
