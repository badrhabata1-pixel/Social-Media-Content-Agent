import { useEffect, useState } from 'react';
import {
  Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from 'recharts';
import { Activity, ChartColumn, FileText, RefreshCw, TriangleAlert, Trophy } from 'lucide-react';
import { API_BASE, BACKEND_UNREACHABLE, apiErrorMessage, readJson } from '../api';
import './AnalyticsDashboard.css';

// Single series -> one color: the theme's --primary. Checked with the dataviz palette
// validator against the white card surface (contrast >= 3:1, lightness/chroma in band).
const BAR_COLOR = '#a855f7';
const GRID_COLOR = '#e2e8f0';   // --border-color
const INK_MUTED = '#64748b';    // --text-muted
const INK_MAIN = '#1a1a1a';     // --text-main
const MAX_BARS = 10;

const GROUPINGS = [
  { key: 'by_domain', label: 'Domain' },
  { key: 'by_topic', label: 'Topic' },
  { key: 'by_tone', label: 'Tone' },
];

const DOMAIN_LABELS = {
  tech_ai: 'Tech & AI',
  productivity_time: 'Productivity',
  education_study: 'Education',
  business_career: 'Business',
  general: 'General',
};

const compact = new Intl.NumberFormat('en', { notation: 'compact', maximumFractionDigits: 1 });
const formatNumber = value => compact.format(value ?? 0);
const truncate = (text, max = 22) => (text.length > max ? `${text.slice(0, max - 1)}…` : text);

async function fetchReport() {
  const response = await fetch(`${API_BASE}/analytics/report`);
  const payload = await readJson(response);
  if (!response.ok || payload?.status !== 'success') throw new Error(apiErrorMessage(payload, response.status));
  return payload.data;
}

function describeFailure(err) {
  return err instanceof TypeError ? BACKEND_UNREACHABLE : err.message;
}

function formatTime(iso) {
  return iso ? new Date(iso).toLocaleString() : 'never';
}

function ChartTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const row = payload[0].payload;
  return (
    <div className="chart-tooltip">
      <strong>{row.engagement_score.toLocaleString()}</strong>
      <span className="chart-tooltip-name">{row.label}</span>
      <span>{row.posts} {row.posts === 1 ? 'post' : 'posts'} · avg {row.average_engagement} per post</span>
      <span>{row.reactions} reactions · {row.comments} comments · {row.shares} shares</span>
    </div>
  );
}

function StatCard({ icon: Icon, label, value, detail }) {
  return (
    <div className="stat-card">
      <span className="stat-label"><Icon size={16} /> {label}</span>
      <span className="stat-value">{value}</span>
      {detail && <span className="stat-detail">{detail}</span>}
    </div>
  );
}

function AnalyticsDashboard() {
  const [report, setReport] = useState(null);
  const [grouping, setGrouping] = useState('by_domain');
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState('');
  const [syncNote, setSyncNote] = useState('');
  const [reportVersion, setReportVersion] = useState(0); // bump to reload the report

  useEffect(() => {
    let cancelled = false;
    fetchReport()
      .then(data => {
        if (cancelled) return;
        setReport(data);
        setError('');
      })
      .catch(err => { if (!cancelled) setError(describeFailure(err)); })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
  }, [reportVersion]);

  const handleSync = async () => {
    setSyncing(true);
    setError('');
    setSyncNote('');
    try {
      const response = await fetch(`${API_BASE}/analytics/sync`, { method: 'POST' });
      const payload = await readJson(response);
      if (!response.ok || payload?.status !== 'success') throw new Error(apiErrorMessage(payload, response.status));
      const { total, synced, failed } = payload.data;
      setSyncNote(total === 0
        ? 'No published posts to sync yet.'
        : `Synced ${synced} of ${total} posts${failed ? ` · ${failed} could not be read` : ''}.`);
      setReportVersion(version => version + 1);
    } catch (err) {
      setError(describeFailure(err));
    } finally {
      setSyncing(false);
    }
  };

  const groups = report?.[grouping] ?? [];
  const rows = groups.slice(0, MAX_BARS).map(row => ({
    ...row,
    label: grouping === 'by_domain' ? (DOMAIN_LABELS[row.name] ?? row.name) : row.name,
  }));
  const hasEngagement = (report?.total_engagement ?? 0) > 0;
  const topDomain = report?.top_domain;

  return (
    <section className="analytics-dashboard">
      <div className="analytics-toolbar card">
        <div>
          <h3 className="section-title analytics-title">Monitor &amp; Analytics</h3>
          <p className="analytics-subtitle">
            Engagement score = {report?.scoring ?? 'reactions + 2 × comments + 3 × shares'} · Last synced: {formatTime(report?.last_synced_at)}
          </p>
        </div>
        <button className="btn-outline sync-btn" onClick={handleSync} disabled={syncing || loading}>
          <RefreshCw size={16} className={syncing ? 'spin' : ''} />
          {syncing ? 'Syncing…' : 'Sync Live Metrics'}
        </button>
      </div>

      {error && <div className="error-message"><TriangleAlert size={16} /> {error}</div>}
      {syncNote && !error && <div className="sync-note">{syncNote}</div>}

      {loading && (
        <div className="loading-state card">
          <div className="spinner-large" />
          <p>Loading analytics…</p>
        </div>
      )}

      {report && (
        <>
          <div className="stat-grid">
            <StatCard icon={FileText} label="Total posts" value={formatNumber(report.total_posts)}
                      detail="Published through the agent" />
            <StatCard icon={Trophy} label="Top domain"
                      value={topDomain ? (DOMAIN_LABELS[topDomain.name] ?? topDomain.name) : '—'}
                      detail={topDomain ? `${topDomain.average_engagement} avg score per post` : 'No engagement recorded yet'} />
            <StatCard icon={Activity} label="Total engagement" value={formatNumber(report.total_engagement)}
                      detail={`${report.totals.reactions} reactions · ${report.totals.comments} comments · ${report.totals.shares} shares`} />
          </div>

          <div className="card chart-card">
            <div className="chart-header">
              <h4><ChartColumn size={18} /> Engagement score by {GROUPINGS.find(g => g.key === grouping).label.toLowerCase()}</h4>
              <div className="segmented" role="tablist" aria-label="Group by">
                {GROUPINGS.map(g => (
                  <button key={g.key} type="button" role="tab" aria-selected={grouping === g.key}
                          className={grouping === g.key ? 'active' : ''} onClick={() => setGrouping(g.key)}>
                    {g.label}
                  </button>
                ))}
              </div>
            </div>

            {rows.length === 0 ? (
              <div className="empty-state">
                No published posts yet. Publish a post to Facebook, then sync live metrics.
              </div>
            ) : (
              <>
                {!hasEngagement && (
                  <p className="chart-note">No engagement recorded yet. Use “Sync Live Metrics” to pull the latest counts.</p>
                )}
                <ResponsiveContainer width="100%" height={rows.length * 44 + 40}>
                  <BarChart data={rows} layout="vertical" margin={{ top: 4, right: 48, bottom: 4, left: 4 }}>
                    <CartesianGrid horizontal={false} stroke={GRID_COLOR} strokeWidth={1} />
                    <XAxis type="number" allowDecimals={false} tickFormatter={formatNumber}
                           axisLine={false} tickLine={false} tick={{ fill: INK_MUTED, fontSize: 12 }} />
                    <YAxis type="category" dataKey="label" width={150} tickFormatter={label => truncate(label)}
                           axisLine={{ stroke: GRID_COLOR }} tickLine={false} tick={{ fill: INK_MAIN, fontSize: 13 }} />
                    <Tooltip content={<ChartTooltip />} cursor={{ fill: 'rgba(168, 85, 247, 0.06)' }} />
                    <Bar dataKey="engagement_score" fill={BAR_COLOR} maxBarSize={24} radius={[0, 4, 4, 0]}
                         isAnimationActive={false}>
                      <LabelList dataKey="engagement_score" position="right" formatter={formatNumber}
                                 fill={INK_MUTED} fontSize={12} />
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
                {groups.length > MAX_BARS && (
                  <p className="chart-note">Showing the top {MAX_BARS} of {groups.length}. The table lists all of them.</p>
                )}

                <details className="chart-table">
                  <summary>View as table</summary>
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">{GROUPINGS.find(g => g.key === grouping).label}</th>
                        <th scope="col">Posts</th><th scope="col">Reactions</th><th scope="col">Comments</th>
                        <th scope="col">Shares</th><th scope="col">Score</th><th scope="col">Avg / post</th>
                      </tr>
                    </thead>
                    <tbody>
                      {groups.map(row => (
                        <tr key={row.name}>
                          <th scope="row">{grouping === 'by_domain' ? (DOMAIN_LABELS[row.name] ?? row.name) : row.name}</th>
                          <td>{row.posts}</td><td>{row.reactions}</td><td>{row.comments}</td>
                          <td>{row.shares}</td><td>{row.engagement_score}</td><td>{row.average_engagement}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              </>
            )}
          </div>

          {report.top_posts.length > 0 && (
            <div className="card">
              <h4 className="top-posts-title">Top posts</h4>
              <table className="top-posts">
                <thead>
                  <tr>
                    <th scope="col">Topic</th><th scope="col">Domain</th><th scope="col">Tone</th>
                    <th scope="col">Score</th><th scope="col">Post</th>
                  </tr>
                </thead>
                <tbody>
                  {report.top_posts.map(post => (
                    <tr key={post.platform_post_id}>
                      <th scope="row" title={post.topic}>{truncate(post.topic || '—', 48)}</th>
                      <td>{DOMAIN_LABELS[post.domain] ?? post.domain}</td>
                      <td>{post.tone}</td>
                      <td>{post.engagement_score}</td>
                      <td>
                        <a href={`https://facebook.com/${post.platform_post_id}`} target="_blank" rel="noreferrer">
                          Open
                        </a>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </section>
  );
}

export default AnalyticsDashboard;
