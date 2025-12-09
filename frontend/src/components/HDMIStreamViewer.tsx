import { useEffect, useRef, useState } from 'react';
import { usePlaybackStatus } from '@/hooks/usePlaybackStatus';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Monitor, AlertCircle, Loader2 } from 'lucide-react';
import { useTranslation } from 'react-i18next';

interface StreamInfo {
  playing: boolean;
  video: {
    title: string;
    duration: number | null;
    playback_time: number | null;
    is_youtube: boolean;
  } | null;
  streamable: boolean;
  stream_type: 'local' | 'redirect' | null;
}

export function HDMIStreamViewer() {
  const { t } = useTranslation();
  const { status } = usePlaybackStatus();
  const videoRef = useRef<HTMLVideoElement>(null);
  const [streamInfo, setStreamInfo] = useState<StreamInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStreamInfo = async () => {
      if (!status.is_playing) {
        setStreamInfo(null);
        return;
      }

      try {
        setLoading(true);
        setError(null);
        
        const response = await fetch('/api/stream/info');
        const data = await response.json();
        
        if (!response.ok) {
          throw new Error(data.error || 'Failed to get stream info');
        }
        
        setStreamInfo(data);
      } catch (err) {
        console.error('Error fetching stream info:', err);
        setError(err instanceof Error ? err.message : 'Failed to load stream');
      } finally {
        setLoading(false);
      }
    };

    fetchStreamInfo();
    
    // Refresh stream info every 5 seconds while playing
    const interval = setInterval(fetchStreamInfo, 5000);
    return () => clearInterval(interval);
  }, [status.is_playing]);

  // Handle video source changes
  useEffect(() => {
    if (!streamInfo?.playing || !streamInfo?.streamable || !videoRef.current) {
      return;
    }

    const video = videoRef.current;
    
    // Set video source based on stream type
    if (streamInfo.stream_type === 'local') {
      video.src = '/api/stream/current';
      video.load();
    } else if (streamInfo.stream_type === 'redirect') {
      // For redirect (YouTube), fetch the redirect URL
      fetch('/api/stream/current')
        .then(res => res.json())
        .then(data => {
          if (data.redirect && data.stream_url) {
            video.src = data.stream_url;
            video.load();
          }
        })
        .catch(err => {
          console.error('Error loading redirect stream:', err);
          setError('Failed to load video stream');
        });
    }
  }, [streamInfo]);

  if (!status.is_playing) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            {t('control.hdmiStream', 'HDMI Stream')}
          </CardTitle>
          <CardDescription>
            {t('control.hdmiStreamDescription', 'View what\'s playing on the HDMI screen')}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48 bg-muted rounded-lg">
            <p className="text-muted-foreground">
              {t('control.noVideoPlaying', 'No video currently playing')}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            {t('control.hdmiStream', 'HDMI Stream')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center h-48 bg-muted rounded-lg">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (error || !streamInfo?.streamable) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Monitor className="h-5 w-5" />
            {t('control.hdmiStream', 'HDMI Stream')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center gap-2 p-4 bg-destructive/10 text-destructive rounded-lg">
            <AlertCircle className="h-4 w-4" />
            <p className="text-sm">
              {error || t('control.streamNotAvailable', 'Stream not available for this video')}
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Monitor className="h-5 w-5" />
          {t('control.hdmiStream', 'HDMI Stream')}
        </CardTitle>
        <CardDescription>
          {streamInfo.video?.title || t('control.currentlyPlaying', 'Currently playing')}
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="relative w-full aspect-video bg-black rounded-lg overflow-hidden">
          <video
            ref={videoRef}
            controls
            className="w-full h-full"
            playsInline
            onError={(e) => {
              console.error('Video playback error:', e);
              setError(t('control.playbackError', 'Video playback error'));
            }}
          >
            {t('control.videoNotSupported', 'Your browser does not support video playback')}
          </video>
        </div>
        {streamInfo.video && (
          <div className="mt-4 text-sm text-muted-foreground">
            {streamInfo.video.playback_time !== null && streamInfo.video.duration && (
              <p>
                {t('control.progress', 'Progress')}: {formatTime(streamInfo.video.playback_time)} / {formatTime(streamInfo.video.duration)}
              </p>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

function formatTime(seconds: number): string {
  const mins = Math.floor(seconds / 60);
  const secs = Math.floor(seconds % 60);
  return `${mins}:${secs.toString().padStart(2, '0')}`;
}
