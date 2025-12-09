import { useTranslation } from 'react-i18next';
import { useConfig } from '@/hooks/useConfig';
import { useToast } from '@/hooks/useToast';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Switch } from '@/components/ui/switch';
import { Save, RotateCcw, ChevronDown, ChevronUp, Plus, Trash2 } from 'lucide-react';
import { useState, useEffect } from 'react';
import { useTheme } from '@/components/theme-provider';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export default function ConfigPage() {
  const { t, i18n } = useTranslation();
  const { config, updateConfig } = useConfig();
  const { showSuccess, showError } = useToast();
  const { theme, setTheme } = useTheme();
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [newScheduleTime, setNewScheduleTime] = useState('10:00');
  const [formData, setFormData] = useState({
    gpio_enabled: false,
    auto_play: false,
    volume: 50,
    playback_duration_minutes: 30,
    youtube_quality: '720p',
    play_schedule: [] as string[],
    // Night mode
    night_mode_start: '22:00',
    night_mode_end: '06:00',
    night_mode_disable_playback: false,
    night_mode_volume: 30,
    // Motion sensor
    motion_sensor_enabled: false,
    motion_stop_enabled: false,
    motion_stop_timeout_seconds: 300,
  });

  useEffect(() => {
    if (config) {
      setFormData({
        gpio_enabled: config.gpio_enabled || false,
        auto_play: config.auto_play || false,
        volume: config.volume || 50,
        playback_duration_minutes: config.playback_duration_minutes || 30,
        youtube_quality: config.youtube_quality || '720p',
        play_schedule: config.play_schedule || [],
        night_mode_start: config.night_mode_start || '22:00',
        night_mode_end: config.night_mode_end || '06:00',
        night_mode_disable_playback: config.night_mode_disable_playback || false,
        night_mode_volume: config.night_mode_volume || 30,
        motion_sensor_enabled: config.motion_sensor_enabled || false,
        motion_stop_enabled: config.motion_stop_enabled || false,
        motion_stop_timeout_seconds: config.motion_stop_timeout_seconds || 300,
      });
    }
  }, [config]);

  const handleSave = async () => {
    try {
      console.log('Saving config:', formData);
      await updateConfig(formData);
      showSuccess(t('messages.saveSuccess'));
    } catch (error: any) {
      console.error('Config save error:', error);
      const errorMessage = error?.message || t('messages.error');
      showError(errorMessage);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-3xl font-bold tracking-tight">{t('config.title')}</h2>
        <p className="text-muted-foreground">{t('config.description')}</p>
      </div>

      <div className="grid gap-6">
        {/* General Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('config.general')}</CardTitle>
            <CardDescription>{t('config.generalDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t('config.autoPlay')}</Label>
                <p className="text-sm text-muted-foreground">
                  {t('config.autoPlayDescription')}
                </p>
              </div>
              <Switch
                checked={formData.auto_play}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, auto_play: checked })
                }
              />
            </div>

            <div className="space-y-2">
              <Label>{t('config.volume')}</Label>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={formData.volume}
                  onChange={(e) =>
                    setFormData({ ...formData, volume: Number(e.target.value) })
                  }
                  className="flex-1"
                />
                <span className="w-12 text-center">{formData.volume}%</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>{t('config.playbackDuration')}</Label>
              <p className="text-sm text-muted-foreground">
                {t('config.playbackDurationDescription')}
              </p>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="1"
                  max="120"
                  value={formData.playback_duration_minutes}
                  onChange={(e) =>
                    setFormData({ ...formData, playback_duration_minutes: Number(e.target.value) })
                  }
                  className="flex-1"
                />
                <span className="w-16 text-center">{formData.playback_duration_minutes} {t('common.min')}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Night Mode Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('config.nightMode')}</CardTitle>
            <CardDescription>{t('config.nightModeDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label>{t('config.nightModeStartTime')}</Label>
                <Input
                  type="time"
                  value={formData.night_mode_start}
                  onChange={(e) =>
                    setFormData({ ...formData, night_mode_start: e.target.value })
                  }
                />
              </div>

              <div className="space-y-2">
                <Label>{t('config.nightModeEndTime')}</Label>
                <Input
                  type="time"
                  value={formData.night_mode_end}
                  onChange={(e) =>
                    setFormData({ ...formData, night_mode_end: e.target.value })
                  }
                />
              </div>
            </div>

            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>{t('config.nightModeDisablePlayback')}</Label>
                <p className="text-sm text-muted-foreground">
                  {t('config.nightModeDisablePlaybackDescription')}
                </p>
              </div>
              <Switch
                checked={formData.night_mode_disable_playback}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, night_mode_disable_playback: checked })
                }
              />
            </div>

            {!formData.night_mode_disable_playback && (
              <div className="space-y-2">
                <Label>{t('config.nightModeVolume')}</Label>
                <p className="text-sm text-muted-foreground mb-2">
                  {t('config.nightModeVolumeDescription')}
                </p>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={formData.night_mode_volume}
                    onChange={(e) =>
                      setFormData({ ...formData, night_mode_volume: Number(e.target.value) })
                    }
                    className="flex-1"
                  />
                  <span className="w-12 text-center">{formData.night_mode_volume}%</span>
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        {/* YouTube Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('config.youtube')}</CardTitle>
            <CardDescription>{t('config.youtubeDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t('config.quality')}</Label>
              <select
                value={formData.youtube_quality}
                onChange={(e) =>
                  setFormData({ ...formData, youtube_quality: e.target.value })
                }
                className="w-full h-10 rounded-md border border-input bg-background px-3 py-2"
              >
                <option value="best">{t('config.qualityBest')}</option>
                <option value="1080p">1080p</option>
                <option value="720p">720p</option>
                <option value="480p">480p</option>
              </select>
            </div>
          </CardContent>
        </Card>

        {/* Schedule Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('config.scheduledPlayback')}</CardTitle>
            <CardDescription>{t('config.scheduledPlaybackDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t('config.scheduledTimes')}</Label>
              <p className="text-sm text-muted-foreground">
                {t('config.scheduledTimesDescription', { duration: formData.playback_duration_minutes })}
              </p>
              
              {/* List of scheduled times */}
              <div className="space-y-2">
                {formData.play_schedule.length === 0 ? (
                  <p className="text-sm text-muted-foreground italic">{t('config.noScheduledTimes')}</p>
                ) : (
                  formData.play_schedule.map((time, index) => (
                    <div key={index} className="flex items-center gap-2 p-2 border rounded-md">
                      <span className="flex-1 font-medium">{time}</span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                          const newSchedule = formData.play_schedule.filter((_, i) => i !== index);
                          setFormData({ ...formData, play_schedule: newSchedule });
                        }}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
                    </div>
                  ))
                )}
              </div>

              {/* Add new time */}
              <div className="flex items-center gap-2">
                <Input
                  type="time"
                  value={newScheduleTime}
                  onChange={(e) => setNewScheduleTime(e.target.value)}
                  className="flex-1"
                />
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => {
                    if (newScheduleTime && !formData.play_schedule.includes(newScheduleTime)) {
                      setFormData({
                        ...formData,
                        play_schedule: [...formData.play_schedule, newScheduleTime].sort()
                      });
                    }
                  }}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  {t('config.addTime')}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* UI & Appearance Settings */}
        <Card>
          <CardHeader>
            <CardTitle>{t('config.uiAppearance')}</CardTitle>
            <CardDescription>{t('config.uiAppearanceDescription')}</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label>{t('config.language')}</Label>
              <Select
                value={i18n.language}
                onValueChange={(value: string) => {
                  i18n.changeLanguage(value);
                  localStorage.setItem('pawvision-language', value);
                }}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t('config.selectLanguage')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="en">🇬🇧 English</SelectItem>
                  <SelectItem value="de">🇩🇪 Deutsch</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {t('config.languageDescription')}
              </p>
            </div>

            <div className="space-y-2">
              <Label>{t('config.theme')}</Label>
              <Select
                value={theme}
                onValueChange={(value: any) => setTheme(value)}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder={t('config.selectTheme')} />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="light">☀️ {t('config.themeLight')}</SelectItem>
                  <SelectItem value="dark">🌙 {t('config.themeDark')}</SelectItem>
                  <SelectItem value="system">💻 {t('config.themeSystem')}</SelectItem>
                </SelectContent>
              </Select>
              <p className="text-sm text-muted-foreground">
                {t('config.themeDescription')}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Advanced Settings - Collapsible */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>{t('config.advanced')}</CardTitle>
                <CardDescription>{t('config.advancedDescription')}</CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setShowAdvanced(!showAdvanced)}
              >
                {showAdvanced ? (
                  <>
                    <ChevronUp className="h-4 w-4 mr-2" />
                    {t('config.hide')}
                  </>
                ) : (
                  <>
                    <ChevronDown className="h-4 w-4 mr-2" />
                    {t('config.show')}
                  </>
                )}
              </Button>
            </div>
          </CardHeader>
          {showAdvanced && (
            <CardContent className="space-y-6">
              {/* GPIO Settings */}
              <div className="space-y-4">
                <h4 className="font-medium text-sm">{t('config.gpioButton')}</h4>
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{t('config.enableGpio')}</Label>
                    <p className="text-sm text-muted-foreground">
                      {t('config.enableGpioDescription')}
                    </p>
                  </div>
                  <Switch
                    checked={formData.gpio_enabled}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, gpio_enabled: checked })
                    }
                  />
                </div>

                <Button variant="outline" className="w-full">
                  {t('config.testGpio')}
                </Button>
              </div>

              {/* Motion Sensor Settings */}
              <div className="space-y-4 pt-4 border-t">
                <h4 className="font-medium text-sm">{t('config.motionSensor')}</h4>
                
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <Label>{t('config.enableMotionSensor')}</Label>
                    <p className="text-sm text-muted-foreground">
                      {t('config.enableMotionSensorDescription')}
                    </p>
                  </div>
                  <Switch
                    checked={formData.motion_sensor_enabled}
                    onCheckedChange={(checked) =>
                      setFormData({ ...formData, motion_sensor_enabled: checked })
                    }
                  />
                </div>

                {formData.motion_sensor_enabled && (
                  <>
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <Label>{t('config.autoStopOnNoMotion')}</Label>
                        <p className="text-sm text-muted-foreground">
                          {t('config.autoStopOnNoMotionDescription')}
                        </p>
                      </div>
                      <Switch
                        checked={formData.motion_stop_enabled}
                        onCheckedChange={(checked) =>
                          setFormData({ ...formData, motion_stop_enabled: checked })
                        }
                      />
                    </div>

                    {formData.motion_stop_enabled && (
                      <div className="space-y-2">
                        <Label>{t('config.motionTimeout')}</Label>
                        <p className="text-sm text-muted-foreground mb-2">
                          {t('config.motionTimeoutDescription')}
                        </p>
                        <div className="flex items-center gap-4">
                          <Input
                            type="number"
                            min="30"
                            max="3600"
                            step="30"
                            value={formData.motion_stop_timeout_seconds}
                            onChange={(e) =>
                              setFormData({
                                ...formData,
                                motion_stop_timeout_seconds: Number(e.target.value),
                              })
                            }
                          />
                          <span className="text-sm text-muted-foreground whitespace-nowrap">
                            ({Math.floor(formData.motion_stop_timeout_seconds / 60)} {t('common.min')})
                          </span>
                        </div>
                      </div>
                    )}
                  </>
                )}
              </div>
            </CardContent>
          )}
        </Card>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <Button onClick={handleSave} className="flex-1">
            <Save className="mr-2 h-4 w-4" />
            {t('config.save')}
          </Button>
          <Button variant="outline">
            <RotateCcw className="mr-2 h-4 w-4" />
            {t('config.reset')}
          </Button>
        </div>
      </div>
    </div>
  );
}
