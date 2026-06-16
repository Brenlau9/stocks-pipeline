import { useEffect, useState } from "react";
import "./App.css";

function App() {
  const [movers, setMovers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function fetchMovers() {
      try {
        const response = await fetch(import.meta.env.VITE_API_URL);

        if (!response.ok) {
          throw new Error("Failed to fetch movers");
        }

        const data = await response.json();
        setMovers(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    }

    fetchMovers();
  }, []);

  return (
    <main className="container">
      <h1>Daily Stock Top Movers</h1>
      <p>Last 7 winning stocks from the watchlist.</p>

      {loading && <p>Loading...</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Ticker</th>
              <th>Percent Change</th>
              <th>Closing Price</th>
            </tr>
          </thead>
          <tbody>
            {movers.map((mover) => (
              <tr key={mover.date}>
                <td>{mover.date}</td>
                <td>{mover.ticker}</td>
                <td className={mover.percent_change >= 0 ? "gain" : "loss"}>
                  {mover.percent_change}%
                </td>
                <td>${mover.close_price}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}

export default App;