import { useTranslation } from 'react-i18next';
import { usePlaybackStatus } from '@/hooks/usePlaybackStatus';
import { useVideos } from '@/hooks/useVideos';
import { useToast } from '@/hooks/useToast';
import { videoService } from '@/services/videoService';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Play, Pause, Square, Volume2 } from 'lucide-react';
import { useState } from 'react';

export default function ControlPage() {
  const { t } = useTranslation();
  const { status, refetch } = usePlaybackStatus();
  const { videos } = useVideos();
  const { showSuccess, showError } = useToast();
  const [volume, setVolume] = useState(50);

  const handlePlay = async (videoId: number) => {
    try {
      await videoService.play(videoId);
      showSuccess(t('control.playing'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handleStop = async () => {
    try {
      await videoService.stop();
      showSuccess(t('control.stopped'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handlePause = async () => {
    try {
      await videoService.pause();
      showSuccess(t('control.paused'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handleResume = async () => {
    try {
      await videoService.resume();
      showSuccess(t('control.playing'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handleVolumeChange = async (newVolume: number) => {
    setVolume(newVolume);
    try {
      await videoService.setVolume(newVolume);
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('control.title')}</h2>
        <p className="text-muted-foreground">{t('control.status')}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Playback Control */}
        <Card>
          <CardHeader>
            <CardTitle>Playback Control</CardTitle>
            <CardDescription>
              {status.is_playing ? `${t('control.playing')}` : t('control.stopped')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Button
                onClick={handleStop}
                variant="destructive"
                className="flex-1"
              >
                <Square className="mr-2 h-4 w-4" />
                {t('control.stop')}
              </Button>
              {status.is_playing ? (
                <Button
                  onClick={handlePause}
                  variant="secondary"
                  className="flex-1"
                >
                  <Pause className="mr-2 h-4 w-4" />
                  {t('control.pause')}
                </Button>
              ) : (
                <Button
                  onClick={handleResume}
                  variant="default"
                  className="flex-1"
                >
                  <Play className="mr-2 h-4 w-4" />
                  {t('control.resume')}
                </Button>
              )}
            </div>

            {/* Volume Control */}
            <div className="space-y-2">
              <Label className="flex items-center gap-2">
                <Volume2 className="h-4 w-4" />
                {t('control.volume')}: {volume}%
              </Label>
              <input
                type="range"
                min="0"
                max="100"
                value={volume}
                onChange={(e) => handleVolumeChange(Number(e.target.value))}
                className="w-full"
              />
            </div>
          </CardContent>
        </Card>

        {/* Quick Play */}
        <Card>
          <CardHeader>
            <CardTitle>Quick Play</CardTitle>
            <CardDescription>Select a video to play</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {videos.length === 0 ? (
                <p className="text-sm text-muted-foreground">
                  {t('library.noVideos')}
                </p>
              ) : (
                videos.slice(0, 10).map((video) => (
                  <Button
                    key={video.id}
                    variant="outline"
                    className="w-full justify-start"
                    onClick={() => handlePlay(video.id)}
                  >
                    <Play className="mr-2 h-4 w-4" />
                    {video.title}
                  </Button>
                ))
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
