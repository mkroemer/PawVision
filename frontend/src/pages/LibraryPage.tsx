import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useVideos } from '@/hooks/useVideos';
import { useToast } from '@/hooks/useToast';
import { videoService } from '@/services/videoService';
import { youtubeService } from '@/services/youtubeService';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Label } from '@/components/ui/label';
import { Progress } from '@/components/ui/progress';
import { Play, Trash2, Upload, Clock, Pencil } from 'lucide-react';
import { formatDuration } from '@/lib/utils';

// Custom YouTube icon to replace deprecated lucide Youtube icon
const YoutubeIcon = ({ className }: { className?: string }) => (
  <svg
    xmlns="http://www.w3.org/2000/svg"
    viewBox="0 0 24 24"
    fill="currentColor"
    className={className}
  >
    <path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/>
  </svg>
);

// Placeholder for videos without thumbnails
const VideoPlaceholder = () => (
  <div className="w-full h-full flex items-center justify-center bg-muted">
    <svg
      className="w-16 h-16 text-muted-foreground/50"
      fill="none"
      stroke="currentColor"
      viewBox="0 0 24 24"
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={1.5}
        d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
      />
    </svg>
  </div>
);

export default function LibraryPage() {
  const { t } = useTranslation();
  const { videos, refetch } = useVideos();
  const { showSuccess, showError } = useToast();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [youtubeStartTime, setYoutubeStartTime] = useState('');
  const [youtubeEndTime, setYoutubeEndTime] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [youtubeDialogOpen, setYoutubeDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<number | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [videoToEdit, setVideoToEdit] = useState<any | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editStartTime, setEditStartTime] = useState('');
  const [editEndOffset, setEditEndOffset] = useState('');

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setUploadProgress(0);
    }
  };

  const extractYouTubeTimestamp = (url: string): number => {
    // Extract &t= parameter from YouTube URL
    const tMatch = url.match(/[?&]t=(\d+)/);
    if (tMatch) {
      return parseInt(tMatch[1], 10);
    }
    return 0;
  };

  const stripYouTubeTimestamp = (url: string): string => {
    // Remove &t= parameter from YouTube URL
    return url.replace(/[?&]t=\d+/, '').replace(/[?&]$/, '');
  };

  const handleFileUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setUploadProgress(0);
    try {
      await videoService.upload(selectedFile, (progress) => {
        setUploadProgress(Math.round(progress));
      });
      showSuccess(t('messages.uploadSuccess'));
      setUploadDialogOpen(false);
      setSelectedFile(null);
      setUploadProgress(0);
      await refetch();
    } catch (error: any) {
      const errorMessage = error?.response?.data?.error || error?.message || t('messages.uploadError');
      showError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

    const handleYoutubeDownload = async () => {
    if (!youtubeUrl) return;

    setUploading(true);
    try {
      // Strip timestamp parameter from URL before sending to backend
      const cleanUrl = stripYouTubeTimestamp(youtubeUrl);
      
      // Parse start and end times (in seconds)
      const startTime = youtubeStartTime ? parseFloat(youtubeStartTime) : 0;
      const endOffset = youtubeEndTime ? parseFloat(youtubeEndTime) : undefined;
      
      // Validate times
      if (startTime < 0) {
        showError('Start time cannot be negative');
        setUploading(false);
        return;
      }
      
      if (endOffset !== undefined && endOffset < 0) {
        showError('End trim cannot be negative');
        setUploading(false);
        return;
      }

      const result = await youtubeService.download(cleanUrl, startTime, endOffset);
      if (result.success) {
        showSuccess(result.message || t('messages.downloadSuccess'));
        setYoutubeDialogOpen(false);
        setYoutubeUrl('');
        setYoutubeStartTime('');
        setYoutubeEndTime('');
        await refetch();
      } else {
        showError(result.message || t('messages.downloadError'));
      }
    } catch (error: any) {
      console.error('YouTube download error:', error);
      const errorMessage = error?.message || t('messages.downloadError');
      showError(errorMessage);
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (videoId: number) => {
    setVideoToDelete(videoId);
    setDeleteDialogOpen(true);
  };

  const confirmDelete = async () => {
    if (videoToDelete === null) return;

    try {
      await videoService.delete(videoToDelete);
      showSuccess(t('messages.success'));
      await refetch();
    } catch (error) {
      showError(t('messages.error'));
    } finally {
      setDeleteDialogOpen(false);
      setVideoToDelete(null);
    }
  };

  const handlePlay = async (videoId: number) => {
    try {
      await videoService.play(videoId);
      showSuccess(t('control.playing'));
    } catch (error) {
      showError(t('messages.error'));
    }
  };

  const handleEdit = (video: any) => {
    setVideoToEdit(video);
    setEditTitle(video.title || '');
    
    // Convert absolute start time to offset (skip from start)
    setEditStartTime(video.custom_start_time ? video.custom_start_time.toString() : '');
    
    // Convert absolute end time to offset (trim from end)
    if (video.custom_end_time && video.duration) {
      const endOffset = video.duration - video.custom_end_time;
      setEditEndOffset(endOffset > 0 ? endOffset.toString() : '');
    } else {
      setEditEndOffset('');
    }
    
    setEditDialogOpen(true);
  };

  const confirmEdit = async () => {
    if (!videoToEdit) return;

    try {
      const formData = new FormData();
      formData.append('path', videoToEdit.path);
      if (editTitle) {
        formData.append('title', editTitle);
      }
      if (editStartTime && parseFloat(editStartTime) > 0) {
        formData.append('custom_start_time', editStartTime);
      }
      if (editEndOffset && parseFloat(editEndOffset) > 0) {
        formData.append('custom_end_offset', editEndOffset);
      }

      const response = await fetch('/api/video/update', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || 'Failed to update video');
      }

      showSuccess('Video updated successfully');
      setEditDialogOpen(false);
      setVideoToEdit(null);
      setEditTitle('');
      setEditStartTime('');
      setEditEndOffset('');
      refetch();
    } catch (error: any) {
      showError(error.message || 'Failed to update video');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t('library.title')}</h2>
          <p className="text-muted-foreground">Manage your video collection</p>
        </div>
        <div className="flex gap-2">
          <Dialog open={uploadDialogOpen} onOpenChange={setUploadDialogOpen}>
            <DialogTrigger asChild>
              <Button>
                <Upload className="mr-2 h-4 w-4" />
                {t('library.upload')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('library.upload')}</DialogTitle>
                <DialogDescription>
                  Upload a video file from your computer (max 5GB)
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="file-upload">Select Video File</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    disabled={uploading}
                  />
                  {selectedFile && (
                    <p className="text-sm text-muted-foreground">
                      Selected: {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)
                    </p>
                  )}
                </div>
                {uploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>Uploading...</span>
                      <span>{uploadProgress}%</span>
                    </div>
                    <Progress value={uploadProgress} />
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => {
                  setUploadDialogOpen(false);
                  setSelectedFile(null);
                  setUploadProgress(0);
                }} disabled={uploading}>
                  {t('common.cancel')}
                </Button>
                <Button onClick={handleFileUpload} disabled={!selectedFile || uploading}>
                  {uploading ? 'Uploading...' : t('library.upload')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={youtubeDialogOpen} onOpenChange={setYoutubeDialogOpen}>
            <DialogTrigger asChild>
              <Button variant="secondary">
                <YoutubeIcon className="mr-2 h-4 w-4" />
                {t('library.youtube')}
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('youtube.title')}</DialogTitle>
                <DialogDescription>
                  Download a video from YouTube
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="youtube-url">{t('youtube.url')}</Label>
                  <Input
                    id="youtube-url"
                    type="text"
                    placeholder={t('youtube.urlPlaceholder')}
                    value={youtubeUrl}
                    onChange={(e) => {
                      const url = e.target.value;
                      setYoutubeUrl(url);
                      // Auto-extract timestamp from URL if present
                      const timestamp = extractYouTubeTimestamp(url);
                      if (timestamp > 0 && !youtubeStartTime) {
                        setYoutubeStartTime(timestamp.toString());
                      }
                    }}
                    disabled={uploading}
                  />
                  <p className="text-xs text-muted-foreground">
                    Enter a YouTube video URL (e.g., https://www.youtube.com/watch?v=...)
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="youtube-start-time">Skip Start (seconds)</Label>
                    <Input
                      id="youtube-start-time"
                      type="number"
                      min="0"
                      step="1"
                      placeholder="0"
                      value={youtubeStartTime}
                      onChange={(e) => setYoutubeStartTime(e.target.value)}
                      disabled={uploading}
                    />
                    <p className="text-xs text-muted-foreground">
                      Optional: Skip this many seconds from the start
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="youtube-end-time">Trim End (seconds)</Label>
                    <Input
                      id="youtube-end-time"
                      type="number"
                      min="0"
                      step="1"
                      placeholder="0"
                      value={youtubeEndTime}
                      onChange={(e) => setYoutubeEndTime(e.target.value)}
                      disabled={uploading}
                    />
                    <p className="text-xs text-muted-foreground">
                      Optional: Remove this many seconds from the end
                    </p>
                  </div>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setYoutubeDialogOpen(false)}>
                  {t('common.cancel')}
                </Button>
                <Button onClick={handleYoutubeDownload} disabled={!youtubeUrl || uploading}>
                  {uploading ? t('youtube.downloading') : t('youtube.download')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Delete Video</DialogTitle>
                <DialogDescription>
                  Are you sure you want to delete this video? This action cannot be undone.
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={() => {
                  setDeleteDialogOpen(false);
                  setVideoToDelete(null);
                }}>
                  {t('common.cancel')}
                </Button>
                <Button variant="destructive" onClick={confirmDelete}>
                  Delete
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>Edit Video</DialogTitle>
                <DialogDescription>
                  Update video metadata and trim settings
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label htmlFor="edit-title" className="text-sm font-medium">
                    Title (optional)
                  </label>
                  <Input
                    id="edit-title"
                    placeholder="Video title"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="edit-start-time" className="text-sm font-medium">
                    Skip Start (seconds)
                  </label>
                  <Input
                    id="edit-start-time"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="0"
                    value={editStartTime}
                    onChange={(e) => setEditStartTime(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Number of seconds to skip from the start of the video
                  </p>
                </div>
                <div className="space-y-2">
                  <label htmlFor="edit-end-offset" className="text-sm font-medium">
                    Trim End (seconds)
                  </label>
                  <Input
                    id="edit-end-offset"
                    type="number"
                    min="0"
                    step="0.1"
                    placeholder="0"
                    value={editEndOffset}
                    onChange={(e) => setEditEndOffset(e.target.value)}
                  />
                  <p className="text-xs text-muted-foreground">
                    Number of seconds to trim from the end of the video
                  </p>
                </div>
                {videoToEdit && videoToEdit.duration && (
                  <div className="text-sm text-muted-foreground">
                    <Clock className="inline h-4 w-4 mr-1" />
                    Total duration: {Math.floor(videoToEdit.duration / 60)}:{(videoToEdit.duration % 60).toFixed(0).padStart(2, '0')}
                  </div>
                )}
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => {
                  setEditDialogOpen(false);
                  setVideoToEdit(null);
                  setEditTitle('');
                  setEditStartTime('');
                  setEditEndOffset('');
                }}>
                  {t('common.cancel')}
                </Button>
                <Button onClick={confirmEdit}>
                  Save Changes
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </div>

      {videos.length === 0 ? (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <p className="text-lg font-medium">{t('library.noVideos')}</p>
            <p className="text-sm text-muted-foreground">{t('library.addFirst')}</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {videos.map((video) => (
            <Card key={video.id} className="overflow-hidden flex flex-col">
              <div className="aspect-video w-full overflow-hidden bg-muted">
                {video.thumbnail ? (
                  <img
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-full h-full object-cover"
                    onError={(e) => {
                      // Show placeholder if image fails to load
                      const parent = e.currentTarget.parentElement;
                      e.currentTarget.style.display = 'none';
                      if (parent) {
                        const placeholder = document.createElement('div');
                        placeholder.className = 'w-full h-full flex items-center justify-center';
                        parent.appendChild(placeholder);
                      }
                    }}
                  />
                ) : (
                  <VideoPlaceholder />
                )}
              </div>
              <CardHeader>
                <CardTitle className="line-clamp-1">{video.title}</CardTitle>
                <CardDescription className="flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {formatDuration(video.duration)}
                </CardDescription>
              </CardHeader>
              <CardContent className="flex-1">
                <div className="space-y-2">
                  <div className="text-sm">
                    <span className="text-muted-foreground">{t('library.source')}: </span>
                    <span className="font-medium">{video.source}</span>
                  </div>
                  {video.youtube_url && (
                    <div className="text-xs text-muted-foreground truncate">
                      {video.youtube_url}
                    </div>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2 mt-auto">
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => handlePlay(video.id)}
                >
                  <Play className="mr-2 h-4 w-4" />
                  {t('library.play')}
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => handleEdit(video)}
                >
                  <Pencil className="h-4 w-4" />
                </Button>
                <Button
                  size="sm"
                  variant="destructive"
                  onClick={() => handleDelete(video.id)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
