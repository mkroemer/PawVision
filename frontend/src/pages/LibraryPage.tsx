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
import { Switch } from '@/components/ui/switch';
import { Play, Trash2, Upload, Clock, Pencil, Download } from 'lucide-react';
import { formatDuration, formatBytes } from '@/lib/utils';

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
  const { videos, refetch, hasMore, loadMore, loadingMore } = useVideos();
  const { showSuccess, showError } = useToast();
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [youtubeStartTime, setYoutubeStartTime] = useState('');
  const [youtubeEndTime, setYoutubeEndTime] = useState('');
  const [youtubeOffline, setYoutubeOffline] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadDialogOpen, setUploadDialogOpen] = useState(false);
  const [youtubeDialogOpen, setYoutubeDialogOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [videoToDelete, setVideoToDelete] = useState<string | null>(null);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [videoToEdit, setVideoToEdit] = useState<any | null>(null);
  const [editTitle, setEditTitle] = useState('');
  const [editStartTime, setEditStartTime] = useState('');
  const [editEndOffset, setEditEndOffset] = useState('');
  const [editOffline, setEditOffline] = useState(false);
  const [deleteOfflineDialogOpen, setDeleteOfflineDialogOpen] = useState(false);
  const [pendingOfflineChanges, setPendingOfflineChanges] = useState<any>(null);

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
    
    // Show initial downloading toast
    showSuccess(t('library.downloadStarted'));
    
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

      const result = youtubeOffline 
        ? await youtubeService.download(cleanUrl, startTime, endOffset)
        : await youtubeService.add(cleanUrl, startTime, endOffset);
        
      if (result.success) {
        showSuccess(youtubeOffline ? t('library.downloadComplete') : t('messages.downloadSuccess'));
        setYoutubeDialogOpen(false);
        setYoutubeUrl('');
        setYoutubeStartTime('');
        setYoutubeEndTime('');
        setYoutubeOffline(false);
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

  const handleDelete = async (videoPath: string) => {
    setVideoToDelete(videoPath);
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

  const handlePlay = async (videoPath: string) => {
    try {
      await videoService.play(videoPath);
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
    
    // Set offline status for YouTube videos
    setEditOffline(video.source === 'youtube' && !!video.download_path);
    
    setEditDialogOpen(true);
  };

  const confirmEdit = async () => {
    if (!videoToEdit) return;

    // Check if we're disabling offline mode - need confirmation
    if (videoToEdit.source === 'youtube') {
      const wasOffline = !!videoToEdit.download_path;
      const shouldBeOffline = editOffline;

      if (wasOffline && !shouldBeOffline) {
        // User is disabling offline - ask for confirmation
        setPendingOfflineChanges({
          videoToEdit,
          editTitle,
          editStartTime,
          editEndOffset,
          editOffline
        });
        setDeleteOfflineDialogOpen(true);
        return; // Don't proceed yet, wait for confirmation
      }
    }

    // Proceed with the update
    await performEdit();
  };

  const performEdit = async () => {
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

      // Handle offline download toggle for YouTube videos
      if (videoToEdit.source === 'youtube') {
        const wasOffline = !!videoToEdit.download_path;
        const shouldBeOffline = editOffline;

        if (!wasOffline && shouldBeOffline) {
          // Need to download - show toast
          showSuccess(t('library.downloadingForOffline'));
          
          // Start download in background
          youtubeService.add(videoToEdit.youtube_url || videoToEdit.path, 0, undefined, '720p', true)
            .then((result) => {
              if (result.success) {
                showSuccess(t('library.downloadComplete'));
                refetch();
              } else {
                showError(result.message || t('messages.downloadError'));
              }
            })
            .catch((error) => {
              showError(error.message || t('messages.downloadError'));
            });
        } else if (wasOffline && !shouldBeOffline) {
          // Delete the downloaded file
          if (videoToEdit.download_path) {
            try {
              await fetch('/api/video/delete-offline', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ path: videoToEdit.path })
              });
              showSuccess(t('library.offlineDeleted'));
            } catch (error) {
              showError('Failed to delete offline file');
            }
          }
        } else {
          showSuccess(t('messages.success'));
        }
      } else {
        showSuccess(t('messages.success'));
      }

      setEditDialogOpen(false);
      setVideoToEdit(null);
      setEditTitle('');
      setEditStartTime('');
      setEditEndOffset('');
      setEditOffline(false);
      refetch();
    } catch (error: any) {
      showError(error.message || 'Failed to update video');
    }
  };

  const confirmDeleteOffline = async () => {
    if (pendingOfflineChanges) {
      // Restore the pending changes and proceed with the edit
      setVideoToEdit(pendingOfflineChanges.videoToEdit);
      setEditTitle(pendingOfflineChanges.editTitle);
      setEditStartTime(pendingOfflineChanges.editStartTime);
      setEditEndOffset(pendingOfflineChanges.editEndOffset);
      setEditOffline(pendingOfflineChanges.editOffline);
      
      setDeleteOfflineDialogOpen(false);
      setPendingOfflineChanges(null);
      
      // Proceed with the edit
      await performEdit();
    }
  };

  const cancelDeleteOffline = () => {
    // User cancelled, restore the offline toggle
    setEditOffline(true);
    setDeleteOfflineDialogOpen(false);
    setPendingOfflineChanges(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">{t('library.title')}</h2>
          <p className="text-muted-foreground">{t('library.description')}</p>
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
                <DialogTitle>{t('library.uploadDialog')}</DialogTitle>
                <DialogDescription>
                  {t('library.uploadDescription')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <Label htmlFor="file-upload">{t('library.selectFile')}</Label>
                  <Input
                    id="file-upload"
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    disabled={uploading}
                  />
                  {selectedFile && (
                    <p className="text-sm text-muted-foreground">
                      {t('library.currentTitle')}: {selectedFile.name} ({(selectedFile.size / (1024 * 1024)).toFixed(1)} MB)
                    </p>
                  )}
                </div>
                {uploading && (
                  <div className="space-y-2">
                    <div className="flex justify-between text-sm">
                      <span>{t('library.uploading')}</span>
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
                  {uploading ? t('library.uploading') : t('library.upload')}
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
                  {t('youtube.description')}
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
                    {t('youtube.urlPlaceholder')}
                  </p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="youtube-start-time">{t('youtube.startTime')}</Label>
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
                      {t('youtube.startTimeDescription')}
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="youtube-end-time">{t('youtube.endOffset')}</Label>
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
                      {t('youtube.endOffsetDescription')}
                    </p>
                  </div>
                </div>

                {/* Offline availability toggle */}
                <div className="flex items-center justify-between p-4 border rounded-lg">
                  <div className="space-y-0.5">
                    <Label htmlFor="youtube-offline">{t('youtube.makeAvailableOffline')}</Label>
                    <p className="text-sm text-muted-foreground">
                      {t('youtube.makeAvailableOfflineDescription')}
                    </p>
                  </div>
                  <Switch
                    id="youtube-offline"
                    checked={youtubeOffline}
                    onCheckedChange={setYoutubeOffline}
                    disabled={uploading}
                  />
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
                <DialogTitle>{t('library.delete')}</DialogTitle>
                <DialogDescription>
                  {t('library.deleteConfirmDescription')}
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
                  {t('library.delete')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={deleteOfflineDialogOpen} onOpenChange={setDeleteOfflineDialogOpen}>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>{t('library.deleteOfflineTitle')}</DialogTitle>
                <DialogDescription>
                  {t('library.deleteOfflineDescription')}
                </DialogDescription>
              </DialogHeader>
              <DialogFooter>
                <Button variant="outline" onClick={cancelDeleteOffline}>
                  {t('common.cancel')}
                </Button>
                <Button variant="destructive" onClick={confirmDeleteOffline}>
                  {t('library.deleteOfflineConfirm')}
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>

          <Dialog open={editDialogOpen} onOpenChange={setEditDialogOpen}>
            <DialogContent className="sm:max-w-[500px]">
              <DialogHeader>
                <DialogTitle>{t('library.editVideo')}</DialogTitle>
                <DialogDescription>
                  {t('library.editDescription')}
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4 py-4">
                <div className="space-y-2">
                  <label htmlFor="edit-title" className="text-sm font-medium">
                    {t('library.videoTitle')}
                  </label>
                  <Input
                    id="edit-title"
                    placeholder={t('library.videoTitle')}
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label htmlFor="edit-start-time" className="text-sm font-medium">
                    {t('library.startTime')}
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
                    {t('library.startTimeDescription')}
                  </p>
                </div>
                <div className="space-y-2">
                  <label htmlFor="edit-end-offset" className="text-sm font-medium">
                    {t('library.endOffset')}
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
                    {t('library.endOffsetDescription')}
                  </p>
                </div>
                {videoToEdit && videoToEdit.duration && (
                  <div className="text-sm text-muted-foreground">
                    <Clock className="inline h-4 w-4 mr-1" />
                    {t('library.duration')}: {Math.floor(videoToEdit.duration / 60)}:{(videoToEdit.duration % 60).toFixed(0).padStart(2, '0')}
                  </div>
                )}
                {videoToEdit && videoToEdit.size > 0 && (
                  <div className="text-sm text-muted-foreground">
                    <Download className="inline h-4 w-4 mr-1" />
                    {t('library.fileSize')}: {formatBytes(videoToEdit.size)}
                  </div>
                )}
                {videoToEdit && videoToEdit.source === 'youtube' && (
                  <div className="flex items-center space-x-2 pt-2 border-t">
                    <Switch
                      id="edit-offline"
                      checked={editOffline}
                      onCheckedChange={setEditOffline}
                    />
                    <Label htmlFor="edit-offline" className="flex-1 cursor-pointer">
                      <div className="font-medium">{t('youtube.makeAvailableOffline')}</div>
                      <p className="text-xs text-muted-foreground">
                        {t('youtube.downloadDescription')}
                      </p>
                    </Label>
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
                  setEditOffline(false);
                }}>
                  {t('common.cancel')}
                </Button>
                <Button onClick={confirmEdit}>
                  {t('library.saveChanges')}
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
                    loading="lazy"
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
                    <>
                      <div className="text-xs text-muted-foreground truncate">
                        {video.youtube_url}
                      </div>
                      <div className="h-5 flex items-center">
                        {video.download_path && (
                          <div className="flex items-center gap-1 text-xs text-green-600 dark:text-green-400">
                            <Download className="h-3 w-3" />
                            <span>{t('library.availableOffline')}</span>
                          </div>
                        )}
                      </div>
                    </>
                  )}
                </div>
              </CardContent>
              <CardFooter className="flex gap-2 mt-auto">
                <Button
                  size="sm"
                  className="flex-1"
                  onClick={() => handlePlay(video.path)}
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
                  onClick={() => handleDelete(video.path)}
                >
                  <Trash2 className="h-4 w-4" />
                </Button>
              </CardFooter>
            </Card>
          ))}
        </div>
      )}
      {hasMore && (
        <div className="flex justify-center">
          <Button variant="outline" onClick={loadMore} disabled={loadingMore}>
            {loadingMore ? 'Loading…' : 'Load more'}
          </Button>
        </div>
      )}
    </div>
  );
}
