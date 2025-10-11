# YouTube Troubleshooting Guide

## Bot Detection Error

If you see an error like:
```
ERROR: [youtube] Sign in to confirm you're not a bot
```

This means YouTube has detected automated access and requires verification. Here are solutions:

### Solution 1: Update yt-dlp (Easiest)

YouTube frequently changes their API. Updating yt-dlp usually fixes the issue:

```bash
# Update yt-dlp to the latest version
pip install -U yt-dlp
```

Then restart PawVision.

### Solution 2: Use YouTube Cookies (Most Reliable)

Export your YouTube cookies and PawVision will use them for authentication:

#### Using Browser Extension (Recommended)

1. **Install a Cookie Export Extension:**
   - Chrome: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid)
   - Firefox: [cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)

2. **Export YouTube Cookies:**
   - Go to [youtube.com](https://youtube.com) and make sure you're logged in
   - Click the extension icon
   - Click "Export" or "Download" 
   - Save as `youtube_cookies.txt`

3. **Move the file to PawVision:**
   ```bash
   # For development mode
   mv ~/Downloads/youtube_cookies.txt /path/to/PawVision/youtube_cache/
   
   # For production on Raspberry Pi
   mv youtube_cookies.txt /home/pi/youtube_cache/
   ```

4. **Restart PawVision** - it will automatically detect and use the cookies file

#### Manual Cookie Export (Advanced)

1. Open browser DevTools (F12)
2. Go to youtube.com
3. Open Application/Storage tab
4. Copy cookies manually to Netscape format
5. Save to `youtube_cache/youtube_cookies.txt`

### Solution 3: Wait and Retry

Sometimes YouTube's bot detection is temporary:

1. Wait 10-15 minutes
2. Try adding the video again
3. If still blocked, use Solution 1 or 2

### Solution 4: Use Different Video Sources

- Try different YouTube videos
- Use direct video file uploads instead
- Consider downloading videos offline first

## Prevention Tips

To avoid bot detection in the future:

1. **Keep yt-dlp updated** - Run `pip install -U yt-dlp` monthly
2. **Don't add many videos rapidly** - Space out video additions
3. **Use cookies proactively** - Export cookies before you hit rate limits
4. **Monitor logs** - Check `pawvision.log` for early warnings

## Cookie File Format

The cookies file should be in Netscape format:
```
# Netscape HTTP Cookie File
.youtube.com	TRUE	/	TRUE	1234567890	CONSENT	YES+...
.youtube.com	TRUE	/	FALSE	1234567890	VISITOR_INFO1_LIVE	...
```

## Security Note

**Important:** Cookie files contain sensitive authentication data. 

- Never share your cookies file
- Store it securely (chmod 600 on Linux/Mac)
- Regenerate cookies if compromised
- Delete cookies file if you're done using YouTube integration

## Still Having Issues?

If none of these solutions work:

1. Check if YouTube is accessible in your region
2. Verify your internet connection
3. Try the video URL in a regular browser
4. Check the PawVision logs: `tail -f pawvision.log`
5. Report the issue on [GitHub](https://github.com/mkroemer/PawVision/issues)

## Technical Details

PawVision uses these anti-bot measures automatically:

- Android player client emulation
- Realistic browser headers
- Cookie-based authentication (when provided)
- Format selection to avoid rate limits

These are built-in and require no configuration.
