# 9. React Dashboard

## 9.1 Page Breakdown

**Page 1: Dashboard (landing page)**
- 4 stat cards: Total Jobs, Avg Salary Range, Remote %, Active Sources
- Line chart: Job posting volume over time (by week)
- Bar chart: Top 15 skills by demand
- Pie chart: Jobs by source
- Donut chart: Remote vs on-site

**Page 2: Job Explorer**
- Filterable, searchable table of all jobs
- Filters: source, location, salary range, remote, employment type
- Click to expand job detail
- Export to CSV button

**Page 3: Salary Insights**
- Horizontal bar chart: Average salary by city (top 15)
- Grouped bar chart: Salary by experience level
- Salary bucket histogram

**Page 4: Skill Demand**
- Treemap: Top 30 skills sized by demand
- Multi-line chart: Selected skills over time
- Table: Skill → avg salary → demand count

**Page 5: About**
- Data sources and methodology
- Pipeline architecture diagram
- Last updated timestamp

## 9.2 Chart Recommendations per Insight

| Insight | Chart Type | Why |
|---|---|---|
| Top skills by demand | Horizontal bar | Easy to read skill names |
| Salary by city | Grouped horizontal bar (min/max) | Compare ranges across locations |
| Skill trends over time | Multi-line chart | Temporal patterns |
| Jobs by source | Pie/donut | Part-of-whole |
| Remote vs onsite | Donut with center stat | Clean two-category |
| Salary distribution | Histogram | Shape of distribution |
| Salary by experience | Grouped bar | Entry/mid/senior comparison |
| Industry breakdown | Treemap | Relative sizes |
| Job posting volume | Area chart | Overall market trend |

## 9.3 Key Components

```jsx
// frontend/src/api/client.js
import axios from "axios";
const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1",
  timeout: 10000,
});
export default api;
```

```jsx
// frontend/src/hooks/useAnalytics.js
import { useState, useEffect } from "react";
import api from "../api/client";

export function useAnalytics(endpoint, params = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api.get(`/analytics/${endpoint}/`, { params })
      .then((res) => { if (!cancelled) setData(res.data); })
      .catch((err) => { if (!cancelled) setError(err.message); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [endpoint, JSON.stringify(params)]);

  return { data, loading, error };
}
```

```jsx
// frontend/src/components/shared/StatCard.jsx
export default function StatCard({ label, value, subtitle, icon }) {
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-zinc-500">{label}</p>
        {icon && <span className="text-zinc-400">{icon}</span>}
      </div>
      <p className="mt-2 text-3xl font-semibold tracking-tight text-zinc-900">{value}</p>
      {subtitle && <p className="mt-1 text-sm text-zinc-500">{subtitle}</p>}
    </div>
  );
}
```

```jsx
// frontend/src/components/charts/TopSkillsBar.jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

export default function TopSkillsBar({ data }) {
  if (!data || data.length === 0) return null;
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-base font-semibold text-zinc-900">Top Skills by Demand</h3>
      <ResponsiveContainer width="100%" height={400}>
        <BarChart data={data} layout="vertical" margin={{ top: 0, right: 30, left: 100, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" />
          <YAxis type="category" dataKey="skill_name" tick={{ fontSize: 13 }} width={90} />
          <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e4e4e7" }} />
          <Bar dataKey="posting_count" fill="#2563eb" radius={[0, 4, 4, 0]} name="Job Postings" />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

```jsx
// frontend/src/components/charts/SalaryDistribution.jsx
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

export default function SalaryDistribution({ data }) {
  if (!data || data.length === 0) return null;
  const formatted = data.map((d) => ({
    ...d, city: d.location__city,
    avg_min: Math.round(d.avg_min), avg_max: Math.round(d.avg_max),
  }));
  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-base font-semibold text-zinc-900">Average Salary by City (Monthly PHP)</h3>
      <ResponsiveContainer width="100%" height={500}>
        <BarChart data={formatted.slice(0, 15)} layout="vertical" margin={{ top: 0, right: 30, left: 120, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis type="number" tickFormatter={(v) => `₱${(v / 1000).toFixed(0)}k`} />
          <YAxis type="category" dataKey="city" tick={{ fontSize: 13 }} />
          <Tooltip formatter={(v) => `₱${Number(v).toLocaleString()}`}
                   contentStyle={{ borderRadius: "8px", border: "1px solid #e4e4e7" }} />
          <Legend />
          <Bar dataKey="avg_min" fill="#3b82f6" name="Avg Min" radius={[0, 4, 4, 0]} />
          <Bar dataKey="avg_max" fill="#1d4ed8" name="Avg Max" radius={[0, 4, 4, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

```jsx
// frontend/src/components/charts/JobTrendLine.jsx
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Legend } from "recharts";

const COLORS = ["#2563eb", "#dc2626", "#16a34a", "#ea580c", "#7c3aed", "#0891b2", "#ca8a04", "#be185d"];

export default function JobTrendLine({ data, skills }) {
  if (!data || data.length === 0) return null;
  const byDate = {};
  data.forEach((d) => {
    if (!byDate[d.date]) byDate[d.date] = { date: d.date };
    byDate[d.date][d.skill__skill_name] = d.posting_count;
  });
  const chartData = Object.values(byDate).sort((a, b) => new Date(a.date) - new Date(b.date));
  const uniqueSkills = skills || [...new Set(data.map((d) => d.skill__skill_name))];

  return (
    <div className="rounded-xl border border-zinc-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 text-base font-semibold text-zinc-900">Skill Demand Over Time</h3>
      <ResponsiveContainer width="100%" height={400}>
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
          <XAxis dataKey="date" tick={{ fontSize: 12 }} />
          <YAxis />
          <Tooltip contentStyle={{ borderRadius: "8px", border: "1px solid #e4e4e7" }} />
          <Legend />
          {uniqueSkills.map((skill, i) => (
            <Line key={skill} type="monotone" dataKey={skill}
                  stroke={COLORS[i % COLORS.length]} strokeWidth={2} dot={false} />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
```

See the Dashboard page component in the original plan for the full page assembly with stat cards + charts.
