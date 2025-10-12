import { useTranslation } from 'react-i18next';
import { useStatistics } from '@/hooks/useStatistics';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ChartContainer, ChartTooltip, ChartTooltipContent } from '@/components/ui/chart';
import { Clock, Play, TrendingUp } from 'lucide-react';
import { Bar, BarChart, CartesianGrid, Line, LineChart, XAxis, YAxis } from 'recharts';
import { formatDuration } from '@/lib/utils';

export default function StatisticsPage() {
  const { t } = useTranslation();
  const { summary, playsByDay, playsByVideo, loading } = useStatistics();

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="text-muted-foreground">{t('app.loading')}</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('statistics.title')}</h2>
        <p className="text-muted-foreground">View your playback statistics</p>
      </div>

      {/* Summary Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t('statistics.totalPlays')}
            </CardTitle>
            <Play className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_plays || 0}</div>
            <p className="text-xs text-muted-foreground">All time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              {t('statistics.totalDuration')}
            </CardTitle>
            <Clock className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {summary ? formatDuration(summary.total_duration) : '0:00'}
            </div>
            <p className="text-xs text-muted-foreground">Viewing time</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Videos</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{summary?.total_videos || 0}</div>
            <p className="text-xs text-muted-foreground">In library</p>
          </CardContent>
        </Card>
      </div>

      {/* Plays by Day Chart */}
      <Card>
        <CardHeader>
          <CardTitle>{t('statistics.playsByDay')}</CardTitle>
          <CardDescription>Your pet's viewing activity over the last 30 days</CardDescription>
        </CardHeader>
        <CardContent>
          {playsByDay.length === 0 ? (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              No playback data available yet
            </div>
          ) : (
            <ChartContainer
              config={{
                plays: {
                  label: 'Plays',
                  color: 'hsl(var(--primary))',
                },
              }}
              className="h-[300px]"
            >
              <LineChart data={playsByDay}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis
                  dataKey="date"
                  tickFormatter={(value) => {
                    const date = new Date(value);
                    return `${date.getMonth() + 1}/${date.getDate()}`;
                  }}
                />
                <YAxis />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Line
                  type="monotone"
                  dataKey="plays"
                  stroke="var(--color-plays)"
                  strokeWidth={2}
                  dot={{ fill: 'var(--color-plays)' }}
                />
              </LineChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>

      {/* Plays by Video Chart */}
      <Card>
        <CardHeader>
          <CardTitle>{t('statistics.playsByVideo')}</CardTitle>
          <CardDescription>Most popular videos (top 10)</CardDescription>
        </CardHeader>
        <CardContent>
          {playsByVideo.length === 0 ? (
            <div className="h-[300px] flex items-center justify-center text-muted-foreground">
              No playback data available yet
            </div>
          ) : (
            <ChartContainer
              config={{
                play_count: {
                  label: 'Plays',
                  color: 'hsl(var(--accent))',
                },
              }}
              className="h-[300px]"
            >
              <BarChart data={playsByVideo} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis
                  dataKey="video_title"
                  type="category"
                  width={150}
                  tickFormatter={(value) => {
                    return value.length > 20 ? `${value.substring(0, 20)}...` : value;
                  }}
                />
                <ChartTooltip content={<ChartTooltipContent />} />
                <Bar dataKey="play_count" fill="var(--color-play_count)" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ChartContainer>
          )}
        </CardContent>
      </Card>

      {/* Recent Activity */}
      {summary?.recent_plays && summary.recent_plays.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Recent Activity</CardTitle>
            <CardDescription>Latest video plays</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {summary.recent_plays.map((play, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div className="flex-1">
                    <p className="font-medium">{play.video_title}</p>
                    <p className="text-sm text-muted-foreground">
                      {new Date(play.timestamp).toLocaleString()}
                    </p>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {formatDuration(play.duration)}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

