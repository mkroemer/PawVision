import { useTranslation } from 'react-i18next';
import { useEffect, useState } from 'react';
import { usePlaybackStatus } from '@/hooks/usePlaybackStatus';
import { useVideos } from '@/hooks/useVideos';
import { useToast } from '@/hooks/useToast';
import { videoService } from '@/services/videoService';
import { youtubeService } from '@/services/youtubeService';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Play, Square, Pause, PlayCircle, Volume2, SkipForward } from 'lucide-react';
import { HDMIStreamViewer } from '@/components/HDMIStreamViewer';
import { useConfig } from '@/hooks/useConfig';

export default function ControlPage() {
  const { t } = useTranslation();
  const { status, refetch } = usePlaybackStatus();
  const { videos } = useVideos();
  const { config } = useConfig();
  const { showSuccess, showError } = useToast();
  const [volume, setVolume] = useState(100);
  const [isActing, setIsActing] = useState(false);
  const [simpleMode, setSimpleMode] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [youtubeOffline, setYoutubeOffline] = useState(true);

  useEffect(() => {
    if (config?.volume !== undefined) setVolume(config.volume);
  }, [config?.volume]);

  useEffect(() => {
    const value = localStorage.getItem('pawvision_simple_mode');
    if (value !== null) {
      setSimpleMode(value === 'true');
    }
  }, []);

  useEffect(() => {
    localStorage.setItem('pawvision_simple_mode', String(simpleMode));
    if (!simpleMode) {
      setShowAdvanced(true);
    }
  }, [simpleMode]);

  const handlePlay = async (videoPath: string) => {
    try {
      setIsActing(true);
      await videoService.play(videoPath);
      showSuccess(t('control.playing'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setIsActing(false);
    }
  };

  const handleStop = async () => {
    try {
      setIsActing(true);
      const response = await videoService.stop();
      if (response.success) {
        showSuccess(t('control.stopped'));
      } else {
        showError(response.message || t('messages.error'));
      }
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setIsActing(false);
    }
  };

  const handleNext = async () => {
    try {
      setIsActing(true);
      const response = await videoService.next();
      if (response.success) {
        showSuccess(t('control.nextPlaying'));
      } else {
        showError(response.message || t('messages.error'));
      }
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setIsActing(false);
    }
  };

  const handlePause = async () => {
    try {
      setIsActing(true);
      const response = await videoService.pause();
      if (response.success) {
        showSuccess(t('control.paused'));
      } else {
        showError(response.message || t('messages.error'));
      }
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setIsActing(false);
    }
  };

  const handleResume = async () => {
    try {
      setIsActing(true);
      const response = await videoService.resume();
      if (response.success) {
        showSuccess(t('control.resumed'));
      } else {
        showError(response.message || t('messages.error'));
      }
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setIsActing(false);
    }
  };

  const handleVolumeChange = (value: number[]) => {
    const newVolume = value[0];
    setVolume(newVolume);
  };

  // Only send to backend once the user releases the slider
  const commitVolumeChange = async (value: number[]) => {
    const newVolume = value[0];
    if (status.is_playing) {
      try {
        await videoService.setVolume(newVolume);
      } catch (error) {
        showError(t('messages.error'));
      }
    }
  };

  const handleQuickYoutubeAdd = async () => {
    if (!youtubeUrl.trim()) return;
    try {
      const result = youtubeOffline
        ? await youtubeService.download(youtubeUrl.trim())
        : await youtubeService.add(youtubeUrl.trim());
      if (result.success) {
        showSuccess(youtubeOffline ? 'YouTube video added and downloading' : 'YouTube video added');
        setYoutubeUrl('');
      } else {
        showError(result.message || t('messages.error'));
      }
    } catch (error) {
      showError(t('messages.error'));
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

      <div className="flex items-center justify-between rounded-lg border p-3">
        <div className="space-y-1">
          <Label htmlFor="simple-mode-toggle">Simple Mode</Label>
          <p className="text-xs text-muted-foreground">Shows only practical core controls.</p>
        </div>
        <Switch id="simple-mode-toggle" checked={simpleMode} onCheckedChange={setSimpleMode} />
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
              {isPaused ? (
                <Button onClick={handleResume} variant="default" className="flex-1" disabled={isActing}>
                  <PlayCircle className="mr-2 h-4 w-4" />
                  {t('control.resume')}
                </Button>
              ) : (
                <Button onClick={handlePause} variant="default" className="flex-1" disabled={isActing || !status.is_playing}>
                  <Pause className="mr-2 h-4 w-4" />
                  {t('control.pause')}
                </Button>
              )}

              <Button onClick={handleStop} variant="destructive" className="flex-1" disabled={isActing || !status.is_playing}>
                <Square className="mr-2 h-4 w-4" />
                {t('control.stop')}
              </Button>

              <Button onClick={handleNext} variant="secondary" className="flex-1" disabled={isActing}>
                <SkipForward className="mr-2 h-4 w-4" />
                {t('control.next')}
              </Button>
            </div>

            {(!simpleMode || showAdvanced) && (
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
                  onValueCommit={commitVolumeChange}
                  max={100}
                  step={1}
                  disabled={isActing || !status.is_playing}
                  className="w-full"
                />
              </div>
            )}

            {(!simpleMode || showAdvanced) && status.is_playing && status.current_video && (
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
            {simpleMode && (
              <Button variant="ghost" className="w-full" onClick={() => setShowAdvanced((prev) => !prev)}>
                {showAdvanced ? 'Hide advanced controls' : 'Show advanced controls'}
              </Button>
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
                    disabled={isActing}
                  >
                    <Play className="mr-2 h-4 w-4" />
                    {video.title}
                  </Button>
                ))
              )}
            </div>
            <div className="space-y-2 pt-4 border-t mt-4">
              <Label htmlFor="quick-youtube-url">Quick YouTube add/download</Label>
              <Input
                id="quick-youtube-url"
                placeholder="https://youtube.com/watch?v=..."
                value={youtubeUrl}
                onChange={(e) => setYoutubeUrl(e.target.value)}
              />
              <div className="flex items-center justify-between">
                <Label htmlFor="quick-youtube-offline" className="text-sm">Download for offline playback</Label>
                <Switch
                  id="quick-youtube-offline"
                  checked={youtubeOffline}
                  onCheckedChange={setYoutubeOffline}
                />
              </div>
              <Button onClick={handleQuickYoutubeAdd} className="w-full" disabled={!youtubeUrl.trim()}>
                Add YouTube
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>

      {(!simpleMode || showAdvanced) && <HDMIStreamViewer />}
    </div>
  );
}
