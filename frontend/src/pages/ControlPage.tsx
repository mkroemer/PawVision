import { useTranslation } from 'react-i18next';
import { useState } from 'react';
import { usePlaybackStatus } from '@/hooks/usePlaybackStatus';
import { useVideos } from '@/hooks/useVideos';
import { useToast } from '@/hooks/useToast';
import { videoService } from '@/services/videoService';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Slider } from '@/components/ui/slider';
import { Play, Square, Pause, PlayCircle, Volume2 } from 'lucide-react';
import { HDMIStreamViewer } from '@/components/HDMIStreamViewer';

export default function ControlPage() {
  const { t } = useTranslation();
  const { status, refetch } = usePlaybackStatus();
  const { videos } = useVideos();
  const { showSuccess, showError } = useToast();
  const [volume, setVolume] = useState(100);

  const handlePlay = async (videoPath: string) => {
    try {
      await videoService.play(videoPath);
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
      showSuccess(t('control.resumed'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handleVolumeChange = async (value: number[]) => {
    const newVolume = value[0];
    setVolume(newVolume);
    
    // Only send to backend if video is playing
    if (status.is_playing) {
      try {
        await videoService.setVolume(newVolume);
      } catch (error) {
        console.error('Failed to set volume:', error);
      }
    }
  };

  const formatTime = (seconds: number | undefined) => {
    if (!seconds) return '0:00';
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  const isPaused = status.paused || false;
  const isPlaying = status.is_playing && !isPaused;

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('control.title')}</h2>
        <p className="text-muted-foreground">{t('control.description')}</p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Playback Control */}
        <Card>
          <CardHeader>
            <CardTitle>{t('control.playbackControl')}</CardTitle>
            <CardDescription>
              {isPlaying ? t('control.playing') : isPaused ? t('control.paused') : t('control.stopped')}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              {/* Pause/Resume Button */}
              {isPaused ? (
                <Button
                  onClick={handleResume}
                  variant="default"
                  className="flex-1"
                >
                  <PlayCircle className="mr-2 h-4 w-4" />
                  {t('control.resume')}
                </Button>
              ) : (
                <Button
                  onClick={handlePause}
                  variant="default"
                  className="flex-1"
                  disabled={!status.is_playing}
                >
                  <Pause className="mr-2 h-4 w-4" />
                  {t('control.pause')}
                </Button>
              )}
              
              {/* Stop Button */}
              <Button
                onClick={handleStop}
                variant="destructive"
                className="flex-1"
                disabled={!status.is_playing}
              >
                <Square className="mr-2 h-4 w-4" />
                {t('control.stop')}
              </Button>
            </div>

            {/* Volume Control */}
            <div className="space-y-2 pt-2 border-t">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <Volume2 className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{t('control.volume')}</span>
                </div>
                <span className="text-sm text-muted-foreground">{volume}%</span>
              </div>
              <Slider
                value={[volume]}
                onValueChange={handleVolumeChange}
                max={100}
                step={1}
                disabled={!status.is_playing}
                className="w-full"
              />
            </div>

            {/* Playing Progress */}
            {status.is_playing && status.current_video && (
              <div className="space-y-2 pt-2 border-t">
                <div className="text-sm">
                  <div className="font-medium text-foreground mb-1">
                    {status.current_video.title || t('control.currentlyPlaying')}
                  </div>
                  {status.current_video.playback_time !== undefined && status.current_video.playback_time !== null && status.current_video.duration && (
                    <div className="text-muted-foreground">
                      {formatTime(status.current_video.playback_time)} / {formatTime(status.current_video.duration)}
                    </div>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Quick Play */}
        <Card>
          <CardHeader>
            <CardTitle>{t('control.quickPlay')}</CardTitle>
            <CardDescription>{t('control.quickPlayDescription')}</CardDescription>
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
                    onClick={() => handlePlay(video.path)}
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

      {/* HDMI Stream Viewer */}
      <HDMIStreamViewer />
    </div>
  );
}
